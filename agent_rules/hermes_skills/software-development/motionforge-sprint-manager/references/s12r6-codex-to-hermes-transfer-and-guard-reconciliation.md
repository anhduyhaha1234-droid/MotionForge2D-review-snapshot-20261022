# S12-R6 Codex→Hermes owner transfer + guard reconciliation (2026-09-15)

Round: user handed `NEXT_HERMES_PROMPT.md` (S12 R6 completion, CHANGES_REQUESTED)
to a Hermes desktop chat; Manager + ALL workers on exact `ocg/deepseek-v4.1-flash`
@ custom (9Router `127.0.0.1:20128/v1`), fallback OFF. Five tasks transferred ONCE
from Codex owners: RETRY / VAL / QA / S09-LOCK-PRODUCER-B01 / INT.
Receiving Manager session: `20260915_194636_b5ea4c`.

## Route evidence (what "verified route" looked like)

- `curl /v1/models` → HTTP200, 145 models, exact ID present (full programmatic match).
- Adapter inspection: `_supports_reasoning_extra_body()` (run_agent.py ~6436)
  returns **False** for non-OpenRouter/non-Nous/non-LMStudio/non-Ollama base URLs
  → Hermes emits NO `reasoning`/`reasoning_effort` field on this route; the
  config's `max` never hits the wire. Native DeepSeek thinking runs gateway-side.
  Log this mapping instead of "sending max".
- Live probe: `hermes chat -q "Reply with exactly: PROBE_OK" -m ocg/deepseek-v4.1-flash
  --provider custom -Q --max-turns 2` → `PROBE_OK`, ~9.5 s, session `20260915_200617_c594a2`.
- Runtime verified from the worker side: `C:/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe`
  = Python 3.11.9 + pytest 9.1.1 + cv2 5.0.0 + fastapi 0.139.2 + sqlalchemy 2.0.51;
  ffmpeg at `.../WinGet/Packages/Gyan.FFmpeg_.../ffmpeg-8.1.2-full_build/bin`.

## Quiescence evidence (proof shape for "old owners inactive")

1. `find <wt> -newermt "6 hours ago"` → empty for all 5 worktrees (repeat with a
   40-min window during any snapshot copy).
2. No `*.lock` in worktree roots or `.git/worktrees/<name>/` admin dirs.
3. `Win32_Process` scan: NO process cmdline references any of the 5 worktrees;
   the only live codex.exe/python.exe processes were desktop-app infrastructure.
4. `hermes cron list` → no jobs (nothing to freeze); `hermes sessions list` →
   no prior S12 Hermes transfer (create-new transfer justified, not a duplicate).
5. Old owner states (reviewer-observed) recorded as HISTORICAL only — quiescence
   proven by 1–4, not by task headers.

## Dispatch commands actually used (all background + notify_on_complete)

```bash
# readiness (turn 1, NEW session):
cd <worktree> && EV=<lane evidence> && \
hermes chat -q "$(cat "$EV/prompt-readiness.txt")" -m "ocg/deepseek-v4.1-flash" \
  --provider custom -Q --yolo --accept-hooks --pass-session-id --max-turns 30 \
  > "$EV/readiness-console.txt" 2>&1; echo "EXIT=$?" >> "$EV/readiness-console.txt"

# work (turn 2, resume same session):
hermes chat -q "$(cat "$EV/prompt-work.txt")" -r <session_id> -m "ocg/deepseek-v4.1-flash" \
  --provider custom -Q --yolo --accept-hooks --pass-session-id --max-turns 400 \
  > "$EV/work-turn2-console.txt" 2>&1; echo "EXIT=$?" >> "$EV/work-turn2-console.txt"
```

- Session id parsed from the console tail (`session_id: 20260915_XXXXXXXX_XXXXXX`);
  `--pass-session-id` also makes the worker self-report it in its first reply.
- Readiness prompts must state ZERO WRITES explicitly (no pytest, no commit, no
  fetch/pull/push) and demand RAW output of each command. Workers auto-load the
  terminal-engineering-discipline skill mandate first (extra turn, ~10-40 KB console).
- Console files: keep turn1 logs after a death; name successive turns
  `work-turn2-console.txt`, `work-turn3-console.txt` … (incident trail).
- B01 worktree has `dubious ownership` (`.git` owned by `CodexSandboxOffline`
  user): use `git -c safe.directory='*' …` per-invocation; never persist config.

## Batch 502 incident (three workers, one upstream)

- Timeline (UTC): RETRY turn1 died 13:53:47Z; VAL + B01 turn1 died ~13:55:52-53Z.
  All: `API call failed after 3 retries: HTTP 503: [opencode-go/deepseek-v4.1-flash]
  [502]: fetch connect timeout (reset after Ns)`, EXIT=1. QA (4th worker) SURVIVED
  and kept writing — same upstream, so survival is per-connection luck, not policy.
- Post-death: all three worktrees CLEAN (deaths happened in design/read phase —
  no partial writes). RETRY's runtime dir already held its sync artifacts
  (`01_pre_head..05_post_status`, `cmdlog.py`, `COMMAND_LEDGER.jsonl`).
- Liveness probe before resume: `PROBE2_OK` @ 13:00:10Z, **57 s latency** (vs 9.5 s
  baseline) → recovered but degraded; expect more drops, keep the cycle armed.
- Resumes: identical continuation text to all three, same route/flags:
  "Tiếp tục làm việc đi. Lượt trước bị ngắt bởi lỗi kết nối gateway tạm thời
  (HTTP 503/502 fetch connect timeout) — KHÔNG phải lỗi của bạn; route/model/scope/
  allowlist không đổi. Trước khi tiếp tục: kiểm tra nhanh state hiện tại (git status;
  các file bạn đã tạo trong evidence/runtime dir), rồi tiếp tục đúng work order từ
  điểm dừng (<step n>). Không làm lại phần đã xong. Không hỏi lại."
- All three resumed cleanly (0 API-fail after). Stale exit-notices for the dead
  turn1s kept arriving 20–60 min later — verify state, do not re-act.
- Incident recorded: `manager/INCIDENT_20260915T1353Z_gateway_502.md` + registry
  bumped `RUNNING_RETRY_WAIT → RESUMED`.

## Post-merge guard reconciliation (the numbers)

- Pre-sync manifests were captured at each lane's own baseline (RETRY c60235f,
  VAL 4f83662, QA b6ab84e; B01/INT already at 83af516), then lanes ff-merged to
  the shared candidate `83af516` — the sanctioned sync REWRITES protected files.
- QA protected verify: "FAILED 10/18" → compare-vs-INT proved 10/10 identical to
  candidate (8 byte-identical, 2 both-MISSING = T03C tests relocated to retry by
  design). `all_merge_explained: true`. Re-baseline captured
  (`guard-*-postmerge.json`).
- RETRY protected verify: 12/13 byte-identical; `app/persistence/models.py`
  differed 64 bytes → not a violation:
  - `git rev-parse HEAD:app/persistence/models.py` → `dc71157f16b8…` IDENTICAL both sides
  - CR count 3528 (RETRY) vs 3592 (INT) = 64 delta
  - `tr -d '\r' < file | sha256sum` → `ecd68a371745…` IDENTICAL
  - both trees porcelain-clean ⇒ EOL checkout artifact. Closed in
    `manager-verify-merge-explained.json` (`EOL_ONLY_ARTIFACT_NOT_A_VIOLATION`).
- Allow-set verify stays valid across the merge: pass `--allow-change` for every
  lane write-set path (shrink check only); protected manifest is re-baselined.

## Manager submission verification (per lane, exact command set)

```bash
git show --stat --format='%H%n%P%n%s' <sha>   # file list ⊆ allowlist, parent == wave base
git status --porcelain                         # must be empty
git diff --check <base> <sha>                  # exit 0
<python> -m ruff check --select F <changed py> # clean
<python> -B -m pytest <affected suite> -q -p no:cacheprovider --basetemp <short %TEMP% path>
```

- RETRY (commit `1d9ed94`, parent 83af516): 5 files / 1498+ — Manager re-run
  **85 passed in 208 s** == worker claim (46/46 M01–M19 + 39 affected). ruff clean,
  diff-check 0, guard-allow VERIFIED (12), protected all explained.
- QA (commit `69a1280`): 6 files / 628+ — Manager re-run **11 passed in 2.94 s**
  == claim; guard-allow VERIFIED (50).

## Misc traps hit this round

- VAL `work/` snapshot: `shutil.copytree` default (`symlinks=False`) MATERIALIZES
  `*current` symlinks → 58 src vs 116 dst false mismatch. Re-copy with
  `symlinks=True`; verify file-list + symlink-list + hashes (`status: VERIFIED`).
- Nested `$(grep -c "…" "$f")` substitutions inside mixed-quote loops tripped the
  terminal command parser once ("BLOCKED (hardline): command parser limit or
  malformed executable payload"). Split into simple non-nested commands.
- `git -C /c/abs` false "cannot change to …" errors (intermittent) — `cd` + relative.
- PowerShell helpers (heartbeat collector, worker lister): write `.ps1` via
  write_file and call with `-ExecutionPolicy Bypass -File` — avoids inline quoting hell.
- Heartbeat while gateway-off desktop: chained `sleep 1140; <collector.ps1>; echo DONE`
  background jobs with notify_on_complete ≈ 19-min visible heartbeat + wake-up;
  collector appends per-lane console sizes/mtimes/tails + live proc count to
  `manager/HEARTBEAT.md`.
