# S10 T01C handler registration miss + T04C acceptance routing (verified 28/08)

**Context:** S10 8-owner DAG `PREP→(T01A‖T01B)→J1→T01C→J2→T02→J3→T03→J4→T04A→J5→T04B→J6→T04C→EXIT`. T01C owned `app/workflow/s10_full_apply_jobs.py` with `register_s10_full_apply_handler()` but never registered it in `app/workflow/job_service.py` (only scene/proxy/discover/recompute/attach_audio were registered). T04C acceptance harness (last task, forbidden to touch production code) reported `BLOCKED_WITH_FINDINGS` with exact file:line pointer — valid P0.

**Lessons:**

1. **Allowed scope must include workflow wiring.** T01C prompt allowed `app/api/app.py (+bounded deps.py)` but not `app/workflow/job_service.py`. The precedent pattern for every durable-job sprint is: handler lives in `app/workflow/<feature>_jobs.py`, registration lives in `app/workflow/job_service.py` (`register_*_handler(self._worker)`). Future T01C-style prompts should explicitly allow `app/workflow/job_service.py` (bounded +2 import +1 register) as part of the write-set, or the acceptance lane will always re-discover the same blocker one sprint-exit gate before close.

2. **Owner-routing loop works as designed.** Manager confirmed via `grep -n s10_full_apply app/workflow/job_service.py` (0 hits), dispatched correction to exact owner `20260828_003035_859fe5` with a 22-line packet prescribing the single fix (`from app.workflow.s10_full_apply_jobs import register_s10_full_apply_handler` + `register_s10_full_apply_handler(self._worker)` after `register_attach_original_audio_handler`), re-verified with `pytest 11 passed ×2` (54s each, isolated basetemp), then resumed T04C same session `20260828_023122_76b87e`. No new session, no scope creep.

3. **P2 docs ≠ gate block.** T04B worker passed TSC + ESLint scoped + `next build BUILD_EXIT=0` + `playwright --list 6 tests` but wrote no `TASK.md/LOG.md/REPORT.md` (only `output/s10/t04b/*.log`). Manager carried it as P2 at J6 (`J6=MANAGER_VERIFIED with P2 docs only`) — evidence logs are the real proof; doc scaffold can be backfilled without reopening the lane.

4. **Heartbeat/ETA wall table stays 30'+instant.** From S10 W1 through W6 the wall ETA table (J1–J6 + T04C ×2 + sprint-exit) was re-anchored with `date` on every `go+ETA` co-occurrence (`up date tiến độ đi bao giờ xong`), and `sao thấy dừng rồi?` never meant Manager was idle — T04C `RUNNING_RETRY_WAIT`-style handler miss is still `BLOCKED_WITH_FINDINGS` awaiting a single owner resume, not a liveness stall.
