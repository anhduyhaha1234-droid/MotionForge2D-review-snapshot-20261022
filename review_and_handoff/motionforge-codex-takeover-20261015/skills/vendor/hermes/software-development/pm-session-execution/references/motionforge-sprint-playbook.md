# MotionForge PM Sprint Orchestration — session playbook (S09 run, 2026-08-23/24)

Condensed, battle-tested patterns for running a full PM-gated sprint as HERMES MANAGER:
dispatching worker sessions via hermes CLI, resuming dead workers, independent verification.
The canonical rules live in `docs/pm/HERMES_AUTOPILOT_RULES.md` (MAIN tree) — this file is the
how-to supplement, not a replacement.

## Worker lifecycle observed in S09 (11 tasks, all completed)

Typical failure mode: worker process dies silently mid-task. Seen 6+ times in one sprint.
Symptoms: log size frozen across 2+ samples, `tasklist python.exe` = 0 processes, background
process list empty, NO wrapper EXIT line appended to dispatch.log (wrapper was killed with child).

### Recovery protocol that worked every time

1. **Verify disk state yourself** — never trust the worker's last narration:
   - `ls` the expected output files; `git diff --numstat <allowlist>` to see what landed
   - Run the task's own test suites by hand (`env -u MOTIONFORGE_DATABASE_URL pytest ... -p no:cacheprovider --basetemp=<fresh tmp>`)
   - Grep the dispatch.log tail for the exact point of death (last diff hunk / last reasoning line)
2. **Write a resume packet** (`resume-r1.txt`) next to dispatch.log containing:
   - "TRẠNG THÁI ĐÃ CÓ (Manager verify bằng disk)" — bullet list of what exists and is verified
   - The exact place it stopped ("đang patch print-order trong proof script")
   - Findings you already root-caused FOR it (e.g. "Finding 1: ORM class thiếu CHECK X mà migration có — thêm CheckConstraint theo pattern của bảng sibling")
   - Numbered remaining steps + gates + REPORT.md requirement + STATUS: TASK_SUBMITTED then STOP
   - Write-set reminder (unchanged allowlist) + forbidden list
3. **Resume the EXACT owner session**: `hermes chat --provider custom --model alpha --resume <session-id> -q "$(cat resume-r1.txt)" --yolo -Q >> dispatch.log 2>&1`
4. Finding owner session id when the log doesn't show it: query
   `C:/Users/Admin/AppData/Local/hermes/state.db`, table `sessions`, match on first user message content.

### Independent manager verification gates (per task)

- Test suites ×2 consecutive runs with DIFFERENT basetemp each (`--basetemp=%TEMP%/mgr-<task>-v1` / `-v2`)
- Static: ruff check (Python only — NEVER point ruff at .ts files), mypy spot-check on new modules
- Alembic: `ScriptDirectory.from_config(Config('alembic.ini')).get_heads()` → assert single head;
  round-trip test = upgrade head → downgrade to PARENT revision → upgrade again
  (full downgrade-to-base may be blocked by earlier sprint contracts, e.g. S06 irreversible migration — that is by design, not a bug)
- Additive-only proofs: `difflib.unified_diff` old-vs-new counting `-` lines (models.py zero-removed);
  `git diff app/api/app.py | grep -c "^-[^-]"` must be 0
- OpenAPI path count before/after (removed=0); UI helper-text compliance grep (`grep -c text-gray-400`)
- Cross-check worker claims against disk; workers DO catch wrong management assumptions
  (S09 example: TASK.md said reference media missing → worker found it present, sha matched)

### Dispatch pattern

```
terminal(background=true, notify_on_complete=true):
cd /c/Users/Admin && HERMES=".../hermes.exe" && \
"$HERMES" chat --provider custom --model alpha --resume <sid>| -q "$(cat prompt.txt)" --yolo -Q \
  > <lane>/dispatch.log 2>&1; echo "EXIT=$?" >> <lane>/dispatch.log
```

- Always append wrapper EXIT marker AFTER hermes exits — absence of it = hard kill signal.
- Liveness check = `stat -c%s dispatch.log` sampled twice ≥40s apart; delta>0 means alive.
- Never trust MSYS ps/tasklist PID mapping on this machine.
