# Gate calibration, continuation prompts, cron model, ETA reporting
(Captured from S10-C6B evening session, 2026-08-31 → 09-01. Class-level patterns, session specifics condensed.)

## 1. Gate-script calibration — avoid Manager false FAILs
- **Bare `ruff check` applies the FULL default ruleset** (E501/I001/N814…). On lifecycle files that is 300+ pre-existing style errors → gate exits 1 = FALSE FAIL. The canonical sprint gate is `python -m ruff check --select F <files>` (matches historical `ruff_F.log`). Before declaring any gate failure, re-run the canonical command manually and compare against prior evidence logs — the script may be miscalibrated, not the code.
- **Broad-except sweep false positive:** a nested rollback-guard (`try: session.rollback() except Exception: pass` INSIDE an outer `except Exception` that compensates + raises HTTPException 500) is legitimate fail-closed design. Regex sweeps flag it. Manual code-read of flagged lines is mandatory before classifying; record the verdict (LEGITIMATE vs defect) in the verdict file.
- Always emit a `*_VERDICT.md` with the gate table + calibration notes so downstream Codex rereview sees WHY a raw exit-1 was overridden by manual verification.

## 2. Manager-owned decisive evidence vs worker-verified static gates
- Worker-run static gates (tsc, eslint changed-files, J1-v4, diff-check) may be verified by READING the worker's evidence logs instead of re-running (~30' → ~3') — "paper gate" only when the logs contain real command output.
- Decisive behavioral gates MUST be run by the Manager independently, e.g. the race/lifecycle probe `pytest -k "cancel or resume or retry"` on a fresh short-basetemp root. Manager-executed behavioral evidence is what makes an intermediate gate (J6C) independent of worker claims.

## 3. Build-skip hash-equality — check invalidation BEFORE trusting it
- The build-skip shortcut (keep current BUILD_ID because N production frontend inputs hash-equal a snapshot) is invalidated the moment any worker edits production frontend bytes (e.g. `src/lib/api.ts`, `src/app/(app)/apply/page.tsx`).
- BEFORE using the shortcut: `git status --porcelain | grep frontend` + recompute hashes FROM the snapshot file. Any DIFF → cancel the shortcut, rebuild (`node output/s10/run-s10.js --build-only` → `--verify-build-only` 7/7) and pin downstream vertical runs to the NEW BUILD_ID. A stale BUILD_ID poisons all downstream vertical-run evidence.
- **Snapshot parsing discipline:** READ the snapshot file and parse its actual format first; never guess delimiters or hardcode hashes into an ad-hoc dict (CRLF + space-separated variants burned 4 tool calls on format guessing).

## 4. Continuation prompts for cleanly-exited workers (exit 0, work remaining)
- When a worker exits 0 with an honest "remaining work" list in its final response, resume the SAME owner session with a SHORT turn-N prompt that: (a) states Manager-verified state (grep/mtimes — not worker claims), (b) endorses or corrects the worker's own proposed plan, (c) enumerates remaining steps in order + guards (branch/HEAD/no-git-ops/DB-env/allowlist/model).
- This landed two multi-step completions in single turns (T01C F2/F3; T04B 20/20 full pass). Keep ≤ ~2KB — workers re-read their own LOG.md for design context; don't re-paste it.

## 5. ETA reporting under slip pressure (user friction signal)
- User signal: "sao càng ngày càng xa deadline thế" — repeated slipping re-estimates erode trust more than one honest variance table.
- On slip, report: planned-vs-actual per node with cause attribution (worker death → re-run turn; first-live-run defect discovery; model reasoning latency), which causes are manager-owned vs user-chosen (e.g. comboBAI reasoning-max), and the concrete gates CUT to recover time.
- Give optimistic + pessimistic ETA with the switch condition ("+1 turn if another first-live defect"). Do NOT set the initial ETA at 1-turn-per-node without buffer: context-compression kills and first-live-run defects are recurring — budget ~1 extra turn per 2 nodes.

## 6. Per-job cron model override (heartbeat must not run on the wrong model)
- Cron jobs inherit `model.default` from config.yaml (e.g. meta/muse) unless the job carries its own model — the cronjob TOOL schema has no model field.
- Fix via CLI: `hermes cron edit <job_id> --model comboBAI --provider custom` (exact case matters); verify with `hermes cron list`.
- Heartbeat jobs can disappear between turns ("Job not found" on edit) — always `cronjob(action='list')` first and recreate rather than editing a stale ID.
