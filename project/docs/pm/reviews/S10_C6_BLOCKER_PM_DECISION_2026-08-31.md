# MotionForge2D — S10-C6 blocker PM decision

- Review time: 2026-08-31 10:01 +07
- Reviewer: Codex Project PM/BA/Reviewer
- Integration authority: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Integration branch/HEAD: `codex/s08-integration` / `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`
- MAIN HEAD: `f0ee4bd11f83fb6fed8c9a8f3924e85b903c3d3b`
- Current build retained for diagnosis: `rbYCsFU8q82gvOvcRhJSA`

## Verdict

`S10-C6 = CONTINUATION_AUTHORIZED / NOT_APPROVED`

Hermes dừng đúng tại `BLOCKED_SCOPE_EXPANSION / PENDING_CODEX_DECISION`.
Blocker không chỉ là thiếu một public `manifest_hash`; review độc lập phát hiện
Full Apply hiện vẫn để client cung cấp phần authority quyết định plan, route,
shot/range và affected region. Vì vậy:

- không expose riêng `StructuralLockManifest.manifest_hash` rồi tiếp tục tin
  scene/mapping từ client;
- không cho checkpoint hash hoặc timebase fingerprint thay thế manifest hash;
- không nới equality, không downgrade route và không waiver;
- phải tạo immutable approval authority v2 và chuyển Full Apply sang
  server-derived authority trước khi tiếp tục C6 UI acceptance.

Phần kết luận “backend/authority green” trong
`S10_C5_PM_REVIEW_2026-08-30.md` bị supersede bởi review này. Các gate C5 khác
chỉ được giữ làm baseline/provisional evidence và phải được re-run khi production
source đổi.

## Evidence độc lập

### F1 — P0: Full Apply plan và job manifest vẫn client-authoritative

`app/services/s10_full_apply.py:129-185` chỉ kiểm tra client manifest hash/policy
nếu client gửi string và chỉ yêu cầu scene/mapping không rỗng. Nó không canonicalize
hoặc so scene, shot, range, route, mapping hay affected region với snapshot/persisted
authority. Sau đó `FullApplyService.submit` tại `:238-260` gọi
`plan_full_apply(...)` bằng nguyên các object client gửi.

`app/api/routes/s10_full_apply.py:380-398` tiếp tục ghi nguyên
`body.approved_checkpoint`, `body.structural_lock_manifest`, `body.scene_manifest`,
`body.mapping` và `body.compatibility_policy` vào `render_authority`, dù comment gọi
đó là immutable server-side authority.

OpenAPI hiện hành xác nhận `SubmitFullApplyRequest` bắt buộc tám field, trong đó
bốn authority payload là `approved_checkpoint`, `structural_lock_manifest`,
`scene_manifest`, `mapping`. `CheckpointOut` không có `manifest_hash`, nhưng việc
thêm field đó một mình không đóng lỗ hổng client-authoritative.

### F2 — P0: C5 vertical acceptance đã dùng authority tự dựng và route downgrade

`frontend/e2e/s10-full-apply.spec.ts:657-686` đọc DB trực tiếp để lấy SLM hash,
sau đó dựng shot từ fixture, đổi `mesh_warp` thành `sprite_affine` và gắn cố định
`affected_region: [0.10, 0.10, 0.40, 0.40]`. Worker production tại
`app/workflow/s10_full_apply_jobs.py:89-91` tuyên bố rõ route unsupported phải
fail closed và không bao giờ downgrade.

Probe C6 run3 lặp lại bypass này: `probe_run3.py:73-84` đổi route và tự tạo vùng
ảnh hưởng; `:104-119` hard-code SLM hash, generation và frame count. Vì vậy các
green vertical run trước chứng minh media/job plumbing, nhưng không chứng minh
immutable render authority.

### F3 — P0: approval snapshot v1 không đủ để server dựng Full Apply authority

`app/services/s09_approval.py:395-470` hash-verify SLM nhưng snapshot v1 chỉ lưu
policy, SLM id và toàn bộ `list_routes_for_video` evidence. Nó không đóng băng
SLM hash/canonical manifest, exact manifest-selected route, source artifact
authority, role/layer-to-pack mapping, config params hoặc affected region.

Read-only DB probe trên fresh C6 run3:

- checkpoint `efa685d6-1fbf-496e-a617-a78ac29fb473`;
- checkpoint hash `885f14b5...`, timebase fingerprint `1db7d4ad...`, SLM hash
  `bfb41c7b...` là ba giá trị khác nhau;
- snapshot keys chỉ là `compatibility_policy`, `correction_history_refs`,
  `demo_artifact_refs`, `note`, `overrides`, `schema`, `warnings_accepted`;
- SLM có hai exact segments: frames 0-49 `sprite_affine`, frames 50-99
  `mesh_warp`;
- snapshot route evidence lại có sáu rows: ba route alternatives cho mỗi segment.

Không thể suy ra deterministic selected route bằng cách lấy
`renderer_routes_per_segment`; cần snapshot authority mới.

### F4 — P1: Apply UI hiện không thể submit checkpoint thật

`frontend/src/features/apply/ApplyCard.tsx:97-111` dùng
`timebase_fingerprint` làm manifest hash và tìm scene/mapping ở snapshot top
level. Snapshot thật không có các key đó, nên selection null và Apply không bao
giờ enable; nếu tự dựng payload thì server trả 422 hoặc nhận authority sai.

T04B-C3 đã tạo suite 20 tests = 10 scenarios × desktop/mobile, zero skip và
static gates green. Suite nên được giữ, nhưng chưa thể hoàn thành trước correction
authority.

## Quyết định kiến trúc bắt buộc

1. S09 approval tạo additive immutable `s09.approval/v2` với
   `full_apply_authority` canonical, hash-covered. Nó phải pin đủ source/SLM,
   exact manifest-selected segments/routes, frame/timebase/shot order, role/layer
   mapping, published pack/version/assets, config params, affected region và
   dependency evidence cần cho Full Apply. Không lấy route alternatives làm
   selected route và không hard-code missing geometry.
2. Checkpoint v1 không mutate hoặc upgrade tại chỗ. Full Apply trả fail-closed
   `REAPPROVAL_REQUIRED` cho v1; reapproval tạo checkpoint v2 mới, có audit và
   idempotency rõ ràng.
3. `SubmitFullApplyRequest` chỉ cần identity/CAS và bounded chunk controls.
   Authority payload cũ có thể giữ optional để compatibility, nhưng nếu hiện
   diện phải canonical-compare và mismatch phải bị từ chối trước zero run/job.
4. Service, planner input và job manifest chỉ dùng authority do server resolve từ
   checkpoint v2 rồi re-hash/cross-check với persisted immutable rows. Client
   không được chọn shot/range/route/mapping/region/pack/source.
5. Route unsupported/ambiguous/missing authority phải có explicit fail-closed
   reason. Không downgrade `mesh_warp`/`part_rig` sang route khác. Demo approval
   có thể tồn tại, nhưng Full Apply eligibility phải phản ánh đúng capability.
6. Apply UI gửi minimal public contract và hiển thị reason thật; không derive
   authority bằng fixture, DB probe hoặc snapshot guessing.

## Authorized serialized DAG

`PREP -> S09-T06A-C4-AUTHORITY-BRIDGE -> J6A -> S10-T01C-C8-AUTHORITY -> J6B -> S10-T04B-C3 -> J6-UI -> J6-BUILD -> S10-T04C-C5 -> EXIT`

- S09 exact owner: `20260824_120141_312e9e`.
- S10-T01C exact owner: `20260828_003035_859fe5`.
- S10-T04B exact owner: `20260828_020206_b1f8af`.
- S10-T04C exact owner: `20260828_023122_76b87e`.
- Every resume: exact `ocg/deepseek-v4-flash`, reasoning max, fallback OFF,
  TTFB 900.
- One writer at a time. MAIN protected. No commit/push/merge.

S09 remains historically `CODEX_APPROVED/CLOSED`; the T06A continuation is a
bounded S10 dependency bridge and does not rewrite old S09 approval history.
S10 remains not approved. S11-T02..T06 and production S13 remain blocked.

## Required exit proof

- v2 approval hash immutability and reapproval behavior;
- minimal public submit succeeds from server authority;
- client tamper of manifest/scene/range/route/mapping/region/pack/source cannot
  alter a plan and creates zero run/job;
- unsupported route blocks with no downgrade;
- job manifest/plan fingerprints match canonical checkpoint v2 authority;
- C6 live UI suite executes all 20 cases, zero skip/vacuous branch, on fresh
  isolated product services;
- fresh current build plus two T04C vertical runs use public submit, no DB
  authority probe/fabrication, and retain all media/recovery/structural gates;
- full S09 targeted and S10 regression/static/OpenAPI/Alembic/J1/build/process
  gates green with exact write-set attribution.

## Next prompt

`docs/pm/prompts/S10_C6A_SERVER_DERIVED_APPLY_AUTHORITY_MANAGER_2026-08-31.md`
