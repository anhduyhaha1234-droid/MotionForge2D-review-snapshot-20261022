Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, coordination write hoặc worker resume. Sau đó báo `RULES_LOADED` kèm absolute path, logical line count, SHA-256, toàn bộ section rules đã nạp, branch/HEAD/dirty state thực tế. Nếu thiếu file, chưa đọc đủ hoặc có mâu thuẫn chưa giải quyết, dừng `BLOCKED_RULES`; không điều phối bằng trí nhớ hoặc report cũ.

Tiếp theo đọc TOÀN BỘ `C:\Users\Admin\MotionForge2D\AGENTS.md`, mọi nested `AGENTS.md` áp dụng; local Next.js docs mà nested AGENTS yêu cầu trước khi worker sửa frontend; `docs/pm/CODEX_PM_HANDOFF.md`; `docs/pm/ROADMAP.md`; `docs/pm/SESSION_PROTOCOL.md`; `docs/pm/README.md`; `docs/pm/TARGET_PROFILE_2D_SOURCE_LOCKED.md`; `docs/pm/reviews/S10_C6_BLOCKER_PM_DECISION_2026-08-31.md`; review C5 `docs/pm/reviews/S10_C5_PM_REVIEW_2026-08-30.md`; prompt C6 `docs/pm/prompts/S10_C6_REAL_APPLY_UI_ACCEPTANCE_MANAGER_2026-08-30.md`; current `docs/pm/sessions/S09-SESSION_REGISTRY.md`; current `docs/pm/sessions/S10-SESSION_REGISTRY.md`; `docs/pm/sprints/S10-SPRINT_REPORT.md`; và TOÀN BỘ TASK/LOG/REPORT hiện hành của S09-T06A, S10-T01C, S10-T04B, S10-T04C. Báo `WORKSPACE_INSTRUCTIONS_LOADED`. Không chỉ trả kế hoạch: bắt đầu preflight và thực thi ngay.

# MotionForge2D — S10-C6A server-derived Full Apply authority correction

## 1. Role, verdict và mục tiêu

Bạn là Hermes Manager, không phải Codex Reviewer và không phải production writer. Manager chỉ preflight, resume exact owner, monitor, kiểm tra write-set, chạy join/exit gates và append coordination evidence; Manager không tự sửa code/test/UI/backend/migration/config.

Codex verdict hiện hành:

- `S10-C6 = CONTINUATION_AUTHORIZED / NOT_APPROVED`.
- C6 T04B-C3 dừng đúng ở `BLOCKED_SCOPE_EXPANSION`.
- Defect không chỉ là thiếu public SLM hash. Full Apply hiện plan và ghi job manifest từ scene/mapping/route/affected-region do client gửi; C5/T04C và C6 probe từng đổi `mesh_warp -> sprite_affine` và tự dựng affected region.
- Codex bác ba shortcut: expose hash đơn thuần; cho checkpoint/timebase hash thay SLM hash; nới equality/waiver.
- Mục tiêu C6A: đóng băng approval authority v2, chuyển Full Apply sang server-derived authority, rồi mới resume bộ live UI acceptance 20-case và hai fresh vertical runs.

MAIN `C:\Users\Admin\MotionForge2D` là protected read-only đối với mọi worker. Implementation authority duy nhất là `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`. Không commit/push/merge/reset/checkout/restore/clean/stash/delete hoặc ghi đè foreign dirty state.

S09 vẫn giữ lịch sử `CODEX_APPROVED/CLOSED`; correction T06A dưới đây chỉ là bounded dependency bridge cho S10, không được đổi ngược verdict/roadmap S09. Không mở S11/S12/S13 production.

## 2. Model policy — bắt buộc OCG DeepSeek v4 Flash max

Mọi worker resume trong prompt này phải dùng exact model ID `ocg/deepseek-v4-flash`, reasoning `max`, fallback `OFF`, `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`.

Working launch form phải được harmless-route probe và ghi evidence trước dispatch:

`hermes --resume <exact-session-id> -m ocg/deepseek-v4-flash --yolo`

Effective route phải được chứng minh là OCG/9Router `ocg/deepseek-v4-flash`. Cấm raw alias `deepseek-v4-flash`, `meta`, `muse`, `openrouter`, `cmc` hoặc model/fallback khác. Không log secret/token. Sai hoặc unavailable route => `BLOCKED_MODEL_ROUTE`, không fallback.

Lỗi 502/503/504/524/disconnect/network timeout: báo ngay, giữ `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume đúng session/prompt/model; lặp theo canonical rules, không retry dồn. Lỗi model/auth/quota xác định thì dừng blocker tương ứng.

## 3. Stable preflight và reproduced baseline

Trước dispatch đầu tiên, Manager phải:

1. Rediscover MAIN/integration branch, HEAD, worktrees, `git status --porcelain`, complete diff attribution, current registry/log mtimes, active Hermes sessions, processes/listeners và exact ownership. Không kế thừa snapshot cũ.
2. Chứng minh zero active S09/S10 writer. Không kill process nếu thiếu exact PID + command line + launch-record ownership.
3. `MOTIONFORGE_DATABASE_URL` phải `UNSET`; mọi test/runtime dùng unique temp SQLite, basetemp, managed artifact/runtime/cache/output roots và owned ports.
4. Re-hash J1-v4 13/13 và EOL contract. Capture current backend/frontend/test/config hashes, Alembic head, OpenAPI, current build ID và dirty baseline. Drift phải được attributed; J1 drift => `BLOCKED_J1_DRIFT`.
5. Reproduce/read-only prove the Codex findings before writing:
   - `FullApplyService.submit` plans from client authority;
   - route stores client authority in job manifest;
   - current OpenAPI requires client authority objects;
   - approval v1 snapshot lacks canonical Full Apply authority and records route alternatives;
   - C5 E2E/C6 probe route downgrade and fabricated affected region;
   - real C6 checkpoint hash, timebase fingerprint and SLM hash differ.
6. Save compact raw evidence under `output/s10/c6a/manager/prep/**`; do not mutate the C6 DB while probing.

If any premise is false on the live tree, stop with exact evidence for Codex instead of implementing a stale design.

## 4. Serialized DAG và write-lock policy

Exact serialized DAG:

`PREP -> S09-T06A-C4-AUTHORITY-BRIDGE -> J6A -> S10-T01C-C8-AUTHORITY -> J6B -> S10-T04B-C3 -> J6-UI -> J6-BUILD -> S10-T04C-C5 -> EXIT`

Không parallel writer. Một owner phải `TASK_SUBMITTED` và Manager phải hoàn tất join gate trước khi resume owner kế. Read-only probes chỉ được song song khi tài nguyên độc lập. Không tạo replacement session.

## 5. S09-T06A-C4-AUTHORITY-BRIDGE — immutable approval v2

- Exact owner/session: S09-T06A / `20260824_120141_312e9e`.
- Resume exact session, không session mới.
- Đây là S10 dependency bridge; không đổi historical S09 close verdict.
- Initial exclusive write scope:
  - `app/services/s09_approval.py`;
  - `app/api/routes/s09_approval.py` chỉ khi API/reapproval response cần bounded additive change;
  - `app/schemas/s09_approval.py`;
  - bounded additive `tests/test_s09_t06_backend_*.py`;
  - append-only `docs/pm/sessions/S09-T06A-immutable-approval-backend/{TASK,LOG,REPORT}.md`;
  - new evidence under `output/s10/c6a/s09-t06a-c4/**`.
- Models/migrations, renderer implementation, structural-lock mutation, frontend, S10 implementation, S11/S12/S13 và MAIN forbidden. Nếu live proof cho thấy migration/model write thật sự bắt buộc, dừng `BLOCKED_SCOPE_EXPANSION`; không tự mở.

### 5.1 Required v2 contract

Tạo additive immutable snapshot schema `s09.approval/v2` với nested `full_apply_authority`. Snapshot và toàn bộ authority phải nằm trong checkpoint content hash. Dùng persisted/canonical source, không dùng payload client làm render truth.

Authority v2 phải pin đủ dữ liệu để server tái tạo một Full Apply plan deterministic mà không cần client gửi scene/mapping:

1. workspace/project/video/config/checkpoint identity và revisions;
2. exact source generation và source managed artifact identity, relative path, SHA-256, size, frame count, fps/timebase;
3. structural lock manifest id, policy version, stored manifest hash và canonical manifest/canonical fields cần thiết; verify hash trước freeze;
4. exact manifest-selected shot order, frame ranges/cuts và segment identities/routes; không dùng toàn bộ route alternatives từ `list_routes_for_video` làm selected route;
5. exact role/layer/occurrence-segment mapping, approved published pack version/asset identities, mapping/config params và dependency hashes;
6. real affected region/geometry derived từ persisted segment/config/segmentation authority. Missing hoặc ambiguous geometry không được hard-code/guess;
7. immutable eligibility/result metadata cho route unsupported hoặc authority incomplete để UI/server có reason rõ ràng. Demo approval có thể vẫn tồn tại, nhưng Full Apply phải fail closed nếu không executable.

Đọc schema/persistence thật trước khi chọn field names. Canonical ordering, finite-number validation, cross-workspace/project/video/generation checks và route enum checks bắt buộc. Không duplicate mutable live joins vào hash mà không freeze value.

### 5.2 Legacy/reapproval semantics

- Không mutate, backfill hoặc upgrade checkpoint `s09.approval/v1` tại chỗ.
- Có deterministic reapproval path tạo checkpoint v2 mới với new content hash/audit identity; replay v2 tương đương phải idempotent, conflict phải zero mutation.
- Full Apply sẽ nhận v1 là `REAPPROVAL_REQUIRED`; T06A tests phải chứng minh old row byte-identical.
- Later mutation của current ReskinConfig/route/SLM pointers không được silently đổi v2 snapshot/hash. Tamper snapshot/manifest/hash phải fail closed.

### 5.3 T06A-C4 binary tests/gates

Tối thiểu phải có adversarial tests cho:

- v2 snapshot đầy đủ từ persisted authority và checkpoint hash verify;
- exact selected route khác route alternatives;
- missing/ambiguous role mapping, affected region, source artifact, pack asset, cross-scope reference và tampered manifest đều fail closed/zero mutation hoặc immutable ineligible reason theo contract đã chọn;
- unsupported route không bị downgrade;
- v1 remains immutable; reapproval creates distinct v2; equivalent v2 replay converges;
- mutate live config/routes/SLM pointer sau approval không đổi stored v2 bytes/hash;
- no migration/schema storage drift.

Run focused/adversarial suite ×2 với fresh basetemp/DB, Ruff exact write-set, mypy exact production files, `git diff --check`, Alembic single head, OpenAPI additive/no duplicate. Worker append actual commands/results/write-set and end `STATUS: TASK_SUBMITTED`; never self-approve.

## 6. J6A — Manager independent approval-authority gate

Manager không tin report suông. Phải:

1. Audit exact diff/write-set and prove zero model/migration/renderer/S10/frontend/J1 drift.
2. Rerun T06A focused/adversarial suite on a third fresh DB.
3. Independently inspect a generated v2 checkpoint and recompute checkpoint + SLM canonical hashes.
4. Prove selected routes/ranges/regions/packs/source come from persisted canonical authority, not route alternatives or fixture constants.
5. Prove v1 reapproval semantics and unsupported-route no-downgrade.
6. Run Ruff/mypy/diff-check/Alembic/OpenAPI and J1 hashes.

Only when green append `J6A = MANAGER_VERIFIED` and continue. Otherwise resume the same T06A owner with exact failing evidence.

## 7. S10-T01C-C8-AUTHORITY — server-derived submit and job manifest

- Exact owner/session: S10-T01C / `20260828_003035_859fe5`.
- Resume exact session only after J6A.
- Exclusive write scope:
  - `app/services/s10_full_apply.py`;
  - `app/api/routes/s10_full_apply.py`;
  - `app/workflow/s10_full_apply_jobs.py` only for consuming/verifying canonical authority, not renderer redesign;
  - `app/schemas/s10_full_apply.py` only if live ownership/schema placement requires it;
  - bounded `tests/test_s10_full_apply_api.py` and `tests/test_s10_full_apply_workflow.py`;
  - append-only T01C TASK/LOG/REPORT;
  - new evidence under `output/s10/c6a/t01c-c8/**`.
- No models/migration, S09 implementation, renderer adapter, structural/recompute semantics, frontend, S11/S12/S13, MAIN or unrelated cleanup.

### 7.1 Minimal public submit contract

`SubmitFullApplyRequest` must no longer require client copies of
`approved_checkpoint`, `structural_lock_manifest`, `scene_manifest` or `mapping`.
Required product input is identity/CAS only: video item, checkpoint id/hash/revision
plus bounded chunk/idempotency controls where justified.

Legacy authority fields may remain optional for compatibility only. If present,
canonical-compare every supplied field to server authority. Any mismatch in
manifest/scene/shot/range/route/mapping/affected-region/pack/source/policy must
return fail closed before creation, with zero run/job/publication. Never prefer
or merge client authority.

### 7.2 Server canonicalization

For submit/retry/resume:

1. load checkpoint server-side and recompute/verify checkpoint hash;
2. require `s09.approval/v2`; v1 => explicit `REAPPROVAL_REQUIRED` with zero mutation;
3. validate workspace/project/video/config/generation and all frozen identities;
4. recompute SLM canonical hash and compare exact v2 pins/persisted immutable row;
5. resolve source and replacement assets using frozen ids/hashes/sizes; no scan/guess;
6. build planner inputs exclusively from canonical v2 authority;
7. preserve exact selected route and affected region; unsupported route => explicit fail closed, no downgrade;
8. generate plan/natural/idempotency keys and `render_authority` job manifest only from canonical server data;
9. on worker start/restart, recompute authority/plan fingerprints and fence any mutation/tamper before render/publication.

Delete or make unreachable every path that treats non-empty client scene/mapping as authority. Comments and names must match behavior; do not call client body “server-side immutable”.

### 7.3 T01C-C8 binary tests/gates

Tests must prove:

- minimal public submit from a v2 checkpoint returns 202/200 and creates the expected deterministic plan/job;
- current OpenAPI no longer requires four authority objects;
- arbitrary client scene/range/mapping/route/region/pack/source/hash cannot alter plan; mismatch returns zero run/job;
- omission of legacy authority fields succeeds;
- v1 requires reapproval; tampered/cross-project/stale/incomplete v2 blocks;
- `mesh_warp`/`part_rig` unsupported path never coerces to `sprite_affine`;
- plan and job-manifest authority fingerprints equal independently recomputed v2 authority;
- retry/resume reuse exact canonical lineage and mutation is fenced;
- existing durable checkpoint, cancel/retry, long-path, media hash and atomic publication tests remain green.

Run targeted suite ×2 fresh, then full `tests/test_s10*.py` once; exact Ruff F* and mypy nine-file literal green; OpenAPI materialized unique/additive; Alembic single head; J1 13/13; diff/write-set clean. Worker ends `TASK_SUBMITTED`.

## 8. J6B — Manager independent Full Apply authority gate

Manager must rerun on a new fresh DB and independently inspect DB/job manifest:

1. minimal submit contains no client authority but produces canonical plan/job;
2. legacy tamper matrix creates zero run/job and cannot change fingerprints;
3. v1 reapproval-required, v2 exact hash/source/SLM/pack/segment/route/region binding;
4. unsupported route no downgrade;
5. targeted tests, full S10 suite, Ruff, mypy, OpenAPI, Alembic, J1, diff/write-set all green;
6. no process/listener leak.

Only then append `J6B = MANAGER_VERIFIED` and resume T04B. Failure goes back to exact T01C owner; no Manager product patch.

## 9. Resume S10-T04B-C3 — real Apply UI on minimal contract

- Exact owner/session: `20260828_020206_b1f8af`.
- Continue the existing C6 task/suite; do not replace session or discard its 20-case work.
- Writes remain bounded to original T04B C6 scope:
  - `frontend/src/app/(app)/apply/**`;
  - `frontend/src/features/apply/**`;
  - bounded `frontend/src/lib/api.ts` for the corrected public contract;
  - existing/new T04B-owned UI spec/config/helpers;
  - T04B TASK/LOG/REPORT append;
  - new evidence under `output/s10/c6a/t04b-c3/**`.

Required correction:

- stop using `timebase_fingerprint` as SLM hash;
- stop deriving scene/mapping/routes/region from approval snapshot or fixture;
- submit the minimal public identity/CAS contract;
- use v2 eligibility/reason truth to enable/disable Apply;
- show `REAPPROVAL_REQUIRED`, unsupported route, stale/tampered/incomplete authority and backend action errors truthfully;
- no hidden DB probe, route coercion, hard-coded generation/frame/region or mocked response.

Retain and execute all ten scenarios from prior C6 prompt on desktop + 390x844 = 20 tests, zero skip/vacuous branch. Apply, Cancel, Retry, Resume, progress, compare and Review must be real clicks/public responses. Run exact max-warning lint, TSC, suite ×2 total counting worker+Manager, diff/write-set. Worker ends `TASK_SUBMITTED`.

## 10. J6-UI and mandatory J6-BUILD

Production backend and frontend both change in C6A, so current C5 build/runs cannot be exit evidence. J6-BUILD is mandatory, not conditional.

Manager J6-UI:

1. independent fresh isolated run of all 20 live UI cases against real product services;
2. inspect trace/request evidence, not only Playwright summary;
3. exact lint `--max-warnings 0`, TSC, write-set/hash attribution;
4. prove no DB authority probe, client mapping construction or route downgrade remains in T04B test/product paths.

Manager J6-BUILD:

1. build fresh Next production build; record new BUILD_ID and source manifest;
2. `node output/s10/run-s10.js --verify-build-only` 7/7;
3. direct Apply input hash-to-manifest proof; required production fallback origin present, forbidden QA origins absent;
4. rerun focused live UI smoke on exact new build;
5. backend/J1/Alembic/OpenAPI hashes match J6B-approved state.

## 11. S10-T04C-C5 — two fresh current-build vertical runs

- Exact owner/session: `20260828_023122_76b87e`.
- Resume exact owner after J6-BUILD.
- Existing T04C E2E/config and helpers may be corrected only within their original scope; TASK/LOG/REPORT append and new evidence under `output/s10/c6a/t04c-c5/**`.
- Backend/approval implementation frozen after J6B/J6-BUILD.

Mandatory acceptance corrections:

1. Remove direct DB extraction of SLM hash for submit.
2. Remove client construction of scene/mapping/affected region and every route coercion, including `mesh_warp -> sprite_affine`.
3. Create/approve a real v2 checkpoint through product/public contracts after bounded fixture seeding where no creation API exists; submit Full Apply through UI/public minimal API.
4. Positive fixtures must use a truly executable selected route. Negative fixture must prove unsupported route blocks with no downgrade.
5. Add client-tamper negative request using optional legacy fields and prove zero run/job.
6. Run two fresh, distinct vertical acceptances on exact J6 BUILD_ID with unique DB/runtime/output/cache/ports/run/project/video/checkpoint/correction identities.
7. Retain all prior strict truth: real source and published assets, 24 verified chunks or plan-correct current count, exact frame/timebase/shot order, owned restart/lease recovery, durable affected-only correction, measured structural `REVIEW_REQUIRED`, tamper `BLOCKED`, DB-bound decodable media, SHA/size/ffprobe, long path, publication/provenance, FK clean and owned cleanup.

No copied bundle, direct status/run/job patch, force requeue, grace-zero, stale build, synthetic/fallback authority, fixture route downgrade or missing-route tolerance. Worker ends `TASK_SUBMITTED`; Manager independently validates both bundles before marking task Manager-verified.

## 12. Final EXIT matrix

Manager runs and records:

1. J1-v4 13/13 + EOL unchanged.
2. S09 T06A v2 focused/adversarial suite green; v1 immutable/reapproval proof.
3. Full S10 backend suite green on unique basetemp; targeted authority tamper matrix green.
4. Exact Ruff and nine-file mypy literal green.
5. Alembic exactly one head; materialized OpenAPI unique/additive and minimal submit contract verified.
6. Exact max-warning frontend lint and TSC green.
7. Fresh current build validator 7/7 and source-manifest truth.
8. Live UI 20/20 twice total, desktop+mobile, zero skip/retry/vacuous branch; trace proves all required clicks/responses.
9. Two fresh T04C current-build vertical bundles with server-derived v2 authority and no DB/client fabrication.
10. Independent DB/artifact/media/recovery/structural/tamper/unsupported-route checks green.
11. Source sweeps: zero route downgrade, fixed affected region, hard-coded generation/frame/hash, client-authority planner path, DB submit probe and synthetic/fallback authority.
12. `git diff --check`, exclusive write-set/hash attribution, zero active writer/listener and exact owned cleanup.

Exit is binary. Green tests built on fabricated authority, route downgrade, v1 checkpoint, stale build, unverified report, skipped action or unowned process are not acceptance.

## 13. Coordination writes và terminal

Manager may append only:

- `docs/pm/sessions/S10-SESSION_REGISTRY.md`;
- `docs/pm/sprints/S10-SPRINT_REPORT.md`;
- Manager-owned evidence under `output/s10/c6a/manager/**`.

Manager không edit Codex review/prompt/handoff/roadmap, production/test code, worker TASK/LOG/REPORT hoặc approval state.

Nếu all applicable gates green, append exactly:

`S10-C6A = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

Sau đó stop mọi S09/S10 worker, free only owned ports/PIDs, báo compact evidence matrix và chờ Codex. Không tự ghi `APPROVED/CLOSED`, không commit/push/merge và không mở S11/S12/S13.

Nếu không green, terminal phải là exact blocker (`BLOCKED_MODEL_ROUTE`, `BLOCKED_J1_DRIFT`, `BLOCKED_SCOPE_EXPANSION`, `BLOCKED_ENVIRONMENT`, hoặc finding cụ thể), kèm owner/evidence/required Codex decision. Không tuyên bố hoàn tất bằng kế hoạch suông.
