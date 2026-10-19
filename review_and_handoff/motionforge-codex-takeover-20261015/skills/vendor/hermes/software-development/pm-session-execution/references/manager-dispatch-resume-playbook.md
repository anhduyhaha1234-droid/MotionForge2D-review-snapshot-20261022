# Manager Dispatch/Resume Playbook — Hermes CLI workers

Verified 2026-09-02 on the S10-C6H C15 closure (3 worker generations, 2 resumes, all EXIT 0). These are Hermes-CLI behaviors that repeat across every PM-gated worker dispatch; the failure modes below cost real time when rediscovered one at a time.

## 1. Dispatch shape (proven)
```bash
mkdir -p <task>/logs                      # log dir BEFORE redirect
cd <worktree> && export HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900
hermes --resume <session> --provider custom -m <exact-model-id> --yolo --no-restore-cwd \
  -z "$(cat <packet-file>.txt)" > <task>/logs/<stage>.log 2>&1; echo "EXIT:$?"
```
- Run `background=true` + `notify_on_complete=true`. `process(action='wait')` CLAMPS to 180s — loop it, or let the completion notification re-enter the turn.
- `-z "$(cat file)"` is safe: command-substitution output is literal (double quotes/newlines inside the packet do NOT break argv). Prompt packets >8K: split into two files.
- Best practice: pre-write the packet file (`prompt_c15b.txt` etc.), then resume — this keeps the audit trail of EXACTLY what the worker was told.

## 2. Resume creates a NEW effective session ID — record both
`hermes --resume <old>` does not continue `old` — it spawns a NEW state-db session row. The requested ID stays the lineage anchor; the returned/effective ID is the one to monitor and to resume next time.
```python
# read-only: file:.../state.db?mode=ro — NEVER mutate it
cur.execute("SELECT id, model, model_config, message_count, tool_call_count, end_reason \
             FROM sessions ORDER BY rowid DESC LIMIT 4")
```
Immediately after dispatch: record `requested_resume_id`, `effective_session_id`, timestamp, task identity, single-writer ownership in the registry. A fresh worker shows ~5–20 messages within the first minute — that is the "prove the child is active" evidence.

## 3. Liveness: an empty worker log is NORMAL
Hermes writes its final report into the redirected log ONLY at exit (log is 0 bytes for the whole run). Do not read emptiness as a dead process. Liveness = `ps aux | grep hermes` + state.db `message_count` growth between polls. When the process exits, `process(wait)` returns with `EXIT:0` and the log fills in one shot.

## 4. RUNTIME_CONFIG_GAP — CLI vs desktop config recording
CLI oneshot/resume rows record `model_config={"max_iterations": 90, "reasoning_config": null, "max_tokens": 16384}` even when local config requests max/300. Interactive desktop sessions record the real config (`reasoning_config: {enabled, effort: "max"}, max_iterations: 300`). Consequences:
- NEVER claim "reasoning max" from a CLI worker unless the state row proves it.
- Log the gap with exact state-row values, continue the same model route, add Manager-side verification (independent pytest runs with fresh roots).
- The `model` column DOES record the exact requested ID — use it for route proof (bare alias would show up here).

## 5. Model probe before dispatch
```bash
hermes -z "Reply with exactly: PROBE_OK" --provider custom -m <exact-model-id> --yolo --no-restore-cwd > probe.log 2>&1
```
Then verify BOTH: log tail == `PROBE_OK` AND the newest session row's `model` == the exact ID (not a truncated/aliased form). Keep the raw probe log in evidence.

## 6. Iteration ceiling (90) is NOT a terminal state
Workers hit the 90-tool-call ceiling mid-evidence with the code already done. Resume the LATEST effective session with a SHORT packet scoped to the remaining evidence steps ("do NOT re-run gates, do NOT touch code — only write LOG/REPORT/JSON"). The worker will usually do exactly that; if it refuses a re-run because the packet forbids it, that refusal is CORRECT behavior — the Manager runs the fresh gates.

## 7. Premature evidence claims in worker LOGs
A worker can append a LOG entry reading "STATUS: TASK_SUBMITTED (…). Evidence: <file>.json; LOG/REPORT appended" BEFORE actually writing those artifacts, then hit the ceiling. ALWAYS stat the claimed artifacts (`ls` c15b_done.json, grep REPORT for the section) instead of trusting the LOG tail. Fix pattern (append-only, never rewrite):
```
- SUPERSEDED: câu 'STATUS: …' trong entry trên là PREMATURE … status cuối đúng ở dòng correction này.
```
This keeps history intact and records the truth within the same file.

## 8. Manager verification (R-GATE / EXIT) — independent of worker self-reports
- Own fresh runs: `py_compile` → `ruff --select F` → `--collect-only` → focused `-k` packet → full module, each with DISTINCT short basetemps `%TEMP%/mfc15*` and `-p no:cacheprovider`.
- Diff guard: `diff <pre-correction byte snapshot> <current>` and enumerate hunks with `grep -E "^[0-9]"` — proves exactly which regions changed (authorized hunks only, no shrink).
- Spot-check the failure classification: read the raw traceback + the cited source lines; verify at least 2–3 of N before accepting "all harness, 0 production RED".
- Broad gates: run TWICE on distinct fresh roots; then re-freeze hashes (must be UNCHANGED between runs).
- Line counts: state the method (`wc -l` vs `grep -c ""`) — they can differ by 1 (trailing newline).
- Pre-worker: byte-snapshot every file the worker may touch (even "frozen" ones you plan to open later — `*.pre_c15b`), verify snapshot hash == source hash, keep a manifest.

## 9. ETA queries mid-run
User asks "bao giờ xong?": run `date` FIRST, lead with status + a small ETA table with anchors (started / now / expected / worst-case), then keep the monitoring loop alive in the same turn. Never end a turn with an un-dispatched promise — dispatch first, then report.

## 10. Terminal hardline parser — reshape, don't fight
Some harmless-looking commands get BLOCKED at parse time (exit -1, "unconditional blocklist"). Observed triggers: `grep -c ""` (empty pattern), `$(grep -n … | cut …)` nested inside quoted sed expressions, multi-tool pipelines with mixed quotes. Reshape: `wc -l` instead of `grep -c ""`; get line numbers with a plain `grep -n` first, then `read_file` the region. Never retry the identical blocked shape.