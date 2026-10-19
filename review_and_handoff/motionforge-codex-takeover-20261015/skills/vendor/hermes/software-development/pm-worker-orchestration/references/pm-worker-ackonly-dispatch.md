# PM Worker Dispatch — ack-only exits, self-verify fallback, env/basetemp traps

Observed across S12-C1/C2 correction rounds (2026-09-08/09, Hermes Manager driving
`hermes chat -q "<prompt>" -r <exact-owner-sid> -m <model> --provider <p> -Q`).

## 1. Ack-only worker exits are the NORM, not the exception

With one-shot `-Q` resume, many model sessions reply with an ack/plan and EXIT
without executing tools (`"TASK_SUBMITTED"`, `"Committing now"`, `"Báo ngay"`,
`"RULES_LO"` cut off) while the task worktree shows NO new commit and files still
dirty. Each `hermes chat -q -r` run = exactly ONE turn.

Rules that worked:
1. **Never trust the terminal message alone.** After every dispatch ping, verify
   ground truth in the task worktree: `git rev-parse --short HEAD`, `git status
   --porcelain=v1 -uall`, `git log --oneline -2`, evidence dir mtimes.
2. First ack-only → re-dispatch with an imperative "CHAY NGAY, bao output THAT
   tung lenh" packet that names the exact commands and required report.
3. Second ack-only (or 2h stall with no bytes) → **Manager self-verify fallback**:
   Manager runs the read-only gates itself inside the task worktree (pytest with
   explicit short basetemp, `ruff check --select F`, `git diff --check`), then
   dispatches a narrow "commit-only / docs-only" packet to the exact owner with
   the verified numbers. This unblocked T03C (19 passed) and T06A (full
   lifecycle) in ~15 min after hours of ack-only stalls.
4. Workers that need heavy real media (encode/kill-restart/Playwright) stall
   longer; a mid-flight "NUDGE" asking status+ETA is fine, but prefer one
   decisive RUN packet over repeated nudges.

## 2. `$TEMP`/`$TMP` env pollution breaks pytest basetemp

The shell env on this host can point `$TEMP` at ANOTHER lane's runtime dir
(e.g. `.../demo-v3-r2/_mgr-verify3-tmp`) → pytest setup dies with
`FileNotFoundError: [WinError 3] ... <basetemp>` even though the suite is fine.
**Always pass an explicit absolute basetemp under the real temp dir:**
`--basetemp=C:/Users/Admin/AppData/Local/Temp/<short>` — never `--basetemp=$TEMP/...`
in worker prompts or Manager verification. First failure diagnosis: echo $TEMP
before blaming code.

## 3. Model-route probes: broad match, record switch, never rewrite history

- Probing `http://127.0.0.1:20128/v1/models`: filter with BROAD substrings
  (`'spark'`, `'free'`) and print all matches. A combined-pattern grep can
  falsely conclude a model is missing when it exists (real miss in S12 on
  `ocgfree/muse-spark-1.3-contributor-free`).
- Probe the real chat route with a 5-token request using the full api_key from
  config before dispatching workers; distinguish 401 (bad key/trimmed key),
  429 (quota — e.g. CMC weekly limit), 502 connect-timeout (transient → wait
  ≥5 min, retry exact session+model).
- Every user worker-model override → append to an evidence
  `MODEL_SWITCH.md` (old models stay in history files untouched); workers keep
  the model named in the packet; a 429 is reported as BLOCKED_MODEL_ROUTE, not
  silently swapped.

## 4. Whole-tree pytest collection vs per-dir totals

Multiple task dirs adding the SAME test basename (`test_c1_closure.py` in
s12-t01/t02/t03a/t03b/t04a) with missing `__init__.py` in some packages →
`pytest tests/s12/` fails collection with `import file mismatch` while every
per-dir run passes. Per-dir totals are NOT whole-collection proof; review
packets must disclose the split and fix package naming (`__init__.py` per
package) so the full tree collects — never disable tests to make it collect.

## 5. Watchdog scripts: patch → kill → relaunch

A long-running `watch_24.sh` keeps the OLD code in RAM after you patch the
file. After any edit (model flag, lane), kill the exact bash PID (verify
cmdline + parent first) and relaunch; confirm new PID + first beat line.
Per S12-C2 rules: no self-waking watchdog may remain after submission — kill
and keep logs before the final packet.

## 6. Transient API failures that look fatal

- `API call failed after 3 retries: Codex Responses stream did not emit a
  terminal response` → not terminal; wait ≥5 min, resume same session/model.
- `HTTP 503: [opencode-go/deepseek-v4-flash] [502]: fetch connect timeout` →
  probe route; if 200, retry same session immediately; if still 502, wait 5
  min cycles per rules.
- Session-not-found on heartbeat/remind scripts = stale pinned SID (old
  manager pruned) → re-audit with `hermes sessions list`; never revive a
  pruned manager.

## 7. Git transport belongs to INT01 only

Manager committing/pushing canonical (even docs) crosses the integrator
boundary and gets flagged as a role violation in the next review packet.
Manager verifies commits; INT01 session does merge/push/prep of wave bases
(ff-only into clean owner branches) and reports `ls-remote == local`.
