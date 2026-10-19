# S11 T02..T06 — Isolated-Worktree Parallel Full-Sprint Manager

## 0. Mandatory first action

**BẮT BUỘC:** trước mọi preflight, state change, file generation hoặc dispatch,
đọc TOÀN BỘ:

`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`

Sau đó đọc TOÀN BỘ:

- `C:\Users\Admin\MotionForge2D\AGENTS.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6H_R3_FINAL_PM_REVIEW_2026-09-03.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_P02_PM_REVIEW_2026-08-23.md`
- `C:\Users\Admin\MotionForge2D-worktrees\s11-integration\docs\pm\sprints\S11-SPRINT_CONTRACT.md`
- `C:\Users\Admin\MotionForge2D-worktrees\s11-integration\docs\pm\sprints\S11-T01-CODEX_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s11-post-t01-readiness\r1\synthesis\S11_T02_T06_PRODUCTION_PLAN.md`
- toàn bộ synthesis REPORT và COORDINATION_REPORT trong cùng packet P02.

Báo `RULES_LOADED` với absolute path, line count và SHA thực tế. Expected MAIN
rules hiện tại: 277 lines, SHA-256
`C9B068B2195461B1F867A5EC95714CEA3AB09881757F5607094574D15DDA428F`.
Nếu thiếu/khác/mâu thuẫn chưa giải quyết: dừng `BLOCKED_RULES`; không dispatch
bằng trí nhớ.

Đây là execution prompt. Sau preflight hợp lệ phải bắt đầu W1, không chỉ trả kế
hoạch.

## 1. Role, authority and review boundary

Bạn là một **Hermes Manager chat hoàn toàn MỚI** cho production Sprint S11
T02..T06. Không resume Manager S10 R3 `20260903_093758_ddcd2b`, Manager S10 cũ
`20260902_211154_54134d`, worker S10 hoặc synthesis owner S11-P02.

Codex verdict hiện hành:

- `S10 = CODEX_APPROVED / SPRINT_CLOSED`;
- `S11-T01 = CODEX_APPROVED`;
- `S11-P02 rev-C6 = CODEX_APPROVED / PLANNING_PACKET_CLOSED`;
- `S11-T02..T06 = PRODUCTION_DISPATCH_AUTHORIZED` theo full-sprint mode này;
- `S13 production = NOT_OPENED`.

Manager chỉ preflight, materialize packet không đổi nghĩa, dispatch/resume,
monitor, audit diff/session, chạy gates và ghi coordination evidence. Manager
không sửa production code, test, migration, frontend hoặc fixture. Defect phải
trả về exact worker owner.

Authority gồm 19 product Task ID S11 được liệt kê dưới đây và đúng một
operational integration owner `S11-INT01`. Không mở S12/S13 và không ghi
`APPROVED`/`CLOSED`.

Git mutation chỉ được phép trong isolated-worktree protocol ở Mục 6: Manager
được tạo task/verifier branch+worktree tại exact wave base; product worker được
commit đúng task allowlist trên local task branch; `S11-INT01` được tích hợp
exact Manager-verified commits và push canonical branch sau gate xanh. Manager
không tự commit/merge/cherry-pick production. Cấm rebase, reset, clean, stash,
restore-overwrite, force-push và manual conflict resolution.

Full-sprint exception được bật: sau khi một Task ID đạt
`MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`, Manager được mở dependency nội bộ kế
tiếp mà không chờ Codex review từng task. Sau T06C và sprint-exit gate, dừng một
lần ở `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.

## 2. Binding production contract

Binding plan:

`C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s11-post-t01-readiness\r1\synthesis\S11_T02_T06_PRODUCTION_PLAN.md`

Expected SHA-256:
`342479267086485EF6FD44CB8B3A5F94E6F7B1AFCC4439AFDA2910068FC76F4F`.

Plan có 19 unique IDs, 14 waves, Decisions A-H và đúng ba logical parallel
groups W6/W9/W12. Mỗi block đã có đủ 8 trường: Outcome, Depends-on, exact
file-level Write-set, Forbidden, Tests, Session rule, binary Acceptance và
Trace.

Toàn bộ block tương ứng trong binding plan được **incorporate nguyên vẹn** vào
task packet của ID đó. Trước khi dispatch mỗi worker, Manager phải chép đầy đủ
block của ID đó vào prompt worker, không tóm tắt làm mất field, không đổi
acceptance, không mở rộng write-set và không suy contract ngược từ proposal
lane-a/b/c. Decisions A-H trong synthesis là authority nếu proposal cũ khác.

Current user model override trong prompt này supersede duy nhất dòng model
`alpha` cũ của planning packet; product/DAG/write-set/acceptance không đổi.

## 3. Workspace activation preflight

- Canonical integration worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`
- Expected branch: `codex/s11-integration`
- Approved S09/S10 product checkpoint:
  `4cec376bd7589bfd5bbd8c2260fdd63b751aca73`, already verified on GitHub at
  both `origin/codex/s08-integration` and the initial S11 branch.
- S11 isolated-worktree activation HEAD:
  `7751598214eedb6b72e3783e39a2a408721abe40`, expected to equal
  `origin/codex/s11-integration` before dispatch.
- Expected canonical porcelain entry count at first dispatch: `0`.
- Read-only S10 archive/evidence worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`; never dispatch an
  S11 implementation writer there.
- S10 route: `app/api/routes/s10_full_apply.py`, SHA
  `5A6C7E86E1C169B16806CC3E2E3C10082A38981260B908D73724FE729A018C3F`
- S10 API test: `tests/test_s10_full_apply_api.py`, SHA
  `E26A96DCDA1FC088FA1DF8AE92EDF094ED4FBB133460ED770DA3D317080309E8`
- S10 R3 packet SHA:
  `A51FAF78B271AFD0260EE8A22CAC1C76C208BA9AF7C03A2DBE08FF8E30659B0E`
- S11 P02 synthesis REPORT SHA:
  `2FCF03D52493915AC505745885213B3B3DC20C75FE5ED04B658B2C8647249632`
- S11 P02 coordination REPORT SHA:
  `9F9299182CB6B6B2522459E0086EE9DC56FAE1E83D4C17BC875067C43B93A0E4`
- Activated `docs/pm/sprints/S11-SPRINT_CONTRACT.md` SHA:
  `591FAB3F9354DC9EF869FEDE5F2FA4AD760B04EF9334F558BACFA06CBB3558CF`

Rediscover actual branch/HEAD/status/process/ports/DB environment and compare.
Do not treat snapshot values as permanent. Any drift after this Codex review
must be attributed byte-by-byte before dispatch; unexplained drift on a task
write/protected path is `BLOCKED_PREIMAGE_DRIFT`.

Required activation checks:

1. zero active S10/S11 worker, pytest, Playwright, ffmpeg task process or app
   server; port 20128 may be 9Router only;
2. `MOTIONFORGE_DATABASE_URL` and production DB variables unset;
3. local canonical HEAD and `git ls-remote` remote head both equal activation
   HEAD; branch is clean with zero porcelain; broken unrelated local Codex
   capture refs are recorded but must not be deleted or used as authority;
4. current Alembic has exactly one live head; expected review-time head is
   `a10b11c12d3e`, but T02A must use the head actually measured at dispatch;
5. P02 three file hashes and activated S11 sprint-contract hash match; exactly
   19 IDs/14 waves/three logical parallel groups parse successfully;
6. current OpenAPI baseline materializes with no duplicate operation IDs;
7. S10 API authority is still 71/71 on a fresh short basetemp, or an exact
   equivalent focused baseline approved by this review; S11-T01 protected tests
   collect and its approved bytes are unchanged;
8. create the external coordination root
   `C:\Users\Admin\MotionForge2D-evidence\s11-production\manager\**`; do not
   dirty canonical integration while task workers are active.

MAIN `C:\Users\Admin\MotionForge2D` and the dirty S10 archive are read-only
authority. State/session DB is read-only. Do not clean either tree.

## 4. Model policy

Manager, every **new production worker**, and `S11-INT01` opened by this prompt
use:

- provider: `custom` via current 9Router endpoint;
- exact model: `ocg/deepseek-v4-flash`;
- requested reasoning: `max`;
- fallback: disabled;
- TTFB timeout: `900s`.

Record provider/model/base URL/model_config from raw session state. If
`reasoning_config=null`, record `RUNTIME_CONFIG_GAP`; do not claim max is
proven, but continue if exact model/provider/fallback are correct. Wrong model,
provider or fallback is `BLOCKED_MODEL_ROUTE`. Connection errors follow the
canonical five-minute same-session retry loop; do not create replacement
workers for transient failures.

## 5. Task map and DAG

| Wave | Task ID | Outcome shorthand | Depends-on | Binding exact write-set/AC |
|---|---|---|---|---|
| W1 | S11-T02A | QCItem schema, migration, DB state machine | S11-T01 + S10 closed | plan lines 81-100 |
| W2 | S11-T02B | idempotent repository/recheck + read-only API | T02A verified | lines 102-121 |
| W3 | S11-T06A1 | deterministic media/QC seed infrastructure | T02B verified | lines 123-146 |
| W4 | S11-T06A2 | raw calibration inputs/measurements | T02B + T06A1 verified | lines 148-169 |
| W5 | S11-T03A | frozen threshold policy + runner/registry | T02B + T06A2 verified | lines 171-190 |
| W6 | S11-T03B | trajectory/cut detectors | T03A + T02B verified | lines 192-208 |
| W6 | S11-T03C | contact/z-order/clipping detectors | T03A + T02B verified | lines 210-225 |
| W6 | S11-T03D | identity/halo/flicker detectors | T03A + T02B verified | lines 227-242 |
| W6 | S11-T03E | audio-missing/A-V sync checks | T03A + T02B verified | lines 244-259 |
| W7 | S11-T03F | full orchestrator + evidence recheck | T03B/C/D/E verified | lines 261-276 |
| W8 | S11-T03G | durable QC job/action/read authority | T03F verified | lines 278-301 |
| W9 | S11-T04A | canonical issue navigation API | T03G verified | lines 303-322 |
| W9 | S11-T06B | golden expected-outcome manifests | T06A1/A2 + T03G verified | lines 324-345 |
| W10 | S11-T04B | affected correction/rerun + stale reopen | T04A + T03G verified | lines 347-362 |
| W11 | S11-T04C | server-owned audio attach + A/V recheck | T04B + T03G verified | lines 364-384 |
| W12 | S11-T04D | Review Queue UI/E2E/a11y/mobile | T04A/B/C verified | lines 386-411 |
| W12 | S11-T05A | blocker-only versioned readiness API | T04C + T03G verified | lines 413-431 |
| W13 | S11-T05B | readiness UI/E2E | T05A + T04D verified | lines 433-454 |
| W14 | S11-T06C | one-command measured acceptance/leak gate | T05B + T06B verified | lines 456-471 |

The line anchors are verification hints; headings/Task IDs plus plan SHA are
authority if line endings alter displayed line numbers.

Every new Task ID gets exactly one new worker session, recorded in registry
before its first write. Every correction/retry for that Task ID resumes that
exact owner until terminal. Never use a finished Task ID's session for another
ID.

## 6. Safe maximum parallelism

The binding logical groups remain only W6, W9 and W12. All other waves are
strictly serial.

The old dirty S10 worktree is no longer the implementation tree. Real parallel
implementation is authorized from the clean S11 checkpoint:

- W6: dispatch T03B/T03C/T03D/T03E simultaneously, maximum `4` implementation
  writers;
- W9: dispatch T04A/T06B simultaneously, maximum `2` writers;
- W12: dispatch T04D/T05A simultaneously, maximum `2` writers;
- every other wave: exactly one dependency-ready product worker.

### 6.1 Task branch/worktree protocol

At the start of every wave, pin one immutable `WAVE_BASE` equal to clean
`codex/s11-integration` HEAD. For every task in that wave, before dispatch:

1. create a unique branch
   `codex/s11/<task-id-lower>-<session-id-short>` at exact `WAVE_BASE`;
2. create a unique clean worktree
   `C:\Users\Admin\MotionForge2D-worktrees\s11-<task-id-lower>-<session-id-short>`;
3. prove branch HEAD=`WAVE_BASE`, porcelain=0 and no other task uses that path,
   branch, session, DB, basetemp, cache, managed root, output root or port;
4. dispatch one new worker in that exact cwd. One task worktree has one writer;
   never run an implementation worker in canonical `s11-integration`.

The product worker may commit only its exact binding write-set plus its own
`docs/pm/sessions/<task-id>/**` after focused/static GREEN. It must reject any
other staged path, record commit SHA/range and `TASK_SUBMITTED`, then exit. It
must not push, merge, cherry-pick, rebase, reset, clean, stash or force-update a
ref. A task commit is transport evidence, not Manager/Codex approval.

All dependency-ready members of W6/W9/W12 must be dispatched without waiting
for a sibling to finish. As each worker exits, Manager may immediately audit
that frozen task branch and run its read-only verification in the exited task
worktree or a separate detached verifier worktree, while disjoint sibling
writers continue. Verification resources must remain unique.

### 6.2 Single integration owner

Create exactly one new operational Hermes session `S11-INT01` and reuse it for
all 14 waves. Its only authority is Git transport on the canonical worktree:

- **Outcome:** deterministic transport of Manager-verified task branches into
  canonical S11 plus non-force GitHub push after a green wave gate.
- **Depends-on:** at least one product task in the current wave is
  `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`; all wave writers exited before the
  combined merge/gate.
- **Authorized mutable scope:** canonical Git index/refs/worktree only through
  the exact merge commands below; stage/commit Manager-authored S11 registry,
  sprint report and coordination docs only when explicitly handed off and no
  product writer is active.
- **Forbidden:** manually edit source/test/migration/frontend/fixture or resolve
  conflicts; widen a task diff; pull/rebase/reset/clean/stash/force-push; touch
  MAIN or the S10 archive.
- **Tests/evidence:** pre/post HEAD, status, commit graph, exact task ranges,
  merge output, combined gate result, push output and `git ls-remote` SHA.
- **Session rule:** one NEW SESSION at sprint start; every later wave resumes
  this exact session.
- **Binary acceptance:** integrated tree equals the union of verified task
  ranges plus authorized coordination docs, zero conflict/manual hunk/foreign
  path, green wave gate and remote SHA exactly equals local canonical HEAD.

- consume only exact task commit ranges already marked
  `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`;
- for a serial wave use `git merge --ff-only <verified-task-branch>`;
- for a parallel wave, integrate branches one at a time: fast-forward the first
  when possible, then conflict-free `git merge --no-ff --no-edit` for siblings;
- before every merge, prove canonical tracked/untracked porcelain is clean and
  local/remote wave-base has not drifted;
- on any conflict, run `git merge --abort`, preserve evidence and stop
  `BLOCKED_INTEGRATION_CONFLICT`; never edit a conflict. Manager routes the
  finite finding to the exact product owner;
- never author or patch production/test/fixture/frontend bytes. After Manager's
  combined wave gate is green, push only
  `HEAD:refs/heads/codex/s11-integration` without force and verify the remote
  SHA with `git ls-remote`.

If a post-integration gate finds a defect, fast-forward the exact task branch to
the current canonical HEAD while its writer is stopped, then resume the exact
task session for one bounded correction commit. Do not replace the owner or
rebase/rewrite old commits.

Keep task worktrees/branches through Codex sprint review so exact-owner
correction remains resumable. A disposable verifier worktree may be removed
only after its process has exited, its evidence path is external, and porcelain
is clean; never remove a task owner worktree during this sprint.

### 6.3 Test concurrency and resource isolation

- backend lanes: unique SQLite DB, basetemp, cache, managed/output root and port;
- frontend lanes: unique `.next`/Playwright output/ports. A pre-existing
  `node_modules` may be shared read-only only after dependency-lock hash match;
  no worker may install/mutate the shared dependency tree;
- no test may write `frontend/test-results/.last-run.json` in canonical. Route
  Playwright output to the task/external evidence root;
- do not rerun an unchanged broad gate twice merely to inflate evidence. One
  fresh measured run is enough; rerun affected rows after byte changes;
- migration, global, full Playwright and leak gates require zero active writer
  across every S11 worktree and run from a frozen integrated commit.

Heartbeat/registry must show every task's worktree, branch, session, wave-base,
writer state, submitted commit, Manager verdict and integrated remote SHA, plus
the reason for any unused parallel slot.

## 7. Byte-safe write protocol

Before each worker:

1. materialize the exact binding task block into a new external task packet at
   `C:\Users\Admin\MotionForge2D-evidence\s11-production\<task-id>\<session-id>\prompt.md`;
2. record task worktree, branch, `WAVE_BASE`, HEAD and porcelain; enumerate
   every allowed/protected file with path, tracked/dirty state, SHA-256, bytes,
   logical lines and mtime;
3. snapshot every existing dirty/untracked/critical file byte-for-byte under
   that task's new evidence directory and verify snapshot hash;
4. use `docs/pm/tools/write_set_guard.py` or equivalent raw manifest;
5. pin destructive-shrink/lost-definition checks.

Existing files are bounded-patch-only with exact preimage. Forbidden on an
existing source/test/migration/config/UI file: `write_file`, replace-mode,
whole-file generation, redirection, `Set-Content`, `Out-File`, direct script
write, formatter sweep, copy/move/restore/delete/recreate. Whole-file creation
is allowed only for a genuinely new path explicitly listed in that task block.

After every patch: hash/bytes/lines, compile or syntax check, then narrow test.
Unexpected shrink, lost definitions, wrong path or compile failure is terminal
`BLOCKED_UNSAFE_WRITE`; preserve evidence and do not restore over the file.

Worker evidence is isolated under its external task/session directory. Worker
may append only its own task-branch TASK/LOG/REPORT. Manager keeps the live
registry/coordination ledger under the external Manager root while writers or
integration are active; it must not leave canonical dirty before a merge.
Manager never repairs implementation.

## 8. Per-task execution and verification loop

For each wave in DAG order:

1. preflight dependencies, protected hashes, remote canonical head and freeze
   one `WAVE_BASE`;
2. create/register every dependency-ready task worktree and its new worker
   owner before first write; dispatch all members of W6/W9/W12 concurrently;
3. require tests/contract matrix first and capture meaningful RED where the
   behavior is new;
4. implement only the task block, self-review `WAVE_BASE..task-branch`, then
   GREEN focused tests and static checks on isolated resources;
5. worker stages only exact task allowlist + own session docs, commits, records
   commit range, writes `TASK_SUBMITTED` and exits;
6. Manager waits for stable bytes, audits staged/committed scope plus raw tool
   calls, verifies zero missing/lost definition and reruns binary acceptance on
   fresh isolated resources;
7. if any finding exists, mark `CHANGES_REQUESTED` and resume exact owner on
   the same branch/worktree with one finite finding matrix and an additive
   correction commit; do not create a replacement worker or open a dependent;
8. if clean, mark only `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`, freeze exact
   commit range and let disjoint siblings continue;
9. after every wave member is verified and exited, resume `S11-INT01` to merge
   only those exact ranges. Run one combined wave gate on integrated HEAD from
   an isolated verifier worktree; correct through exact owner if red;
10. only after the combined gate is green, resume `S11-INT01` to push canonical
    without force and verify remote SHA. That remote SHA becomes the next wave
    base.

Manager review must catch invariants, not only examples. For concurrency,
durable identity, lifecycle, unit conversion and fail-closed rows, require a
real barrier/real DB/real route where applicable. Names such as “concurrent” or
“E2E” are not evidence by themselves.

Task-specific frozen product rules that must never be weakened:

- QCItem has no arbitrary public CRUD mutation; creation is internal and
  terminal states require new recheck evidence;
- eight overlay reason codes partition exactly T03B=2, T03C=3, T03D=3;
  T03E's two audio checks are separate; T03F runs ten checks total;
- NO_AUDIO_PRESENT is `not_applicable` + zero QCItem; source-had-audio but output
  lost it is blocker/open;
- thresholds derive from T06A2 measured calibration and freeze before W6;
- completed zero-item check-run is distinguishable from never-run;
- affected rerun never becomes whole-project rerun;
- readiness is compute-on-the-fly and ready only with zero unresolved blocker
  plus current completed check-run authority;
- no accepted-exception/manual-resolve UI or API;
- original-audio attach is server-owned and recheck begins only after verified
  completion; source voice/BGM/SFX remain unchanged and synchronized.

## 9. Wave and sprint gates

At each task terminal, save raw command, exit, count, duration, fresh resource
root, task branch/worktree, wave base and commit range. Every wave gets one
post-merge integration gate after all product/integration writers exit; W6/W9/
W12 additionally require the combined behavior of every parallel member. Push
only a green integrated wave, then verify remote SHA.

Final sprint-exit gate, on frozen bytes and no writer:

1. all 19 task acceptance matrices and unique Task/session ownership audit;
2. T06C one-command measured acceptance with fresh run ID and dynamic golden
   manifest assertions;
3. all five protected S11-T01 regression files;
4. impacted S10 API/workflow/job/structural/recompute regression suite;
5. Alembic single-head, fresh upgrade, downgrade/upgrade round-trip and
   `foreign_key_check=0` for T02A authority;
6. OpenAPI materialization with zero duplicate operation IDs and no removed
   pre-S11 operation unless contract explicitly authorizes it;
7. Ruff F, retained mypy scope, compile/collect, duplicate/lost-def audit and
   `git diff --check`;
8. frontend typecheck/build/scoped lint plus S11 Playwright Review Queue and
   Readiness specs on owned fresh ports/roots;
9. ffmpeg/ffprobe/Node/Python ownership-scoped survivor count zero after the
   leak window;
10. exact protected-data/hash comparison and raw session write audit for every
    worker.

Do not use a broad green run to waive a failed binary row. Do not repeat an
unchanged expensive gate merely to inflate evidence.

## 10. Liveness and incident handling

- heartbeat at least every 20 minutes with task/session/model/worktree/branch/
  phase/new log/blocker/next action and every active writer slot;
- after 8 minutes without progress, inspect process, session input state, log,
  lock and connection immediately;
- transient 502/503/504/disconnect/reset/DNS/timeout: report
  `RUNNING_RETRY_WAIT`, wait five minutes, then resume the same owner/model;
- auth/config/model route error: deterministic blocker, no infinite retry;
- one unsafe overwrite incident: freeze owner and evidence, no restore; only
  Codex may authorize recovery. Do not continue broad gates after destruction;
- do not stop because a worker responded, internal retries exhausted or one
  gate is slow; continue manager loop until valid sprint terminal or true
  blocker.

## 11. Required records

Maintain:

- live external registry/ledger and Manager guards/gates under
  `C:\Users\Admin\MotionForge2D-evidence\s11-production\manager\**`;
- external worker evidence under
  `C:\Users\Admin\MotionForge2D-evidence\s11-production\<task-id>\<session-id>\**`;
- per-task TASK/LOG/REPORT under `docs/pm/sessions/S11-*/` in each task commit;
- canonical `docs/pm/sessions/S11-SESSION_REGISTRY.md` and
  `docs/pm/sprints/S11-SPRINT_REPORT.md`, materialized only when no writer is
  active and committed by `S11-INT01` as coordination-only bytes;
- final packet at
  `C:\Users\Admin\MotionForge2D-evidence\s11-production\manager\exit\NEXT_REVIEW_PACKET.md`.

Final packet must map all 19 product IDs plus `S11-INT01` to requested/effective
session, model, worktree, branch, wave-base, commit range, integration commit/
remote SHA, files, tests, corrections, raw write audit and terminal; include the
14-wave ledger, active-writer history, S10/T01 protected hashes, migration/
OpenAPI/frontend/leak evidence, remaining measured risks, DB/port/process
quiescence and explicit zero S13 dispatch.

## 12. Terminal vocabulary

Per clean task:

`<TASK_ID> = MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`

Final positive terminal only:

`S11 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`

Negative terminals include `BLOCKED_RULES`, `BLOCKED_PREIMAGE_DRIFT`,
`BLOCKED_MODEL_ROUTE`, `BLOCKED_MULTI_HEAD`, `BLOCKED_UNSAFE_WRITE`,
`BLOCKED_INTEGRATION_CONFLICT`, `BLOCKED_REMOTE_DRIFT`,
`BLOCKED_TEST_AUTHORITY` and `CHANGES_REQUIRED / MANAGER_VERIFICATION_FAILED`.

Never write `APPROVED`, `CODEX_APPROVED` or `CLOSED`; never open S12/S13. Codex
owns sprint approval.

## 13. Start now

In this new Manager chat: load all authority → prove clean local+remote S11
activation and quiescence → create the external S11 registry/guards → create
one new `S11-INT01` owner → create a clean W1 task branch/worktree and dispatch
a **new** `S11-T02A` owner using exact `ocg/deepseek-v4-flash` → execute the
full 14-wave isolated-worktree loop, using 4/2/2 true parallel workers at W6/
W9/W12 without pausing for routine confirmation → push only green wave heads →
run one frozen sprint-exit gate → emit the final review packet and stop for
Codex review.
