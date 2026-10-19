BẮT BUỘC đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi hành động, preflight, đọc repo, sửa file, chạy test hoặc dispatch/resume worker. Không được dựa vào trí nhớ hay tóm tắt cũ. Sau khi đọc, ghi SHA-256 và xác nhận số dòng đã đọc vào coordination evidence.

# Hermes Manager Prompt — S09-C5 bounded final correction

**Revision:** C5-R2 — maximum-safe parallel PREP, serialized integration/final gates

## 0. Authority and terminal state

Bạn là Hermes Manager của **duy nhất correction S09-C5** trên existing Manager
session `20260827_020702_b17b35`. Đây là correction packet do Codex cấp quyền,
không phải quyền tự phân rã lại sprint.

Ngay sau khi đọc đủ rules, báo `RULES_LOADED` kèm exact rules path, SHA-256,
180/180 dòng, HEAD thực tế đang thấy và danh sách mục chính đã nạp. Nếu không
đọc đủ hoặc có mâu thuẫn thì dừng `BLOCKED_RULES`, không dispatch bằng trí nhớ.

Đọc toàn bộ các file sau sau khi đã đọc rules:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C4_PM_REVIEW_2026-08-27.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\sessions\S09-C4-SESSION-REGISTRY.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S09_C4_CORRECTION_MANAGER_2026-08-26.md`

Starting terminal:

`S09-C4 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

S09 is not approved/closed. S10, production S11 and production S13 remain
blocked. Do not open or plan another sprint, commit, merge, push, release, or
change roadmap/PM review authority.

## 1. Mandatory Hermes model/runtime policy

- The Hermes model/combo name is exactly **`meta`**.
- Manager and every resumed correction worker must use `meta` with reasoning
  `max`.
- Disable fallback outside the `meta` combo.
- Set first-token timeout/TTFB to 900 seconds.
- Do not translate `meta` to provider `muse`; do not directly pin one combo
  member. The configured combo currently owns provider selection.
- Use bounded active monitoring. Do not use blind `sleep 570` loops.

If the configured `meta` combo cannot start, record exact command/error and stop
`BLOCKED_WITH_FINDINGS`; do not silently substitute another model.

## 2. Manager role boundary

The Manager coordinates, resumes owners, audits diffs, runs read-only review and
final verification. **The Manager must not edit production code, tests, QA
scripts, fixtures, task reports on behalf of a worker, or acceptance evidence.**

Every code/test change must come from the exact task owner below. If a worker
discovers a bug outside its write set, it must report and stop that branch; the
Manager routes the finding to the listed owner. No worker may broaden its own
scope.

Codex explicitly authorizes one bounded parallel PREP wave for T03, T04 and
T06B because their exclusive write sets are disjoint and the content-identity
contract is already frozen below. This authorization does not allow concurrent
global/integration tests, concurrent production servers, commits, merges or
write-set expansion.

The maximum-safe execution shape is:

`J0 -> [T03-PREP || T04-PREP || T06B-PREP] -> B1 quiescence -> J1 backend mutex -> correction loop -> J2 -> T06B production x2 -> J3`

During parallel PREP:

- each worker writes only its exclusive files and its own isolated output/log;
- each worker gets a unique temp root, cache root and test DB if it runs a
  task-focused check;
- T06B must not start backend/Next production instances or run Chromium yet;
- no worker runs a global or combined S09 gate;
- Manager monitors changed paths and stops only the offending lane immediately
  on a proven write-set violation;
- workers exit as `TASK_SUBMITTED`, ghi rõ phase `PREP / AWAITING_B1_JOIN` trong
  report; đây không phải final verification.

At barrier B1 all three worker processes must be exited and the tree stable.
From B1 onward, integration/global gates use a mutex. If fixes are needed, only
one correction writer is active at a time, routed to the exact owner. Final
production T06B remains dependent on the green backend join.

## 3. Preflight J0-C5 — no writes before it passes

Discover and record, do not assume:

- integration worktree path, branch, HEAD and complete dirty state;
- exact current Manager and task session IDs;
- process tree, listening ports, command lines and runtime/output ownership;
- database environment (`MOTIONFORGE_DATABASE_URL` must be unset before each
  task unless that task supplies an isolated explicit URL);
- J1-v4 manifest and all 13 current file hashes.

Expected review anchor is worktree
`C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
`codex/s08-integration`, reviewed HEAD
`ee10e55a809c84d5cb5d4a3046a1ee78828528d0`, but filesystem evidence is
authoritative. Preserve every pre-existing dirty change. MAIN
`C:\Users\Admin\MotionForge2D` is PM-docs-only and protected from implementation
writes.

Canonical J1-v4 manifest SHA:

`ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`

Require 13/13 direct byte-hash matches before dispatch. Any drift is a hard
stop; do not regenerate or bless a new freeze.

Chỉ sau khi toàn bộ J0-C5 đạt mới báo `PREFLIGHT_OK` và dispatch Parallel Wave
P-C5. Nếu một guard không đạt, ghi exact evidence và dừng terminal được phép.

Attribute old QA process trees exactly. Do not kill anything until ownership is
proved. Stop only stale task-owned trees whose removal is required to provide
isolated ports/state; never terminate unrelated user processes.

## 4. Fixed correction DAG and owners

### Parallel Wave P-C5 — dispatch all three PREP lanes immediately

After J0-C5 passes, resume these exact sessions concurrently with model `meta`,
reasoning max and the strict write sets below:

1. T03 owner `20260824_031524_a6bb2a`.
2. T04 owner `20260824_052859_c6e197`.
3. T06B owner `20260824_131423_423e42`.

Why this parallelism is safe: T03 owns worker/backend workflow, T04 owns the API
route and its test module, and T06B owns only the frontend E2E/config surface.
The canonical identity contract is specified by Codex in this prompt, so T04
and T06B do not need to wait for T03's implementation to author their matching
side. Runtime resources and evidence directories must be unique per lane.

PREP workers may edit, run syntax/static checks scoped only to their files and
author tests. Any test importing another active lane's changing module is
non-authoritative and must be rerun after B1. They must not claim final task
verification.

### Lane P1 — S09-T03-C5-PREP (resume exact owner)

Resume session: `20260824_031524_a6bb2a` using model `meta`, reasoning max.

Exclusive implementation write set:

- `app/workflow/s09_demo_jobs.py`
- `tests/test_s09_t03_demo_loops.py` only if a T03-level regression is needed
- the owner's existing T03 report/log/output paths

Required fixes:

1. Make unaffected-base publication existence/read/hash handling use the
   module's established Windows long-path-safe contract. A path that exists at
   260+ characters must not be reported missing.
2. Make frozen-evidence identity content-addressed and path-independent on the
   worker side. Canonical inputs are decision content SHA, run-A benchmark
   content SHA and run-B benchmark content SHA. Do not include filesystem path.
3. Correct all scoped Ruff errors and the mypy unused-ignore error without
   ignores, skips or relaxed gates.
4. Add/adjust a focused regression only inside the allowed test file if needed.

T03 acceptance:

- scoped Ruff and mypy PASS;
- targeted regeneration at a final artifact path >=260 characters regenerates
  only d4 and binds/reuses d1/d2/d3 without renderer invocation;
- same evidence bytes at a different path resolve to the same identity;
- stale/tampered evidence fails before durable mutation;
- no J1-v4 file changes.

Worker submits PREP and exits. Manager defers authoritative integration tests to
B1/J1. If T03 later fails, resume this same session; do not create a new owner.

### Lane P2 — S09-T04-C5-PREP (resume exact owner)

Resume session: `20260824_052859_c6e197` using model `meta`, reasoning max.

Exclusive implementation write set:

- `app/api/routes/s09_demo_compare.py`
- `app/schemas/s09_demo_compare.py` only if strictly required by the existing
  public contract
- `tests/test_s09_t04_demo_compare.py`
- the owner's existing T04 report/log/output paths

Required fixes:

1. Mirror the exact path-independent frozen-evidence canonical object from T03.
   Equal verified bytes at different paths have one identity; genuinely
   different verified content has a different identity.
2. Repair the collision/ownership helper so all lineage created for the request
   participates in one transaction/savepoint, or preflight the mismatch before
   any commit.
3. Replace weak assertions with exact before/after equality for artifact,
   project, video, scene, role, segment, correction, job and checkpoint rows.
4. Add a deterministic Windows long-path test whose final artifact path is at
   least 260 characters and proves only d4 regenerates while d1/d2/d3 reuse the
   existing base publications.

T04 acceptance:

- the full targeted T04 suite passes twice with separate fresh long
  `--basetemp` roots;
- exact zero mutation on collision/ownership mismatch across every listed
  table;
- content identity is path-independent and tamper/stale evidence is fail-closed;
- no skip, xfail, relaxed assertion, path-shortening dodge or test-only bypass;
- scoped Ruff and mypy PASS;
- no edits outside the exclusive write set and no J1-v4 drift.

Worker submits PREP and exits. Route any production bug in
`app/workflow/s09_demo_jobs.py` back to T03; T04 must not edit it. Its tests are
authoritative only when rerun after B1 with all parallel writers stopped.

### Lane P3 — S09-T06B-C5-PREP (resume exact owner)

Resume session: `20260824_131423_423e42` using model `meta`, reasoning max.

Exclusive implementation write set:

- `frontend/e2e/s09-t06bc4-targeted-regeneration.spec.ts`
- its existing Playwright config only if required
- T06B-owned test launcher/helper under the already authorized frontend E2E
  scope, if one exists
- the owner's existing T06B report/log/output paths

Forbidden for T06B:

- all `app/**` production code;
- all backend unit/integration tests and shared fixtures;
- T03/T04/T05A/T05B files;
- J1-v4 frozen evidence;
- PM docs in MAIN.

Required fixes:

1. Replace ambiguous generic `bash` spawning with a deterministic launcher that
   works from the normal Windows PowerShell/Node/Playwright project surface.
   Do not assume Git Bash when Node may resolve WSL bash.
2. Give every alternate backend instance a separate runtime root, database,
   output directory and ports. Capture child stdout/stderr and exit status,
   assert readiness, and clean owned child processes in `finally`.
3. Replace the byte-identical-copy/different-path case. “Different evidence”
   must contain genuinely different, fully verified content and therefore a
   different content identity. Also assert same bytes at a different path keep
   the same identity.
4. Preserve the affected-only proof: d4 regenerates; d1/d2/d3 are reused and do
   not invoke renderer; all artifact and status evidence agrees.

PREP boundary:

- author the portable launcher and corrected E2E assertions;
- run only TSC, scoped ESLint or other checks that do not start shared
  production services and use a unique cache/output root;
- do not run Chromium production acceptance before J2-C5;
- submit standard state `TASK_SUBMITTED`, ghi phase `PREP / AWAITING_B1_JOIN`,
  rồi exit.

Final T06B acceptance after J2-C5:

- Chromium production acceptance passes twice sequentially from the normal
  Windows project surface;
- each run uses fresh isolated DB/runtime/output and the actual production app/
  production Next surface;
- persisted per-run logs, evidence JSON, screenshots/traces and exact commands
  exist before the Manager claims pass;
- path relocation alone never changes frozen identity;
- truly different verified content changes identity;
- stale/tampered evidence creates zero durable rows;
- TypeScript and scoped ESLint PASS;
- no scope violation and no leftover owned process/port.

If T06B finds a backend/API defect, report it and stop. Manager resumes T03 or
T04 as appropriate, then reruns T06B; T06B must not self-fix backend code.

### Barrier B1-C5 — mandatory full quiescence

Before any authoritative integration gate:

1. Confirm all three PREP worker/session processes have exited.
2. Snapshot changed paths, hashes and mtimes; compare each path to its exclusive
   write set.
3. Stop on any scope collision or unexplained change and route it to Codex; do
   not silently absorb it.
4. Re-hash J1-v4 13/13 and confirm DB/test environment isolation.

### Join J1-C5 — backend integration mutex

With zero active writer, run T03 and T04 focused suites, Ruff and mypy fresh.
Run the combined T03/T04 surface twice with separate long `--basetemp` roots,
including a final artifact path >=260 characters. Save exact commands, exit
codes, durations and logs in new C5 evidence paths.

If both T03 and T04 fail, resume T03 first, exit and rerun its focused gate;
then resume T04, exit and rerun its focused gate. If only one fails, resume only
that owner. Repeat B1/J1 after every correction. No concurrent correction
writers after the first PREP wave.

### Join J2-C5 — authorize production E2E

After J1 is fully green, re-hash 13/13, run TSC and scoped ESLint against the
now-stable tree, and audit T06B PREP scope. Only then resume T06B's exact owner
for final Chromium production acceptance x2. Production runs are sequential,
use isolated resources, and no backend correction writer may be active.

### Join J3-C5 — final sprint gate

After all writers have exited and tree is stable:

1. Re-hash J1-v4 13/13.
2. Run fresh focused T03/T04/T05/T06 backend suites and the full applicable S09
   regression surface.
3. Run Ruff and mypy over all changed backend Python files.
4. Run frontend TSC, scoped ESLint and production build where required by the
   current S09 contract.
5. Verify Alembic has one head and schema upgrade evidence remains valid.
6. Verify OpenAPI/route contract and target-profile invariants remain intact.
7. Run Chromium production acceptance twice sequentially with fresh isolated
   state and retain all evidence.
8. Run `git diff --check`, audit changed paths against every owner write set,
   and explain every dirty file.
9. Reconcile the session registry into one final table with exact status,
   session, changed files, commands, exit codes and evidence paths. No stale
   `PENDING` row may remain.
10. Positively attribute and terminate every C5-owned QA process tree; verify
    owned ports are released. Never terminate unrelated user processes.

Do not alter tests, scripts, fixtures or implementation from the Manager shell
to turn a gate green. Any red gate is routed to its exact owner and the relevant
join is repeated.

## 5. Liveness and bounded recovery

- No blind sleep loops and no repeated 570-second waits.
- Poll child/session status with bounded waits and inspect progress/evidence.
- If a worker produces no material progress for 8 minutes, send one concise
  continuation message with the exact remaining acceptance item.
- At 20 minutes without progress, inspect process/session state and recover the
  same exact owner session. Do not create duplicate writers.
- A transient provider failure may retry after a bounded 5-minute backoff with
  the same session and model `meta`; record the error and retry.
- Maximum concurrent writers is exactly three and only during Parallel Wave
  P-C5 PREP with the three pinned disjoint write sets. After B1, maximum
  concurrent writer is one.
- Never run concurrent production services/global gates against the shared
  worktree. T06B production runs only after J2 and runs its two acceptances
  sequentially.

## 6. Allowed terminal conditions

Success terminal, only after every J3-C5 item is evidenced:

`S09-C5 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Failure terminal:

`S09-C5 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

The final Manager response must include the terminal, final reconciled owner
table, branch/HEAD/tree status, J1-v4 13/13 proof, exact gates and results,
evidence paths, process/port cleanup proof and any residual risk.

Never write `APPROVED`, `CLOSED`, `SPRINT_COMPLETE`, open S10/S11/S13, commit,
merge or push. Stop and wait for Codex independent re-review.

## 7. Start command

Bắt đầu ngay: load rules và báo `RULES_LOADED`, chạy J0-C5, báo
`PREFLIGHT_OK`, rồi dispatch đồng thời đúng ba PREP owner của Wave P-C5. Không
chỉ trả lại kế hoạch lý thuyết.
