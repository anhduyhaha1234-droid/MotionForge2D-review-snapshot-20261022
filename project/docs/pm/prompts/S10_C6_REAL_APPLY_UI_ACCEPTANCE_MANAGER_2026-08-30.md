Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, coordination write hoặc worker resume. Sau đó báo `RULES_LOADED` kèm absolute path, logical line count, SHA-256, toàn bộ section rules đã nạp, branch/HEAD/dirty state thực tế. Nếu thiếu file, chưa đọc đủ hoặc có mâu thuẫn chưa giải quyết, dừng `BLOCKED_RULES`; không điều phối bằng trí nhớ hoặc report cũ.

Tiếp theo đọc TOÀN BỘ `C:\Users\Admin\MotionForge2D\AGENTS.md`, mọi nested `AGENTS.md` áp dụng; local Next.js docs được nested AGENTS yêu cầu trước khi worker sửa frontend; `docs/pm/CODEX_PM_HANDOFF.md`; `docs/pm/ROADMAP.md`; `docs/pm/SESSION_PROTOCOL.md`; `docs/pm/README.md`; `docs/pm/TARGET_PROFILE_2D_SOURCE_LOCKED.md`; `docs/pm/reviews/S10_C5_PM_REVIEW_2026-08-30.md`; prompt C5 `docs/pm/prompts/S10_C5_APPLY_LINT_CURRENT_BUILD_EXIT_MANAGER_2026-08-30.md`; current `docs/pm/sessions/S10-SESSION_REGISTRY.md`; `docs/pm/sprints/S10-SPRINT_REPORT.md`; và TOÀN BỘ TASK/LOG/REPORT hiện hành của T04B và T04C. Báo `WORKSPACE_INSTRUCTIONS_LOADED`. Không chỉ trả kế hoạch: bắt đầu preflight và thực thi ngay.

# MotionForge2D — S10-C6 real Apply UI acceptance correction

## 1. Authority, verdict và mục tiêu

Bạn là Hermes Manager, không phải Codex Reviewer và không phải production writer. Manager chỉ preflight, resume exact owner, monitor, kiểm tra write-set, chạy join/exit gates và append coordination evidence; Manager không tự sửa code/test/UI/backend/migration/config.

Codex verdict hiện hành:

- `S10-C5 = CHANGES_REQUESTED / NOT_APPROVED`.
- C5 frontend lint/TypeScript/current build đã green; backend, authority, correction, recovery, structural measurement, media/long-path và hai corrected-build vertical runs đã được Codex kiểm chứng độc lập là green.
- Blocker duy nhất là P1 acceptance integrity trong `frontend/e2e/s10-apply-ui.spec.ts`: các test có thể pass ở empty state mà không click Apply/Cancel/Retry/Resume, không quan sát real progress/evidence/Review; mobile bị skip bởi current project config.
- Đây là bounded C6 live-UI acceptance correction. Không mở S11/S12/S13 và không viết lại backend đã green.

MAIN `C:\Users\Admin\MotionForge2D` là protected read-only đối với worker. Implementation authority duy nhất là `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`. Không commit/push/merge/reset/checkout/restore/clean/stash/delete hoặc ghi đè foreign dirty state.

## 2. Model policy — bắt buộc OCG DeepSeek v4 Flash max

Mọi worker resume trong prompt này phải dùng exact model ID `ocg/deepseek-v4-flash`, reasoning `max`, fallback `OFF`, `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`.

Working launch form phải được harmless-route probe và ghi evidence trước dispatch:

`hermes --resume <exact-session-id> -m ocg/deepseek-v4-flash --yolo`

Effective route phải được chứng minh là OCG/9Router `ocg/deepseek-v4-flash`. Cấm raw alias `deepseek-v4-flash`, `meta`, `muse`, `openrouter`, `cmc` hoặc model/fallback khác. Không log secret/token. Sai hoặc unavailable route => `BLOCKED_MODEL_ROUTE`, không fallback.

Lỗi 502/503/504/524/disconnect/network timeout: báo ngay, giữ `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume đúng session/prompt/model; lặp theo canonical rules, không retry dồn. Lỗi model/auth/quota xác định thì dừng blocker tương ứng.

## 3. Stable preflight và frozen baselines

Trước mọi resume:

1. Rediscover MAIN/integration branch, HEAD, `git status --porcelain`, diff attribution, process/listener ownership và latest registry/log mtime; không kế thừa snapshot.
2. `MOTIONFORGE_DATABASE_URL` phải `UNSET`; mọi test/runtime dùng fresh isolated DB, cache, basetemp, runtime/output roots và owned ports. Không dùng/tắt dịch vụ người khác.
3. Chứng minh zero active S10 writer. Không kill process nếu thiếu exact PID + command line + launch-record ownership.
4. Re-hash frozen J1-v4 13/13 và EOL contract. Drift => `BLOCKED_J1_DRIFT`.
5. Capture SHA-256 current backend S10 production files, migration, eight backend tests, current frontend Apply production files/config, current BUILD_ID `rbYCsFU8q82gvOvcRhJSA` nếu còn đúng, manifest, và hai C5 run bundles. Backend/migration/J1 hashes là C6 no-write baseline.
6. Re-run exact max-warning Apply lint, TSC, build validator 7/7, direct current Apply-page input-hash-to-manifest check, and the current focused UI suite. Record expected current UI evidence smell: quick empty-state pass and one mobile skip. Any unrelated drift/failure must be attributed before dispatch.
7. Inspect actual public routes and existing canonical S10 fixture/setup helpers before authoring tests. Do not invent API paths or use report prose as product truth.

## 4. Dependency DAG và parallel policy

Serialized default DAG:

`PREP -> S10-T04B-C3 -> J6-UI -> EXIT`

Conditional branch only if T04B changes production frontend/build input:

`PREP -> S10-T04B-C3 -> J6-UI -> J6-BUILD -> S10-T04C-C5 -> EXIT`

Không parallel writer. Read-only probes có thể song song khi tài nguyên độc lập. Không tạo replacement session. T04C không được resume nếu chỉ test/evidence/config changed and current C5 production build remains byte-identical; T04C bắt buộc resume if any production build input changed.

## 5. S10-T04B-C3 — non-vacuous live-product UI acceptance

- **Exact owner/session:** S10-T04B / `20260828_020206_b1f8af`.
- **Primary outcome:** replace acceptance theater with deterministic real-browser proof for the user-facing `/apply` workflow.
- **Depends on:** PREP green and exact C5 finding reproduced.
- **Initial exclusive writes:**
  - `frontend/e2e/s10-apply-ui.spec.ts`;
  - new bounded `frontend/playwright.s10-ui.config.ts` and new helpers under `frontend/e2e/helpers/s10-apply-ui/**` only when needed for isolated service/fixture ownership;
  - append-only `docs/pm/sessions/S10-T04B-apply-ux/{TASK,LOG,REPORT}.md`;
  - new evidence only under `output/s10/c6/t04b-c3/**`.
- Existing T04C files (`frontend/e2e/s10-full-apply.spec.ts`, its global setup and `frontend/playwright.s10.config.ts`) are read-only. Their helpers/fixtures may be imported or invoked read-only when contracts fit.
- Backend, migrations, J1, S11, S12 and S13 are frozen read-only.

### 5.1 Test-environment truth

Use fresh isolated DB, managed artifact/runtime/cache/output roots, and Manager/worker-owned backend + production frontend PIDs/ports. Record launch commands, PID ownership, base URLs, DB/root identity, BUILD_ID and cleanup. Tests must run against the real product backend and current production frontend, not a static mock page or dev-only replacement.

Initial immutable fixture authority may use the established canonical setup and direct ORM only when no public creation API exists for source media, structural rows, checkpoint inputs or equivalent pre-run fixtures. Every fixture shortcut must be enumerated and justified. Demo approval/checkpoint selection, Apply submission, returned run identity, progress, action transitions, correction/evidence and Review truth after start must come through product UI/public APIs; direct DB status/evidence mutation is forbidden.

Cấm `page.route`, mocked/fake API response, monkeypatch product handler, hard-coded successful status, direct SQLite run/action/status patch, copied old response, arbitrary sleep as truth, or acceptance from stale C4/C5 run IDs.

### 5.2 Required live scenarios — binary, no vacuous branch

Each named scenario must establish its own deterministic precondition and execute all core assertions. Cấm `if (visible)`, permissive `.or(empty/loading/error)` for a scenario claiming progress/evidence/action, silent early return, `test.skip`, `fixme`, retry-to-hide-flake or assertion weakening.

1. **Approval gate:** with a real selected project/video/checkpoint lacking current Demo approval, assert `apply-submit` is actually disabled and the exact truthful VN reason is visible. Create current approval through the product contract, select the same authority, then assert the button is enabled. A non-empty helper alone is insufficient.
2. **Submit from UI:** click the enabled Apply button. Observe the real product request and successful response, extract the returned durable run ID, and prove the displayed run, URL query and local storage all carry that exact ID/project. Confirm it exists through the public status API.
3. **Reload/history:** on real run A, reload and retain exact identity; navigate to real run B through supported UI/URL behavior; Back and Forward must switch displayed/polled identity correctly without a replace loop or stale storage override.
4. **Progress truth:** hold or create a real nonterminal queued/running run through controlled product process ownership, not DB patching. Assert visible backend-derived status/progress/chunks against the public status response; do not accept empty/loading/error as success.
5. **Cancel:** click the visible enabled Cancel control on a cancellable real run, observe the real action request/response, poll public backend state to terminal cancelled semantics, and assert UI truth survives reload.
6. **Retry:** establish a genuine retryable run using supported product failure/cancel semantics, click Retry, observe the action response and new/current identity semantics defined by the API, then assert backend and UI transition. Do not assume Retry semantics; derive expected behavior from current product contract.
7. **Resume:** establish a genuine resumable interrupted/leased run through controlled product stop/restart or supported API semantics, click Resume, observe the action response, then assert lease/recovery and UI status from public truth. Separate runs for Cancel, Retry and Resume are allowed and preferred when state machines conflict.
8. **Structural evidence and Review:** complete at least one real run, initiate structural compare through the UI, observe `REVIEW_REQUIRED` with actionable role/layer/segment/route evidence and assert Review is enabled only under the real allowed state. Also produce a genuine missing/tampered-authority `BLOCKED` result through the supported product contract and assert Review remains disabled. Do not inject the structural response.
9. **Project Detail entry:** with a deterministically seeded project row, assert the actual project-detail link reaches `/apply` with the expected project selection. No `count()===0` early return.
10. **Mobile execution:** execute, not skip, a 390x844 project/case; assert horizontal overflow <= 1, core button/helper visibility and no clipping. Desktop Chromium must also execute. Project names/config must make both paths unavoidable in the recorded command.

Every action scenario must save compact evidence: test result, request method/path/status, run/project/checkpoint IDs, before/after product statuses, URL/storage identity, BUILD_ID and relevant artifact/report paths. Do not log secrets or dump oversized bodies.

### 5.3 Conditional production correction authority

Test/evidence is the expected change. If and only if the live tests expose a reproducible defect in the original T04B production frontend scope, the same exact owner may correct it in:

- `frontend/src/app/(app)/apply/**`;
- `frontend/src/features/apply/**`;
- bounded `frontend/src/lib/api.ts` only for existing Apply contracts;
- `frontend/src/components/layout/AppNav.tsx` or `frontend/src/app/(app)/projects/[id]/page.tsx` only for the already-owned navigation entry behavior.

Before such a write, append exact failing request/UI evidence and file ownership rationale to T04B LOG. No redesign, dependency upgrade, config weakening, backend change, unrelated cleanup or S11/S13 edit. Any needed path outside this list => stop `BLOCKED_SCOPE_EXPANSION` for Codex.

### 5.4 T04B worker gates and terminal

- New live UI suite passes on desktop and 390px mobile with zero skip.
- Exact max-warning lint over Apply features, Apply route page, new/changed UI spec/config/helpers and both retained S10 E2E specs; zero warning/error.
- `npm exec tsc -- --noEmit` green.
- Diff-check and exclusive write-set audit green.
- Worker appends actual commands, exits, identifiers and artifact paths to TASK/LOG/REPORT and ends `TASK_SUBMITTED`; never `APPROVED/CLOSED`.

## 6. J6-UI — Manager independent join gate

Manager reruns rather than trusts worker prose:

1. SHA/write-set audit: zero backend/migration/J1/T04C/S11/S12/S13 drift. Attribute every frontend/test/config diff to T04B scope.
2. Run exact lint with `--max-warnings 0` including `src/features/apply/**/*.{ts,tsx}`, `src/app/(app)/apply/page.tsx`, `e2e/s10-apply-ui.spec.ts`, `e2e/s10-full-apply.spec.ts` and any new C6 helper/config source.
3. Run `npm exec tsc -- --noEmit`.
4. On a second fresh isolated DB/runtime/output/ports set, run the complete live UI suite against the real product production frontend. Require every scenario in §5.2, desktop+mobile, zero skip, zero flaky retry, no empty-state substitute.
5. Independently inspect trace/report/request evidence to prove Apply, Cancel, Retry, Resume, compare and Review were clicked and their public product responses/states were asserted. A green Playwright summary alone is insufficient.
6. Re-run J1-v4 direct hashes, build validator 7/7, backend freeze hashes and process/port cleanup.

If green and production source/build inputs are byte-identical to C5, record `J6-UI = MANAGER_VERIFIED`, retain C5 BUILD_ID and two C5 vertical runs by hash/reference, then proceed directly to EXIT. Do not rerun T04C just to create cost.

If a real flaky/non-deterministic failure appears, resume the same T04B owner with exact evidence; do not create a new session or weaken assertions. If backend/cross-scope change is required, stop for Codex.

## 7. Conditional J6-BUILD and S10-T04C-C5

This section runs only if any production frontend build input changed.

### J6-BUILD

Manager must:

1. Run exact max-warning lint and TSC green.
2. Build a fresh Next production build; record new BUILD_ID and manifest.
3. Run `node output/s10/run-s10.js --verify-build-only` and require 7/7, current Apply input hashes matching manifest, required fallback origin 8888 present and forbidden QA origins absent.
4. Re-run the complete live UI suite against this exact new build.
5. Prove backend/migration/J1 frozen hashes unchanged.

Only then resume T04C.

### S10-T04C-C5 — two fresh vertical runs if build changed

- **Exact owner/session:** S10-T04C / `20260828_023122_76b87e`.
- **Writes:** append-only T04C TASK/LOG/REPORT and new evidence under `output/s10/c6/t04c-c5/**`; existing T04C E2E/config may be edited only if the new build truth cannot be exercised without a bounded, evidenced correction. Backend remains frozen.
- Run two fresh, distinct strict FullApply vertical acceptances on the exact J6 BUILD_ID, each with unique DB/runtime/output/cache/ports/run/project/video/checkpoint/correction identity.
- Retain all C5 acceptance: real source authority, current Demo approval, 24 verified chunks, real lease expiry/replacement ownership, affected-only durable correction, measured structural `REVIEW_REQUIRED`, tamper `BLOCKED`, DB-bound decodable media, SHA/size/ffprobe, long path, publications/provenance and zero FK violation.
- No copied old bundle, stale build, force-requeue, grace-zero, direct run/status patch, synthetic/fallback truth or missing-route tolerance.
- Worker ends `TASK_SUBMITTED`; Manager independently validates both DBs/artifacts/manifests/media/build IDs and records `S10-T04C-C5 = TASK_MANAGER_VERIFIED` only when all binary facts are green.

## 8. Final EXIT matrix

Manager runs/records:

1. J1-v4 frozen hashes 13/13.
2. Exact Ruff and mypy S10 production/test sets green.
3. Alembic exactly one head and materialized OpenAPI unique with all eight FullApply routes.
4. Full eight-file S10 backend suite green once on a unique short Windows basetemp; no reuse of global DB/cache.
5. Exact max-warning frontend lint and TSC green.
6. Current build validator 7/7 and current Apply source-manifest hash truth.
7. C6 live UI suite green twice total (worker plus Manager rerun), on fresh isolated environments, desktop+390px mobile, zero skip/retry/vacuous path.
8. Trace/report audit proves real UI submit, progress, Cancel, Retry, Resume, structural compare and Review gate through product responses.
9. If production source changed: two fresh current-build T04C runs pass all strict DB/artifact/media/recovery/structural checks. If unchanged: C5 runs may be retained only after direct hash/build/freeze proof.
10. `git diff --check`, exclusive write-set/hash attribution, zero active worker/owned listener, cleanup of owned processes/temp roots and protected MAIN unchanged.

Exit acceptance is binary. “Passed with skipped action”, empty state, report claim without trace, retained stale build after production change, or unowned process is not green.

## 9. Coordination writes và terminal

Manager may append only:

- `docs/pm/sessions/S10-SESSION_REGISTRY.md`;
- `docs/pm/sprints/S10-SPRINT_REPORT.md`;
- Manager-owned evidence under `output/s10/c6/manager/**`.

Do not edit Codex review/prompt/handoff/roadmap, worker implementation, TASK/LOG/REPORT or approval state as Manager.

When all applicable gates are green, append exactly:

`S10-C6 = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

Then stop all S10 workers, free only owned ports/PIDs, report a compact evidence matrix and wait for Codex. Không tự ghi `APPROVED`, `CLOSED`, không commit/push/merge và không mở S11/S12/S13.

Nếu không green, terminal phải là exact blocker (`BLOCKED_MODEL_ROUTE`, `BLOCKED_J1_DRIFT`, `BLOCKED_SCOPE_EXPANSION`, `BLOCKED_ENVIRONMENT`, hoặc finding cụ thể), kèm owner/evidence/required Codex decision. Không tuyên bố hoàn tất bằng kế hoạch suông.

