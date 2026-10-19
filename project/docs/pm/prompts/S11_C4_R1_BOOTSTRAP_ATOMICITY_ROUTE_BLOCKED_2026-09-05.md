# HERMES PROMPT — S11-C4-R1 Bootstrap Atomicity and Route-Gated Closure

Đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
trước mọi preflight hoặc dispatch. Bạn là Hermes Manager; Codex là reviewer/gate
độc lập. **Manager does not code**: Manager không sửa production, test,
migration, UI, config hoặc implementation bytes.

## 1. RULES_LOADED and current verdict

Bắt buộc đọc đầy đủ rules, `AGENTS.md`, `frontend/AGENTS.md`,
`SESSION_PROTOCOL.md`, `CODEX_PM_HANDOFF.md`, `ROADMAP.md`, C3 review, C4
binding prompt, C4 `REGISTRY.md`, C4 EXIT/NEXT_REVIEW_PACKET, T03G
LOG/REPORT trong canonical worktree, current source/tests và state evidence.
Báo `RULES_LOADED` kèm SHA-256, line count, HEAD và evidence root.

Current exact status:

- `S11-C4 = CHANGES_REQUESTED / NOT_APPROVED`.
- `S11 = NOT_CLOSED`; S12/S13 không được mở.
- Reviewed canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Branch: `codex/s11-integration`; reviewed HEAD:
  `8f5af068978265a0dc347db97099f897e1eb5a49`; preflight phải khám phá lại,
  không coi HEAD này là sự thật mới nếu filesystem/Git khác.
- C4 evidence root cũ chỉ là read-only evidence:
  `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-034450`.
  Chưa được claim lại nó là run-root mới.

## 2. Route blocker — terminal preflight, no alias fallback

Required route for this Manager and every new worker turn:

- provider/API mode: `custom` through 9Router;
- base URL: `http://127.0.0.1:20128/v1`;
- exact model ID: `cmc/muse-spark-1.3-contributor`;
- reasoning: `max`; fallback: **OFF**; TTFB timeout: 900 seconds.

Immediately after `RULES_LOADED`, query `/v1/models` and perform one zero-write
probe that records a durable exact provider/base-url/model usage row. The exact
ID must be present and the probe must succeed. If the ID is absent, or the probe
returns 400/401/403/404/429/5xx/model-provider error, stop immediately with:

`BLOCKED_MODEL_ROUTE`

Save raw command, response, exit, timestamp and the durable row in a new review
evidence root. Do not use `cmc/meta/muse-spark-1.3-contributor`, `meta`,
`comboBAI`, `auto`, DeepSeek, inherited sessions or any alias. Do not retry a
deterministic route/auth/model error indefinitely. A temporary 502/503/504 or
disconnect waits 5 minutes, audits liveness, and retries the same exact route.
Until the exact route gate is green, **no worker, correction, integration or
test wave is authorized**.

## 3. Scope and out-of-scope

If the exact route remains blocked, the terminal condition is the blocker above.
If Codex later reopens this prompt after a valid exact route, the only authorized
correction scope is S11-C4-R1:

- `app/workflow/qc_checks_handler.py`
- `app/workflow/job_service.py` only if the production hook needs correction
- `app/persistence/qc_check_runs.py` only for C4-R1-B authority gaps
- `tests/test_s11_t03g_qc_check_job.py`
- `tests/test_s11_t03g_qc_check_api.py`
- one narrowly named clean-process T03G subprocess test if required
- `docs/pm/sessions/S11-T03G/**`
- new C4-R1 evidence only

Forbidden: frontend, migrations, schemas, detector algorithms, T03F/T04/T05/T06
implementation, unrelated lint/refactor, MAIN product bytes, C1/C2/C3/C4 old
evidence, S12/S13 implementation, and any Manager-authored production/test
patch.

## 4. Ownership and task map

This is correction of the existing S11-T03G lineage, not a new feature task.
When route-valid and explicitly reopened, resume exact recovery session
`20260905_043139_01a91f` on the verified recovery worktree/branch. Never resume
frozen old owner `20260903_170546_0d42f6`; never create recovery session 2; never
run two writers. If exact recovery context is not resumable, stop and report the
context/recovery dependency to Codex rather than inventing a replacement.

- `C4-R1-A`: make full-band bootstrap exactly ten, reject ghost registrations,
  restore the complete registry snapshot after every conflict/import/explicit
  registration failure, and prove safe repeated/concurrent construction. Add a
  durable clean subprocess test that starts with an empty registry and does not
  import detector modules or test fixtures before real `JobService()`.
- `C4-R1-B`: complete the fresh Alembic-head revision authority matrix:
  resolver raises; one missing member; two-audio-only registry claiming ten;
  wrong/empty/missing/extra completion revision; current server revision changed
  while completion is old; exact valid ten; no-source and real-source controls;
  API/project readiness `not_run` propagation.
- `C4-R1-C`: Manager-only evidence repair after writers stop: new run-root,
  exact registry, corrected guard command/result, two dedicated T12 runs on
  separate roots followed by full T06, and raw proof for every closure row.

Each task has one owner and disjoint write-set. Maximum safe implementation wave
is **zero while the route blocker exists**; every slot is intentionally unused.
After route clearance, A/B remain one exact writer wave because they share the
registry/authority/test write-set; C waits for writer terminal and immutable
HEAD. Read-only focused checks may parallelize only with unique basetemp,
database, port, cache and evidence roots. Global/leak/Alembic gates are serialized.

## 5. Preflight and byte guard

Before any writer, prove by read-only commands: absolute worktree/branch/HEAD,
porcelain, local==`git ls-remote`, ancestry from `28a2207`, all relevant
worktree cleanliness, zero writer/pytest/product/ffmpeg/watchdog/cron/heartbeat,
and exact recovery/INT01 durable ownership from
`C:\Users\Admin\AppData\Local\hermes\state.db` using only
`mode=ro&immutable=1`. Never copy, vacuum or mutate the DB.

Create a fresh C4-R1 run-root and a manifest for every allowed/protected file:
absolute path, tracked/dirty attribution, SHA-256, bytes, logical lines, mtime;
byte snapshot for critical non-restorable files; verify snapshot hash. Existing
files are bounded preimage patches only. No reset-hard, clean, stash, restore,
rebase, force-push, overwrite, redirection, copy-overwrite or reconstruction.
If a file disappears or shrinks destructively, freeze writer/evidence immediately
and report `BLOCKED_TEST_AUTHORITY` or `BLOCKED_CONTEXT_HEALTH` as applicable.

## 6. Verification order and terminal reports

After a valid exact route and writer terminal, execute in this order:

1. micro clean-process and registry snapshot/rollback repros;
2. full adversarial C4-R1-A/B matrix at 100%;
3. focused/static readers: both complete T03G modules, T05A 14, T12 dedicated
   run #1, T12 dedicated run #2, then complete T06; Ruff, exact mypy and
   `git diff --check`;
4. broad/global retained gates only on frozen bytes, including Alembic fresh
   upgrade, direct OpenAPI, T01 serial 64/64, S10 71/71, hashes, quiescence
   and final local==remote.

Every command must record raw command, start/end timestamp, duration, exit code,
stdout/stderr and unique resource root. A broad green suite cannot waive a red
mechanism row or missing evidence. The Manager must report
`SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW` only if all rows
and artifacts exist; otherwise report the exact blocker. Manager never writes
`APPROVED` or `CLOSED`.

Heartbeat at least every 20 minutes while active; audit after 8 minutes without
progress; report incidents immediately. Temporary network failures wait 5
minutes and retry the same owner/model/route. Do not stop after one worker
response; continue through the terminal condition or an explicit blocker.

## 7. Start now

Start now by loading the full authority and performing the exact route gate.
This prompt is not plan-only: execute through `BLOCKED_MODEL_ROUTE` if the
required route is absent/invalid. Do not dispatch implementation, do not use an
alias, and do not open S12/S13.
