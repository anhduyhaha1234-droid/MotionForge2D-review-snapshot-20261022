Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, coordination write hoặc worker resume. Sau đó báo `RULES_LOADED` kèm absolute path, logical line count, SHA-256, toàn bộ section rules đã nạp, branch/HEAD/dirty state thực tế. Nếu thiếu file, chưa đọc đủ hoặc có mâu thuẫn chưa giải quyết, dừng `BLOCKED_RULES`; không điều phối bằng trí nhớ hoặc report cũ.

Tiếp theo đọc TOÀN BỘ `C:\Users\Admin\MotionForge2D\AGENTS.md`, mọi nested `AGENTS.md` áp dụng; `docs/pm/CODEX_PM_HANDOFF.md`; `docs/pm/ROADMAP.md`; `docs/pm/SESSION_PROTOCOL.md`; `docs/pm/README.md`; `docs/pm/TARGET_PROFILE_2D_SOURCE_LOCKED.md`; `docs/pm/reviews/S10_C4_FINAL_PM_REVIEW_2026-08-30.md`; `docs/pm/reviews/S10_C4_BLOCKER_PM_DECISION_2026-08-30.md`; prompt C4A `docs/pm/prompts/S10_C4A_T01A_STATIC_UNBLOCK_AND_EXIT_MANAGER_2026-08-30.md`; current `docs/pm/sessions/S10-SESSION_REGISTRY.md`; `docs/pm/sprints/S10-SPRINT_REPORT.md`; và toàn bộ TASK/LOG/REPORT hiện hành của T04B và T04C. Báo `WORKSPACE_INSTRUCTIONS_LOADED`. Không chỉ trả kế hoạch: bắt đầu preflight và thực thi ngay.

# MotionForge2D — S10-C5 Apply lint correction and current-build final exit

## 1. Authority, verdict và ranh giới

Bạn là Hermes Manager, không phải Codex Reviewer và không phải production writer. Manager chỉ preflight, resume exact owner, monitor, kiểm tra write-set, chạy join/exit gates và append coordination evidence; Manager không tự sửa code/test/UI/migration/config.

Codex verdict hiện hành:

- `S10-C4 = CHANGES_REQUESTED / NOT_APPROVED`.
- Backend C4, authority, correction binding, structural measurement, long-path, restart/reuse, J1-v4, Ruff, mypy, Alembic, OpenAPI và full backend suite đã được Codex kiểm chứng độc lập là green.
- Blocker còn lại là frontend gate trong chính S10: `frontend/src/app/(app)/apply/page.tsx:90` vi phạm `react-hooks/set-state-in-effect`; exact scoped command exit 1. Cùng command có một warning thuộc T04B E2E và ba warning thuộc T04C E2E.
- Đây là bounded S10-C5 correction, không phải approval và không mở S11/S12/S13.

MAIN `C:\Users\Admin\MotionForge2D` là protected read-only đối với worker. Implementation authority duy nhất là `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`. Không commit/push/merge/reset/checkout/restore/clean/stash/delete hoặc ghi đè foreign dirty state.

## 2. Model policy — bắt buộc OCG DeepSeek v4 Flash max

Mọi worker resume trong prompt này phải dùng exact model ID `ocg/deepseek-v4-flash`, reasoning `max`, fallback `OFF`, `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`.

Working launch form phải được harmless-route probe và ghi evidence trước dispatch:

`hermes --resume <exact-session-id> -m ocg/deepseek-v4-flash --yolo`

Effective route phải được chứng minh là OCG/9Router `ocg/deepseek-v4-flash`. Cấm raw alias `deepseek-v4-flash`, `meta`, `muse`, `openrouter`, `cmc` hoặc model/fallback khác. Không log secret/token. Sai hoặc unavailable route => `BLOCKED_MODEL_ROUTE`, không fallback.

Lỗi 502/503/504/524/disconnect/network timeout: báo ngay, giữ `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume đúng session/prompt/model; lặp theo canonical rules, không retry dồn. Lỗi model/auth/quota xác định thì dừng blocker tương ứng.

## 3. Stable preflight và protected guards

Trước mọi resume:

1. Rediscover MAIN/integration branch, HEAD, `git status --porcelain`, diff attribution, process/listener ownership và latest registry/log mtime; không kế thừa snapshot.
2. `MOTIONFORGE_DATABASE_URL` phải `UNSET`; mọi test/runtime dùng fresh isolated DB, cache, basetemp, runtime/output roots và owned ports.
3. Chứng minh zero active S10 writer. Không kill process nếu thiếu exact PID + command line + launch-record ownership.
4. Re-hash frozen J1-v4 13/13 và EOL contract. Drift => dừng `BLOCKED_J1_DRIFT`.
5. Capture SHA-256 current backend S10 production files, migration, eight backend tests, current frontend Apply files, current BUILD_ID and the two accepted C4 run bundles. Backend hashes become the C5 no-write baseline.
6. Re-run the exact frontend lint command before dispatch and record the expected baseline: one error at Apply page line 90 plus four unused-variable warnings. Any additional error/drift => classify exact owner and stop for Codex if outside the frozen scopes below.

## 4. Dependency DAG và parallel policy

Serialized DAG duy nhất:

`PREP -> S10-T04B-C2 -> J5 -> S10-T04C-C4 -> EXIT`

Không parallel writer. Read-only hashes/probes có thể song song khi tài nguyên độc lập. T04C chỉ resume sau J5 exact green. Không tạo replacement session; mỗi correction phải resume exact frozen owner.

## 5. Task map, owners và exclusive write-sets

### S10-T04B-C2 — correct Apply URL/state synchronization and own lint warning

- **Exact owner/session:** S10-T04B / `20260828_020206_b1f8af`.
- **Outcome:** `/apply` giữ đúng backend truth, URL deep-link, reload, local-storage recovery và browser navigation mà không gọi `setState` đồng bộ trong effect, không render loop và không lint suppression.
- **Depends on:** PREP green; exact baseline reproduced.
- **Exclusive implementation writes:**
  - `frontend/src/app/(app)/apply/page.tsx`;
  - `frontend/e2e/s10-apply-ui.spec.ts`;
  - append-only `docs/pm/sessions/S10-T04B-apply-ux/{TASK,LOG,REPORT}.md`;
  - new evidence only under `output/s10/c5/t04b-c2/**`.
- `frontend/src/features/apply/**`, `frontend/src/lib/api.ts`, navigation/project pages and all other frontend files are read-only in this round unless a separately proven blocker requires Codex scope decision.
- **Required behavior:** URL `run_id`/`project` wins on initial deep-link; selected/current run persists across reload; user actions update URL/storage without a replace loop; browser back/forward or changed search params resolve to the displayed/polled run; cancel/retry/resume and structural evidence remain backend-derived.
- **Lint correction:** remove the `react-hooks/set-state-in-effect` violation structurally. Cấm `eslint-disable`, config/rule weakening, async timeout hack, hidden state copy or deletion/weakening of behavior assertions. Resolve the unused `helper` warning by using it in a truthful assertion or removing only a genuinely dead binding.
- **Binary acceptance:** exact T04B lint set with `--max-warnings 0`; TSC; focused Apply UI Playwright including deep-link/reload/back-forward behavior; fresh production build; no hard-coded QA origin; build validator 7/7; diff-check and exclusive write-set audit.
- **Terminal:** worker append correction evidence and `TASK_SUBMITTED`; never `APPROVED/CLOSED`.

### J5 — Manager current-build UI join gate

After T04B exits, Manager independently reruns rather than trusts the report:

1. Từ `frontend/`, chạy `npm exec eslint -- 'src/features/apply/**/*.{ts,tsx}' 'src/app/(app)/apply/page.tsx' 'e2e/s10-apply-ui.spec.ts' --max-warnings 0` hoặc platform-equivalent command chứng minh target đủ ba exact sets. Acceptance là zero error và zero warning; không được bỏ route page.
2. `npm exec tsc -- --noEmit` green.
3. Focused `s10-apply-ui.spec.ts` green against the newly built current product, including URL/reload/navigation assertions.
4. Fresh Next production build green, new BUILD_ID and manifest recorded; `node output/s10/run-s10.js --verify-build-only` passes 7/7 and compiled origin scan contains required fallback 8888 with forbidden 8201/8099 absent.
5. SHA/status audit proves zero backend/migration/J1/S11/S12/S13 drift.

Only then record `J5 = MANAGER_VERIFIED` and resume T04C. If the finding cannot be fixed inside the exact T04B scope, stop `BLOCKED_SCOPE_EXPANSION` for Codex; Manager must not patch it.

### S10-T04C-C4 — warning cleanup and two fresh runs on the corrected build

- **Exact owner/session:** S10-T04C / `20260828_023122_76b87e`.
- **Outcome:** remove the three genuinely unused T04C E2E bindings without weakening assertions, then prove the corrected current frontend BUILD_ID through two fresh strict FullApply vertical runs.
- **Depends on:** J5 exact green.
- **Exclusive implementation writes:**
  - `frontend/e2e/s10-full-apply.spec.ts`;
  - bounded `frontend/e2e/s10-full-apply-global-setup.ts` and `frontend/playwright.s10.config.ts` only if required for truthful current-build execution;
  - append-only `docs/pm/sessions/S10-T04C-prod-acceptance/{TASK,LOG,REPORT}.md`;
  - new evidence only under `output/s10/c5/t04c-c4/**`.
- **Forbidden:** all production frontend, all `app/**`, migration/model/schema/reconciler, backend tests, historical C0-C4 evidence, MAIN, S11/S12/S13. No ESLint suppression or assertion weakening.
- **Exact lint requirement:** full command over features/apply, Apply route page, T04B E2E and T04C E2E passes with `--max-warnings 0`.
- **Two-run requirement:** two distinct fresh nested roots, DBs, ports, PIDs, job/run/correction IDs and evidence directories, both using the exact new J5 BUILD_ID. Do not reuse the old `KIWvay6FvLdiWmVFduSMG` build as current-build proof.
- **Authority rule:** fixture setup may use canonical app persistence/repository helpers for isolated initial authority, but active run/job/manifest/lease/correction truth must flow through product handlers/APIs. DB access after launch is read-only probe only: zero direct `INSERT/UPDATE/DELETE`, manifest patch, staged synthetic truth, direct lease expiry/requeue, grace=0 or direct reconciler call.
- **Restart proof:** observe real `0 < verified < total`; stop exact owned backend PID; prove old owner/listener gone; launch distinct replacement PID; production lease/reconciler resumes the same DB/run after real expiry; cleanup is fail-closed and ownership-scoped.
- **Media/recompute proof:** every chunk/publication/recompute output exists at DB-bound path, SHA/size/timebase/frame range match and ffprobe decodes; at least one final/staging path exceeds 260 characters; zero `.bin/.partial/.staging`; real persisted typed correction affects only the expected chunks with attempt +1/new media, while unaffected IDs/hashes/metadata and render-call count remain unchanged; replay dedupes.
- **Structural proof:** caller sends empty/caller-truth-free request; independently measured non-empty source/rendered authority yields `REVIEW_REQUIRED`; real tamper/negative perturbation yields `BLOCKED`; missing authority fails closed. Read-only DB probes show source/segment/motion/contact/route rows and zero FK violations.
- **Evidence:** branch/HEAD/status/build/fixture hashes; complete PID/listener timeline; API request/response/status; immutable manifest/fingerprint; correction before/after; adapter requests; DB read-only probes; ffprobe/SHA/size; structural methods/values; screenshots/traces; cleanup and port release.
- **Terminal:** worker writes `TASK_SUBMITTED`; Manager independently verifies both bundles before sprint exit.

## 6. Defect routing and frozen backend rule

S10 backend is frozen in C5. T04B/T04C/Manager may not edit it. If current-build acceptance exposes a new backend defect, stop with exact reproduction, file/owner attribution and `BLOCKED_SCOPE_EXPANSION` for Codex. Do not silently resume T01C/T03/T04A without a new Codex decision.

A harness-only defect stays with T04C exact owner. An Apply production/UI defect stays with T04B exact owner and requires J5 plus downstream T04C rerun. Every resume keeps exact `ocg/deepseek-v4-flash`, max, fallback OFF.

## 7. Final exit verification

At a stable no-writer checkpoint, Manager records raw commands and exit codes under `output/s10/c5/exit/**` and proves:

1. Backend/migration/J1 hashes exactly match the C5 preflight baseline; J1-v4 direct 13/13 and EOL contract remain green.
2. Full eight-file S10 backend suite passes on a unique short isolated Windows basetemp. Retained C4 206/206 x2 evidence may be cited, but at least one current-tree final run is required.
3. Exact Ruff set is zero; exact nine-file mypy prints literal zero; `git diff --check` is zero.
4. Alembic exactly one head `a10b11c12d3e`; DB env is UNSET; materialized OpenAPI keeps 261 paths/327 distinct operations or explains only authorized additive drift—no duplicate operation ID and all eight FullApply routes present.
5. TSC green; exact full Apply/UI/E2E ESLint green with `--max-warnings 0`; fresh current build and validator 7/7 green; no forbidden QA origin.
6. Focused Apply UI suite green and both new C5 T04C vertical bundles use the same exact corrected current BUILD_ID while retaining distinct runtime identities.
7. Direct read-only DB/file/media inspection proves both bundles satisfy authority, restart, affected-only recompute, lineage, long-path and structural negative rules.
8. Source sweep remains zero for synthetic production staging, S10 input-change bypass, fallback checkpoint/zero-hash/gen-1/frame100 authority, correction-ID perturb, fixed structural arrays, rendered-cut mirroring, missing-evidence pass and active-truth DB/requeue harness helpers.
9. Exact session/model/write-set ledger proves no Manager implementation write, no backend/MAIN/S11/S12/S13/J1 drift, all owned processes cleaned and unrelated processes untouched.
10. Append, never rewrite, `docs/pm/sessions/S10-SESSION_REGISTRY.md` and `docs/pm/sprints/S10-SPRINT_REPORT.md` with C5 truth. Explicitly supersede the C4 claim that frontend exit was green while the route page was omitted from lint.

## 8. Heartbeat, liveness và report

Heartbeat at least every 20 minutes while work is active and immediately on gate/blocker change. Audit after 8 minutes without progress: exact process tree, CPU/log growth, waiting input, route/connection status and owned ports. Maintain registry rows with Task ID, exact session, model, status, write-set, heartbeat and recovery reason.

Final report must list actual branch/HEAD/dirty attribution; task/session/model map; every changed path; exact lint/test/build counts and exit codes; new BUILD_ID; both C5 run IDs/DB/job/correction IDs; evidence paths; process cleanup; blockers/risks and recommended Codex decision. Manager does not self-approve.

## 9. Terminal condition

If any binary gate is red, keep the task active or stop at the exact authorized blocker; narrative cannot convert red to green. When and only when every C5 gate is truly green, stop exactly at:

`S10-C5 = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

Không `APPROVED/CLOSED`, không commit/push/merge, không mở S11/S12/S13. Bắt đầu ngay: full rules/instructions load -> stable preflight -> resume exact T04B owner -> independently verify J5/new build -> resume exact T04C owner -> two current-build vertical runs -> full exit gates -> report and stop for Codex review.
