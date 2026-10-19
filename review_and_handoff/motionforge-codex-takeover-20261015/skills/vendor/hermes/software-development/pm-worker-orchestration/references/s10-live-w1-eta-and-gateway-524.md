# S10 Live W1 — T01B Green + Gateway 524 RUNNING_RETRY_WAIT (verified 2026-08-27 23:40–23:59)

Context: Manager `20260827_220742_de1883` dispatched W1 `T01A‖T01B` `meta/max/TTFB900/fallback OFF` at 23:40 from `codex/s08-integration` HEAD `d3f6f79`. User sent two out-of-band messages in the same underlying turn: estimate request + `sao lại dừng r` heartbeat probe. Both handled in same reply (dispatch confirm + date-anchored ETA wall table).

## T01B — first TASK_SUBMITTED of S10 (reference green)

- Worker session `20260827_234004_25fb5c` → `STATUS: TASK_SUBMITTED` at ~23:55, `STOP` awaiting J1.
- Artifacts: `app/services/s10_chunk_plan.py` (481 lines, pure — no DB/IO/time/process/path, hash from pinned canonical JSON sort_keys, deterministic `chunk_id=ck_<sha16>`), `tests/test_s10_chunk_plan.py` (26 tests, 6-bullet full coverage).
- Isolated gates as logged by worker + re-verified by Manager:
  - Ruff scoped `--isolated` → All checks passed; `mypy --strict` → Success no issues.
  - `pytest` run1 `/tmp/tmp.vv8GKn2yKu` 26 passed (1.63s), run2 `/tmp/tmp.mXfvfV6sho` 26 passed — Manager re-ran one more isolated `pytest -p no:cacheprovider --override-ini="addopts=" --basetemp=...` → 26 passed in 1.63s (repro exact).
  - Ruff footgun noted: `ruff check` with `pyproject.toml` (line-length 100) reports E501/SIM108 on this planner (e.g. allowed-keys tuple line 56), but worker's `--isolated` mode is the correct scoped contract. Manager recorded the delta in registry; fix belongs to T01B owner only at J1, not broad reformatting now.
- 6-bullet determinism proof (tests): byte-identical twice + shuffled same; every frame exactly once core / overlap context only; no gap/drift including 1-frame shot + final partial; routes/deps pinned sorted; pinned change → plan_id changes while ambient path/time/pid does not; 9 fail-closed cases.
- Join gate: held — `J1` blocked on `T01A` (T01B alone does not open T01C). Downstream T01C will consume this planner deterministically.

## Gateway 524 — RUNNING_RETRY_WAIT (Rules §7, infinite loop)

- T01A Worker `20260827_234001_9d7f39` (`proc_5dfa6c560716` pid 21500) exited with `statusCode 524 Gateway request failed isRetryable=true` at 23:46 (pre-prefill, ~6m after launch — before any `RULES_LOADED` bytes landed).
- Classification per `HERMES_AUTOPILOT_RULES.md` §7: connection/524/502/503/504/disconnect/socket reset/DNS/timeout are **retryable connection errors**, not terminal. Policy: mark `RUNNING_RETRY_WAIT`, report immediately, wait **5 minutes** (bounded checks, not `sleep 570`), then `resume same session / same model / same prompt file / same exclusive write-set / same TTFB` — no fallback, no new session, retry **unbounded** until success / user stop / proven dead session.
- Recovery that fired: at 23:58 (12m > 5m, conservatively beyond the window) Manager ran `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume 20260827_234001_9d7f39 -z "$(cat output/s10/t01a/prompt.txt)" -m meta --yolo` as `proc_fde510fe01a5` pid 28140. Session context survives the kill — edits carry across resume.
- Live monitor: `process poll proc_fde510fe01a5` at 23:59 still `RUNNING` (prefill silence ~15–22m normal for 150k-token `meta/max`); T01B `TASK_SUBMITTED` held at `SUBMITTED_PENDING_MANAGER` until J1.

## Heartbeat embedding learned this session

- User cadence is now `30' + instant on lane exit/blocker` (S09-C4-META carry-forward), not 5'. Two `sao thấy dừng r` probes arrived while both lanes were legitimately `RUNNING` — Manager answered lead-with-status + slot table + "đang chờ gì" (here: T01A resume, T01B awaiting J1) so silence is read as "workers running" not "Manager stopped".
- Every `chạy đi` / `estimate` out-of-band that co-occurs with an active DAG must produce `date`-anchored wall ETA + dispatch confirm in the same reply; deferring to next heartbeat triggers repeat probes.
