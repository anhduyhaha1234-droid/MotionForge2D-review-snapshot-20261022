# HERMES PROMPT — S11-C4 Production Registry + Fail-Closed Final Exit

Bạn là **Hermes Manager mới, context gọn** cho correction sprint hữu hạn
`S11-C4` của MotionForge2D. Thực thi ngay tới terminal condition; không chỉ trả
kế hoạch và không tự dừng sau khi worker commit.

## 0. Mandatory authority load

Trước mọi preflight/dispatch, đọc TOÀN BỘ:

1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
2. `C:\Users\Admin\MotionForge2D\AGENTS.md`
3. `C:\Users\Admin\MotionForge2D\frontend\AGENTS.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C2_PM_REREVIEW_2026-09-04.md`
8. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C3_PM_REREVIEW_2026-09-05.md`
9. C3 binding prompt, C3 Manager exit/raw packet, T03G/INT01 LOG/REPORT,
   current production source/tests and exact Git tips.

Báo `RULES_LOADED` với path, SHA-256, số dòng và tóm tắt authority. Rules và
current bytes thắng report cũ.

## 1. Verdict, authority và terminal boundary

`AUTHORIZED_TO_DISPATCH` chỉ cho `S11-C4` này.

- `S11-C3 = CHANGES_REQUESTED / NOT_APPROVED`.
- Whole `S11 = NOT_CLOSED`; cấm mở/làm S12 hoặc S13.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Canonical branch: `codex/s11-integration`.
- Expected clean local == remote HEAD:
  `28a22072c27a9cd5d1e5eacca82bf9740ce3558c`.
- T03G branch/worktree is clean at `1135499934f5eba9b812db84c9ca023709d85e58`
  and must fast-forward to canonical before the recovery writer starts.
- T06C/T05A code is retained and read-only. T04B is not dispatched because
  the strengthened real restart proof passes current production.

Green terminal is only:

`S11-C4 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Manager/Hermes never writes `APPROVED`, `CLOSED`, or starts the next sprint.

## 2. Exact model route — no fallback

For the new Manager and every newly opened worker turn in this prompt:

- provider/API mode: `custom` through 9Router;
- base URL: `http://127.0.0.1:20128/v1`;
- exact model ID: `cmc/muse-spark-1.3-contributor`;
- requested reasoning: `max`;
- fallback: **OFF**;
- TTFB timeout: 900 seconds.

Before opening a writer, verify `/v1/models` and make one zero-write route
probe that produces a durable `session_model_usage` row with the exact model,
provider and base URL. The C3 exact route returned 403. If 403/429/route error
persists, follow canonical retry timing on the same route and then stop
`BLOCKED_MODEL_ROUTE` with raw evidence. Never continue via inherited session,
`meta`, `auto`, an alias, DeepSeek or another Muse model. A route failure is
not authority to change the model.

## 3. Preflight, context recovery and byte safety

Before any implementation writer:

1. Prove canonical porcelain empty and local == `ls-remote` == expected HEAD.
2. Prove T03G and INT01 worktrees/branches clean and record exact tips.
3. Prove zero S11 writer/pytest/product/ffmpeg/watchdog/cron/heartbeat. Do not
   create an unbounded watchdog; monitor synchronously/boundedly.
4. Open `C:\Users\Admin\AppData\Local\hermes\state.db` only through SQLite
   URI read-only mode. Never copy, backup, vacuum, mutate or reconstruct it.
5. Create one new evidence root
   `C:\Users\Admin\MotionForge2D-evidence\s11-c4\<run-id>\**` and create
   `manager/REGISTRY.md` before dispatch.
6. Record old T03G context-health facts: owner
   `20260903_170546_0d42f6`, 575 messages/507 API calls at Codex review,
   repeated exact-authority failure across C2→C3, multiple compression/model
   records, and stale “other lanes register detectors” assumption.
7. Confirm no process from the old owner is active. Mark it
   `FROZEN_CONTEXT_UNHEALTHY`; after transfer it must never be resumed.
8. Fast-forward existing clean branch `codex/s11/t03g-0903w8` from `1135499`
   to canonical `28a2207` without rebase/reset/force/history rewrite. Reuse its
   existing worktree; do not create a competing task branch.
9. Capture SHA-256/bytes/lines/status for every allowed existing file with
   the write-set guard. All edits to existing files use bounded preimage patch;
   no whole-file overwrite, redirection, copy/move-overwrite or reconstruction.

Any mismatch is a terminal preflight blocker. Manager does not repair code.

## 4. One recovery implementation owner

Create exactly one **fresh compact recovery session** for the same S11-T03G
lineage and record owner transfer in `manager/REGISTRY.md`. This is not a new
feature Task ID. It is the sole implementation writer in C4.

Worktree/branch:

- `C:\Users\Admin\MotionForge2D-worktrees\s11-t03g-0903w8`
- `codex/s11/t03g-0903w8`, fast-forwarded to canonical `28a2207`

Allowed production/test write-set only:

- `app/persistence/qc_check_runs.py`
- `app/workflow/qc_checks_handler.py`
- `app/workflow/job_service.py`
- `tests/test_s11_t03g_qc_check_job.py`
- `tests/test_s11_t03g_qc_check_api.py`
- one new narrowly named T03G clean-process test file only if subprocess
  isolation cannot be expressed safely in the two existing modules;
- `docs/pm/sessions/S11-T03G/**`;
- new external S11-C4 evidence.

Forbidden: migrations, schemas, QC detector algorithms, T03F orchestrator,
T04/T05/T06 tests/code, frontend, broad refactor, dependency/config changes,
MAIN/root PM docs and any C1/C2/C3 evidence.

### C4-A — deterministic production detector bootstrap

Close the clean-process defect with one explicit server-owned composition path:

1. Constructing the real production `JobService` with its owned worker must
   deterministically register exactly the ten names returned by
   `scope_detectors(SCOPE_FULL)` before a `RUN_QC_CHECKS` handler executes.
2. Register the actual detector entry points/revisions, including the three
   detectors that currently require explicit `register()`. Do not invent a
   duplicate detector implementation, version, dynamic client choice or test-
   only bootstrap.
3. Registration is idempotent for repeated `JobService` construction and
   fails closed on a conflicting name/entry point/version. It must not depend
   on pytest collection order or unrelated module imports.
4. The server-owned full band remains the frozen ten-detector policy contract;
   client inputs never select implementation/provider/entry point.
5. Keep the orchestrator's current unknown-detector rejection. Do not weaken
   it to make startup pass.

Required clean-subprocess executable proofs:

- importing normal app code alone is recorded for diagnostics;
- constructing a real `JobService` on a fresh Alembic-head DB produces an
  exact registry set/order/revision map equal to the binding full band;
- a second construction is idempotent;
- a deliberately conflicting pre-registration fails closed;
- a real full `RUN_QC_CHECKS` submission/worker execution no longer dies with
  `QC_ORCHESTRATOR_MISSING_ARGS` merely because the process started clean.

The subprocess must not import detector modules or test fixtures before the
production bootstrap under test.

### C4-B — revision authority must fail closed

Remove every guessed revision fallback from read authority:

1. Completion `detector_revisions` keyset and values must equal exact current
   server-owned revisions for all ten binding names.
2. Resolver exception, unregistered member, incomplete server map, extra map
   member, empty server revision or conflicting registration returns
   `failed` with readiness `not_run` and a truthful authority detail.
3. Never substitute `1.0.0`, `{}`, manifest/completion values or another local
   convention when server authority is unavailable.
4. A valid full completion with all ten exact server revisions remains
   `completed`/`ready`; valid no-source and real-source controls remain green.
5. Preserve every C2/C3 invariant: unbounded newest-full selection, exact
   schema/policy/evidence/generation/source/count/flag/detector checks, zero-
   item behavior and audio-only non-authority.

Required fresh Alembic-head matrix at minimum:

- only two audio detectors registered + claimed ten revisions => failed;
- exactly one full-band detector unregistered => failed;
- resolver raises => failed with no exception laundering;
- one server revision changed while completion remains old => failed;
- wrong/empty/extra/missing completion revision => failed;
- all ten exact registered revisions => completed/ready;
- previous five C3 identity-tamper rows still fail closed;
- valid no-source and real-source controls remain accepted;
- API/project readiness propagates unavailable revision authority as `not_run`.

### C4-C — bounded hygiene

On files changed by this recovery only, run normal repository-configured Ruff,
not only `--select F`. Fix C4/C3-introduced import ordering and EOF-newline
issues inside the allowlist. Do not expand into unrelated historical lint
cleanup.

### Recovery worker exit gate

Order is mandatory:

1. clean-process RED captured on pre-fix current bytes;
2. micro C4-A/B matrix green;
3. both complete T03G modules green;
4. normal configured Ruff on changed files green;
5. exact retained mypy scope green;
6. own diff-check and write-set guard green;
7. self-review every catch/default and every production import/registration;
8. commit exact allowlist on task branch, report SHA/raw outputs and
   `TASK_SUBMITTED`, then exit.

No push/merge/rebase/reset/stash/clean/force. No second implementation worker.

## 5. Manager independent review

After the recovery writer exits, Manager must inspect code, not only counts:

- prove changed paths are within the exact allowlist and no file shrank beyond
  guard threshold;
- independently rerun clean-subprocess bootstrap without importing tests;
- mutation-probe registry empty/member missing/resolver raise/wrong revision;
- inspect for broad `except`, guessed defaults, hidden test imports and global
  registry pollution;
- verify exact CMC usage row for the recovery session;
- reject overclaim, masked exit or post-gate commit.

Any implementation red returns to the same recovery session. Never resume the
frozen old T03G owner and never create recovery session 2.

## 6. Git-only integration

Only after Manager verifies the recovery commit, resume exact INT01 Git-only
owner `20260903_112116_35051c` on canonical. INT01 may run Git and tests but may
not edit implementation/test bytes.

1. Reconfirm canonical clean/local==remote at `28a2207`.
2. Merge the one exact verified recovery tip conflict-free. Conflict => abort
   and return to recovery owner; INT01 does not resolve code/test conflicts.
3. Prove the recovery tip is an ancestor of canonical candidate HEAD.
4. Run micro/static gates before broad gates. Do not push yet.

## 7. Maximum safe read-only verification

With every writer stopped and one immutable candidate HEAD, run at most three
resource-balanced read-only lanes in parallel. Give every pytest command a
unique short `--basetemp`, every harness a unique DB/managed/evidence root and
no shared ports.

- **Lane V1 — direct risk:** clean-process bootstrap/mutation matrix, both
  T03G modules, both T05A modules.
- **Lane V2 — restart/acceptance:** T06C T12 twice on separate roots, complete
  T06 acceptance, outer acceptance and inner S11 QC suite.
- **Lane V3 — retained/static:** T01 64, S10 full-apply 71, Ruff, exact mypy,
  Alembic, direct OpenAPI, hashes and diff-check.

Parallelize only disjoint read-only commands. Serialize Alembic/global runtime
checks if a tool cannot isolate state. Do not run duplicate broad suites “for
confidence”; one complete final run is sufficient after micro gates are green.

## 8. One complete fail-fast closure ladder

Use PowerShell explicit `$LASTEXITCODE` checks after every external command or
an equivalent fail-fast runner. Save command, start/end timestamps, output and
individual exit. Any red/missing command stops the aggregate; never let a later
green command mask an earlier red.

1. C4 clean-process production bootstrap + revision mutation matrix green.
2. Both complete T03G modules: retain at least `143` plus all C4 nodes.
3. T06C targeted correction/recompute node twice on separate roots, then full
   T06 acceptance retains at least 12.
4. Both T05A modules retain 14/14.
5. Combined focused T03G + T05A + T06C gate green.
6. Normal configured Ruff on all C4 changed files green; `ruff --select F` on
   affected S11 closure files green.
7. `python -m mypy app/persistence/qc_check_runs.py app/persistence/readiness.py --follow-imports=skip`
   prints `Success`.
8. `git diff --check 7751598214eedb6b72e3783e39a2a408721abe40..HEAD`
   exits 0.
9. Alembic reports exactly one head and a fresh isolated upgrade succeeds.
10. Direct `app.openapi()` scan reports path/operation counts and zero duplicate
    operation IDs; do not call a nonexistent test path.
11. Outer acceptance retains at least 12 and includes T12.
12. Inner S11 QC suite retains at least 380 plus all C3/C4 nodes.
13. T01 retains 64/64; S10 full-apply retains 71/71.
14. Frontend/API-route/migration hashes remain unchanged; no migration added.
15. Every verified task tip is contained; canonical porcelain empty; zero
    writer/pytest/product/ffmpeg/watchdog/cron/heartbeat; evidence timestamps
    are after their corresponding tests.

## 9. One push and authoritative packet

Only after all 15 gates are green, INT01 performs one non-force push:

`git push origin HEAD:refs/heads/codex/s11-integration`

Then prove local HEAD == `git ls-remote` remote HEAD. No force/reset/rewrite or
hidden follow-on commit.

Under the exact S11-C4 run root create:

- `manager/REGISTRY.md` with old-owner freeze, recovery transfer, exact session,
  model/provider/base URL, branch/base/tip/status and INT01;
- raw preflight/model probe/guard/process/Git outputs;
- exact recovery prompt and dispatch/usage logs;
- clean-process and mutation probe outputs;
- every one of the 15 gate outputs with individual exit/timestamps;
- `manager/exit/EXIT_VERDICT.md`;
- `manager/exit/NEXT_REVIEW_PACKET.md`.

The packet maps each C3 finding to production lines, exact tests, recovery
session and commit; explicitly states no fallback/no DB copy/no missing gate;
lists actual counts and all skipped lanes. It may claim green only when all
required artifacts exist and local==remote.

Terminal green only:

`S11-C4 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Bắt đầu ngay: full authority load -> exact CMC route probe -> preflight + old
owner freeze/transfer -> one recovery writer -> Manager adversarial review ->
INT01 merge -> three isolated read-only lanes -> all 15 fail-fast gates -> one
non-force push -> terminal packet -> stop chờ Codex.
