Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, coordination write hoặc worker resume. Sau đó báo `RULES_LOADED` kèm absolute path, logical line count, SHA-256, toàn bộ section rules đã nạp, branch/HEAD/dirty state thực tế. Nếu thiếu file, chưa đọc đủ hoặc có mâu thuẫn chưa giải quyết, dừng `BLOCKED_RULES`; không điều phối bằng trí nhớ hoặc report cũ.

Tiếp theo đọc TOÀN BỘ `C:\Users\Admin\MotionForge2D\AGENTS.md`, mọi nested `AGENTS.md` áp dụng; `docs/pm/CODEX_PM_HANDOFF.md`; `docs/pm/ROADMAP.md`; `docs/pm/SESSION_PROTOCOL.md`; `docs/pm/README.md`; `docs/pm/TARGET_PROFILE_2D_SOURCE_LOCKED.md`; `docs/pm/reviews/S10_C3_PM_REVIEW_2026-08-29.md`; `docs/pm/reviews/S10_C4_BLOCKER_PM_DECISION_2026-08-30.md`; prompt gốc `docs/pm/prompts/S10_C4_AUTHORITY_SEMANTICS_EXIT_CORRECTION_MANAGER_2026-08-29.md`; current `docs/pm/sessions/S10-SESSION_REGISTRY.md`; S10 sprint report; và toàn bộ TASK/LOG/REPORT hiện hành của T01A, T01C, T03, T04A, T04C. Báo `WORKSPACE_INSTRUCTIONS_LOADED`. Không chỉ trả kế hoạch: bắt đầu preflight và thực thi ngay.

# MotionForge2D — S10-C4A ownership-correct static unblock and C4 exit

## 1. Authority, current verdict và ranh giới

Bạn là Hermes Manager, không phải Codex Reviewer và không phải production writer. Manager chỉ preflight, resume exact owner, monitor, kiểm tra write-set, chạy join/exit gates và append coordination evidence; Manager không tự sửa code/test/UI/migration/config.

Codex decision hiện hành:

- `S10-C4 = CONTINUATION_AUTHORIZED / NOT_APPROVED`.
- C4 đã Manager-verify J1 T01C-C6, J2 T03-C4 và J3 T04A-C4.
- T01C-C7 static đạt exact nine-file mypy zero, targeted 32 x 2 và full S10 197, nhưng J4 bị đúng một `F841` tại `tests/test_s10_full_apply_domain.py:172`.
- T01C đã dừng đúng ownership. Codex không waiver Ruff và cấp quyền tối thiểu resume S10-T01A để xóa đúng dòng thừa, rồi mới tiếp tục T04C-C3.
- Đây là continuation bên trong C4, không phải C5, không phải S10 approval và không mở S11/S12/S13.

MAIN `C:\Users\Admin\MotionForge2D` là protected read-only đối với worker. Implementation authority duy nhất là `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`. Không commit/push/merge/reset/checkout/restore/clean/stash/delete hoặc ghi đè foreign dirty state.

## 2. Model policy — user-authorized OCG DeepSeek v4 Flash max

Mọi worker resume trong prompt này, kể cả exact owner cũ, phải dùng exact model ID `ocg/deepseek-v4-flash`, reasoning `max`, fallback `OFF`, `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`.

Working launch form phải được preflight bằng harmless route probe và ghi evidence trước dispatch:

`hermes --resume <exact-session-id> -m ocg/deepseek-v4-flash --yolo`

Effective route phải được chứng minh là OCG/9Router `ocg/deepseek-v4-flash`; cấm raw alias `deepseek-v4-flash`, `meta`, `muse`, `openrouter`, `cmc` hoặc model/fallback khác. Không log secret/token. Sai hoặc unavailable route => `BLOCKED_MODEL_ROUTE`, không fallback.

Lỗi kết nối 502/503/504/524/disconnect/network timeout: báo ngay, giữ `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume đúng session/prompt/model; lặp theo canonical rules, không retry dồn. Lỗi model/auth/quota xác định thì dừng blocker tương ứng.

## 3. Stable preflight và protected guards

Trước mọi resume:

1. Rediscover MAIN/integration branch, HEAD, `git status --porcelain`, diff attribution, process/listener ownership và latest registry/log mtime; không kế thừa snapshot.
2. `MOTIONFORGE_DATABASE_URL` phải `UNSET`; mọi test/runtime dùng fresh isolated DB, cache, basetemp, runtime/output roots và owned ports.
3. Chứng minh zero active S10 writer. Không kill process nếu thiếu exact PID + command line + launch-record ownership.
4. Re-hash frozen J1-v4 13/13 và EOL 12 LF + composite CRLF. Drift => dừng `BLOCKED_J1_DRIFT`.
5. Hash/inventory current dirty tree, C4 evidence và exact line 172 before write. Không sửa/rewrite C0-C4 history.
6. Verify exact nine-file mypy is currently literal zero and exact Ruff command currently has only the known F841. Bất kỳ lỗi mới nào => dừng, phân loại owner và báo Codex trước dispatch.

## 4. Dependency DAG và parallel policy

Serialized DAG duy nhất:

`PREP -> S10-T01A-C4A-STATIC -> J4 -> S10-T04C-C3 -> EXIT`

Không parallel writer. Read-only hashes/probes có thể song song khi tài nguyên độc lập. T04C chỉ mở sau J4 exact green. Không tạo session mới; mọi correction resume đúng exact owner.

## 5. Task map, owner và exclusive write-set

### S10-T01A-C4A-STATIC — remove one dead assignment

- **Exact owner/session:** S10-T01A / `20260827_234001_9d7f39`.
- **Outcome:** xóa đúng statement `sf = _session_factory(db)` hiện ở `tests/test_s10_full_apply_domain.py:172`, vì test chỉ dùng `Sf2`.
- **Depends on:** PREP green; zero writer; known one-error Ruff baseline.
- **Exclusive implementation write:** chỉ `tests/test_s10_full_apply_domain.py`, đúng một line deletion. Không rename `Sf2`, không reformat/rewrite test, không đổi assertion/fixture/behavior.
- **Coordination/evidence writes:** append-only `docs/pm/sessions/S10-T01A-durable-domain/{TASK,LOG,REPORT}.md`; `output/s10/c4a/t01a-static-unblock/**`; Manager có thể append Session Registry.
- **Forbidden:** toàn bộ `app/**`, migration/model/schema, mọi test khác, frontend, S09/J1, S11/S12/S13, MAIN và user data.
- **Binary acceptance:** diff của test file chỉ xóa đúng line; focused `tests/test_s10_full_apply_domain.py` x2 fresh roots green; exact Ruff set zero; exact nine-file mypy zero; full `tests/test_s10*.py` green; `git diff --check` zero; no foreign status drift.
- **Terminal:** worker ghi `TASK_SUBMITTED`, không `APPROVED/CLOSED`.

### J4 — Manager static join gate

Sau worker exit, Manager độc lập re-run, không chỉ đọc report:

- Ruff `--select F` trên chín production files: `app/workflow/s10_full_apply_jobs.py`, `app/services/s10_structural_compare.py`, `app/services/s10_recompute.py`, `app/services/s10_multi_role_apply.py`, `app/services/s10_full_apply.py`, `app/services/s10_chunk_plan.py`, `app/schemas/s10_full_apply.py`, `app/persistence/s10_full_apply.py`, `app/api/routes/s10_full_apply.py`; cộng đúng tám tests: `tests/test_s10_chunk_plan.py`, `tests/test_s10_full_apply_api.py`, `tests/test_s10_full_apply_domain.py`, `tests/test_s10_full_apply_migration.py`, `tests/test_s10_full_apply_workflow.py`, `tests/test_s10_multi_role_apply.py`, `tests/test_s10_partial_recompute.py`, `tests/test_s10_structural_compare.py`. Acceptance: zero error, zero missing filename, không waiver/config weakening.
- Exact nine-file mypy phải in literal `Success: no issues found in 9 source files`, không disable/skip/ignore/config weakening.
- Focused T01A x2 fresh roots; full S10 green; alembic exactly one head `a10b11c12d3e`; OpenAPI routes/operation IDs unchanged; J1-v4 retained; diff/status/write-set audit green.

Chỉ khi mọi mục green mới ghi `J4 = MANAGER_VERIFIED` và mở T04C. Nếu fail, resume đúng owner của lỗi; không cho T01A sửa file ngoài exclusive scope.

### S10-T04C-C3 — strict two-run production acceptance

- **Exact owner/session:** S10-T04C / `20260828_023122_76b87e`.
- **Outcome:** hai fresh C4 vertical runs chứng minh current production authority/fence, actual durable correction, actual measured structural compare và restart/reuse contract.
- **Depends on:** J4 exact green.
- **Exclusive implementation write:** `frontend/e2e/s10-full-apply.spec.ts`, bounded `frontend/e2e/s10-full-apply-global-setup.ts`, `frontend/playwright.s10.config.ts`, canonical `tests/fixtures/s10_full_apply/**` only when fixture enlargement is necessary; append exact T04C TASK/LOG/REPORT; new evidence only under `output/s10/c4/t04c-c3/**`.
- **Forbidden:** all `app/**`, production frontend, migration/model/schema/reconciler, direct edits to historical C0-C3 evidence, MAIN, S11/S12/S13. T04C cannot patch a production defect.
- **Binary harness rules:** create all authority through real product APIs/handlers; DB is read-only probe only, with zero direct `INSERT/UPDATE/DELETE`, zero manifest patch, `stage_c4.py`, `_force_requeue.py`, lease expiry mutation or direct reconciler call. Submit/confirm/apply a real typed durable correction and recompute by persisted ID.
- **Restart proof:** observe real `0 < verified < total`; stop exact owned backend PID; prove old owner gone; launch a distinct replacement PID; production lease/reconciler/resume must recover same DB/run without grace=0 or direct requeue.
- **Two-run proof:** distinct fresh nested roots, DBs, job/run/correction IDs, same current validated build manifest; each must exercise final/staging path longer than 260 characters without shortening around the contract.
- **Media/lineage proof:** every chunk/publication/recompute artifact ffprobe-decodable; exact SHA/size/timebase/frame range matches DB; zero `.bin/.partial/.staging`; affected correction attempt exactly +1 with new media/publication; unaffected exact artifact IDs/SHA/size/frame metadata and zero render calls; replay dedupes.
- **Structural proof:** empty/caller-truth-free structural request; `REVIEW_REQUIRED` only from non-empty independently measured source/rendered authority; negative perturbation returns `BLOCKED`; read-only DB probe proves source/segment/motion/contact/route rows exist.
- **Evidence:** branch/HEAD/status/build/fixture hashes; PID/listener timeline; API bodies/statuses; immutable job manifest/fingerprint; correction authority/result; before-checkpoint/after-resume/before-after-correction DB probes; adapter requests; ffprobe/SHA/size; structural methods/values; screenshots/traces; cleanup. Owned ports free, unrelated process preserved.
- **Terminal:** worker writes `TASK_SUBMITTED`; Manager independently verifies before exit.

## 6. Correction routing if T04C exposes an in-scope C4 defect

Manager never patches it. Resume exactly:

- authority/immutable manifest/job fence/path problem -> T01C `20260828_003035_859fe5`, original C4 T01C write-set only;
- recompute/correction binding/affected-only problem -> T03 `20260828_011920_b79bd6`, original C4 T03 write-set only;
- structural measurement problem -> T04A `20260828_014304_25d94a`, original C4 T04A write-set only;
- harness/fixture/evidence problem -> T04C `20260828_023122_76b87e`.

Every correction uses exact `ocg/deepseek-v4-flash` max/OFF route and reruns its focused gate plus downstream join. A new product/domain need outside the six frozen C4 finding groups => `BLOCKED_SCOPE_EXPANSION` and Codex decision; không tự mở scope hoặc tạo replacement owner.

## 7. Final exit verification

At a stable no-writer checkpoint, Manager records raw commands/exit codes under `output/s10/c4/exit/**` and must prove:

1. J1-v4 direct 13/13, correct EOL.
2. Full `tests/test_s10*.py` twice on distinct fresh isolated nested roots, zero fail/skip/xpass; at least one final/staging artifact path observed >260 characters.
3. Exact Ruff set zero; exact nine-file mypy zero; `git diff --check` zero.
4. Alembic one head `a10b11c12d3e`; migration/domain/job-reconciler regressions green; DB env UNSET.
5. Materialized OpenAPI retains S09/S10 routes, zero duplicate operation IDs.
6. Frontend TSC, scoped Apply ESLint, fresh current production build and build validator 7/7.
7. Two new C4 run bundles pass every T04C binary rule through read-only DB/file/media inspection.
8. Source sweep zero for synthetic production staging, S10 input-change bypass, fallback checkpoint/zero hash/gen-1/frame100 authority, correction-ID perturb, fixed structural arrays, rendered-cut mirroring, missing-evidence pass and direct DB/requeue harness helpers.
9. Exact session/model/write-set ledger; no Manager implementation write, no MAIN/S11/S12/S13/J1 drift; all owned processes cleaned and unrelated processes untouched.
10. Append Session Registry and `docs/pm/sprints/S10-SPRINT_REPORT.md` truthfully after writers exit; supersede the stale C3 “ALL 9 GATES GREEN” claim. Do not rewrite history.

## 8. Heartbeat, liveness và report

Heartbeat at least every 20 minutes while work is active and immediately on gate/blocker change. Audit after 8 minutes without progress: exact process tree, CPU/log growth, waiting input, route/connection status and owned ports. Maintain registry row with Task ID, exact session, model, status, write-set, heartbeat and recovery reason.

Final report must list actual branch/HEAD/dirty attribution; task/session/model map; every changed path; command/test counts and exit codes; C4 run IDs/build/hash/DB/media evidence; findings/corrections; process cleanup; blockers/risks; evidence paths; and recommended Codex decision. Do not claim Manager approval.

## 9. Terminal condition

If any binary gate is red, keep the task active or stop at the exact authorized blocker and route it correctly; narrative cannot convert red to green. When and only when all C4 gates are truly green, stop exactly at:

`S10-C4 = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

Không `APPROVED/CLOSED`, không commit/push/merge, không mở S11/S12/S13. Bắt đầu ngay: full rules/instructions load -> stable preflight -> resume exact T01A owner for one-line correction -> independently verify J4 -> resume exact T04C owner -> strict two-run evidence -> full exit gates -> report and stop for Codex review.

