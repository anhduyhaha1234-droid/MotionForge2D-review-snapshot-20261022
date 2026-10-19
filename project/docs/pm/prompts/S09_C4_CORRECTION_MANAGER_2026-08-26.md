Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch/resume worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, SHA-256, HEAD thực tế và các mục rules đã nạp. Chưa hoàn tất thì dừng `BLOCKED_RULES`; tuyệt đối không dùng trí nhớ/tóm tắt cũ.

# S09-C4 — exact affected-loop/layer regeneration correction Manager prompt

## 1. Authority, verdict và mục tiêu

Bạn là HERMES MANAGER của đúng correction round S09-C4 do Codex PM/BA phân rã
trong prompt này. Codex là review/approval gate duy nhất. Manager không viết
production code, test, fixture, schema, UI hay config; chỉ preflight, resume đúng
owner, cấp lock, monitor, review, chạy gate độc lập và append coordination
evidence.

Đọc toàn bộ trước khi dispatch:

- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`;
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`;
- `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`;
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C3_PM_REVIEW_2026-08-26.md`;
- prompt C3, registry C3 và TASK/LOG/REPORT/evidence hiện tại của
  T05A/T03/T04/T05B/T06B.

Current Codex verdict:

`S09-C3 = CHANGES_REQUESTED`

Corrected terminal:

`S09-C3 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Đóng hữu hạn F1-F7 trong review C3. Không tự tạo thêm backlog, không mở S10,
production S11 hoặc production S13. Không `APPROVED/CLOSED`; không commit, push,
merge, reset, restore, checkout, clean, stash hoặc deploy. Cloud checkpoint chỉ
sau Codex `APPROVED`.

Ưu tiên tốc độ tối đa an toàn, không tiết kiệm quota. Mỗi correction phải resume
đúng owner cũ; worker không được mở subworker. Manager không được tự sửa lỗi.

## 2. Preflight/invariant bắt buộc

- Integration worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch `codex/s08-integration`; expected HEAD baseline
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`. Audit actual, không giả định.
- MAIN `C:\Users\Admin\MotionForge2D` read-only tuyệt đối với Manager/worker.
- Audit `git worktree list`, HEAD/branch/dirty paths, exact hashes, Alembic heads,
  DB env, command lines/process tree/ports và log stability. Không tin terminal
  C3. Nếu writer còn active, dừng dispatch và reconcile theo Rules.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi DB/runtime/cache/basetemp/output C4
  dùng root mới ngoài protected MAIN/data/project media.
- Manager tạo append-only
  `docs/pm/sessions/S09-C4-SESSION-REGISTRY.md`, ghi Task → exact session →
  provider/model → process/phase/state → exclusive write-set → dependency →
  hashes → heartbeat → exit.
- Giữ route của các owner cũ: provider `custom` qua 9Router
  `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled.
  Không tạo replacement session trừ khi Rules cho phép sau failure audit.
- Không migration/schema DB mới dự kiến. Nếu worker chứng minh thật sự cần
  migration/model change, dừng `BLOCKED_SCOPE` cho Codex; Manager không tự mở.
- Không sửa/nới benchmark thresholds, không fake output, marker/test pixel,
  route patch hoặc assertion hạ thấp.

## 3. Freeze/evidence retained

J1-C3-v4 là authority renderer duy nhất:

- path:
  `output/s09/20260823_sprint_full/j1-c3/renderer_freeze_manifest_v4.json`;
- manifest SHA:
  `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`;
- exact file set: 13 files.

I03/I05 retained inputs:

- I03 run-A content SHA:
  `12de134527765da2b3a2e890dc7a8d693c43b8325c2f8e122eb8886783d038c3`;
- I03 run-B content SHA:
  `dab37e418907b78e447dfe22f90001707952dc11fedf1ce607b37f32b6ddab40`;
- I05 decision SHA:
  `d289929d948ddfa7ae961810c47e43d4e1a37bda8aea21074c5a7df8c13063e9`.

Manager re-hash v4 manifest + 13/13 files trước Wave A và sau mọi wave. C4 bị
cấm sửa 13-file J1 set. Nếu một byte drift, không rerun I03/I05 và không tự pin
v5; terminal `BLOCKED_FREEZE_DRIFT` kèm path/owner attribution cho Codex.

## 4. BA contract C4 đã chốt

### 4.1 Affected scope phải là scope thật, không phải artifact-equality proxy

- Correction UI phải có current completed base job và current selected/active
  demo loop. Một correction từ demo surface gửi scope chính xác của loop đang
  sửa; không được thay bằng toàn bộ `completedLoops`, frame-range giả định hoặc
  fallback “all”.
- Khi không có exact selected loop hoặc base chưa completed, nút submit/confirm
  regeneration bị block rõ ràng; không archive correction với scope rỗng rồi
  gọi job.
- Applied context lưu exact non-empty `affected_loop_ids`; regenerate endpoint
  load context server-side và verify subset của immutable base publication.
- T03 được gọi renderer đúng số lần bằng số affected loops. Unaffected loops
  không decode/render/encode, không có `render_ms`, giữ exact Artifact row/file/
  ID/hash/size/frame_count và ghi `regenerated=false`.

### 4.2 Stable layer binding và exact semantic effect

- `affected_layer_ids` phải là stable machine IDs/keys từ structural evidence,
  không phải display label mơ hồ. Demo loop manifest/program phải mang stable
  `layer_id`/binding tương ứng cho các operation/placement có thể sửa.
- Effect applicator nhận `correction_kind`, canonical effect và exact affected
  layer/segment IDs. Không dùng `placements[0]`, array position, filename hoặc
  test-only mapping làm target authority.
- Mỗi expected target phải match đúng một render binding. Zero hoặc nhiều match
  fail closed trước render/publication/checkpoint effect.
- Z-order acceptance chính: target là placement thứ hai/non-first trong overlap
  fixture; chỉ target đổi z/compositing order, một unaffected overlapping layer
  giữ z. Output affected phải đổi bytes/hash/artifact thật.
- Cấm marker/pixel giả. Visual change phải đến từ operation compositor thật.

### 4.3 Five correction kinds không được false-success

Production UI đã quảng bá năm kind: mask, z_order, contact, mesh_parts,
route_override. C4 phải có canonical render-effect dispatch cho cả năm:

- `mask`: exact target + resolved immutable mask artifact/path/hash và mask
  semantics thật;
- `z_order`: exact target + corrected z-order;
- `contact`: exact contact/end-frame/time/anchor effect trên bound operation;
- `mesh_parts`: exact target + full applied transform, không chỉ
  `transform_type`;
- `route_override`: exact target/segment + measured-passing `route_to`, frame
  range/anchor/provenance; targeted plan dùng route override thật.

T05A applied context phải chứa đủ canonical post-apply values để T03 tái tạo
effect sau restart. Handler dispatch theo exact kind. Unknown/malformed/không có
binding phải fail closed; tuyệt đối không re-encode unchanged media rồi ghi
`regenerated=true`.

### 4.4 Durable generation identity

Fingerprint C4 bắt buộc là canonical SHA trên đúng:

`base_job_id + correction_context_sha256 + frozen_evidence_sha256`

Trong đó `frozen_evidence_sha256` là machine value server-side đã verify, bao
gồm exact I05 decision identity và benchmark content identity theo một canonical
object. Không nhận caller-trusted SHA làm authority.

- Same three-part tuple → same job/reused=true.
- Khác correction hoặc khác frozen evidence → different generation identity.
- Stale/missing/tampered evidence → zero durable mutation.

### 4.5 Worker/API evidence phải phân biệt reuse với rerender

`GET /api/v2/s09-demo-compare/jobs/{job_id}` phải expose read-only:

- `generation_evidence`: generation, base_job_id, correction_id,
  correction_context_sha256, frozen_evidence_sha256;
- exact `affected_loop_ids`;
- mỗi publication: `regenerated` boolean; `render_ms` chỉ có cho affected render;
  base publication identity cho unaffected.

API mapping đọc immutable attempt result, không suy luận `regenerated` từ hash
equality. UI hiển thị đúng scope/evidence backend trả về.

### 4.6 Worker-side fail-closed và cancellation

- `_load_base_publication`/handler phải so actual base Job workspace với
  `ctx.workspace_id`; cấm self-comparison no-op.
- Direct durable service submit cross-workspace, wrong type/state/base snapshot,
  context drift hoặc affected scope ngoài base đều fail trước publication.
- Cancel trước/during targeted work không để orphan Artifact row/file, partial
  success result hoặc false completed generation. Kill/restart/reconcile không
  rerender unaffected và không duplicate affected publication.

## 5. DAG và parallel authority

### Join J0-C4 — quiescence + retained freeze

Manager audit C3 terminal, active processes, dirty attribution, re-hash J1-v4
13/13 và pin exact current hashes. Chỉ sau J0 mới dispatch Wave A.

### Wave A — tối đa 5 exact owners song song

1. `S09-T05A-C4`, resume `20260824_072626_645cde`.
2. `S09-T03-C4`, resume `20260824_031524_a6bb2a`.
3. `S09-T04-C4-PREP`, resume `20260824_052859_c6e197`.
4. `S09-T05B-C4-PREP`, resume `20260824_093602_af7c26`.
5. `S09-T06B-C4-PREP`, resume `20260824_131423_423e42`.

Các worker code theo exact §4 interface đã freeze; không tự thương lượng contract
khác. PREP được viết phần độc lập nhưng không chạy acceptance final trước join.

### Join J1-C4 — context + handler

Chỉ mở khi T05A và T03 exit, focused/adversarial tests x2 xanh, write-set sạch.
Resume T04 exact owner để bind endpoint/status/fingerprint với implementation
thật. T04 không sửa T05A/T03 files.

### Wave B — frontend final

Sau T04 final exit, resume T05B exact owner để bind typed API/status, selected
loop và production UI. Backend T05A/T03/T04 lúc này read-only.

### Join J2-C4 — production acceptance

Sau T05B exit và all focused integration gates xanh, resume T06B exact owner.
T06B không sửa shared production code; finding mới route về exact owner rồi chờ
Manager resume lại.

## 6. Exclusive write-sets và acceptance

### S09-T05A-C4 — canonical render context for five kinds

Write only:

- `app/services/s09_correction.py`;
- `app/api/routes/s09_correction.py`;
- `app/schemas/s09_correction.py`;
- `tests/test_s09_t05_backend_*.py`;
- own output + append own LOG/REPORT.

Acceptance:

- stable machine layer IDs/keys, exact affected loops and complete per-kind
  canonical render effect survive fresh session/restart with identical SHA;
- mesh context includes full transform; mask context resolves immutable artifact
  evidence; contact/route context complete;
- pending/cancelled/stale/empty/malformed scope fail with zero mutation;
- all existing CAS/idempotency/provenance/count tests remain green x2.

### S09-T03-C4 — exact partial render/effect dispatcher

Write only:

- `app/workflow/s09_demo_jobs.py`;
- `app/schemas/s09_demo_loops.py` only if additive loop-binding type is needed;
- `tests/fixtures/s09_demo/**` only for stable layer/correction binding metadata,
  generator and matching synthetic assets; no benchmark threshold/media cheat;
- `tests/test_s09_t03_demo_loops.py`;
- own output + append own LOG/REPORT.

Acceptance:

- render spy proves one affected loop => exactly one render call; unaffected
  decode/render/encode call count zero;
- non-first layer z-order correction changes exact target only;
- all five kinds have real bound plan/effect tests; unchanged/unsupported false
  success impossible;
- fingerprint has three exact fields and evidence-difference test;
- worker cross-workspace, invalid base/context/scope fail closed;
- cancel/kill/restart/reconcile tests prove no orphan/residue/duplicate;
- long-path affected publication and unaffected reuse remain safe.

### S09-T04-C4 — identity binding + observable generation evidence

Write only:

- `app/api/routes/s09_demo_compare.py`;
- `app/schemas/s09_demo_compare.py`;
- `tests/test_s09_t04_demo_compare.py`;
- own output + append own LOG/REPORT.

Acceptance:

- endpoint computes server-side frozen evidence identity and passes three-field
  fingerprint contract;
- status exposes generation evidence/affected IDs/per-loop regenerated flag
  from attempt result, not hash inference;
- same tuple replay 200/same job; evidence tuple difference cannot collide;
- invalid/stale/tampered requests create zero job/artifact/checkpoint;
- content long-path GET/serve >=260 remains hash-verifiable;
- T03+T04 focused x2.

### S09-T05B-C4 — exact selected-loop UI

Write only:

- `frontend/src/features/demo/**`;
- T05B-owned new C4 frontend/E2E/config/setup files;
- own output + append own LOG/REPORT.

Trước code phải đọc `frontend/AGENTS.md` và relevant local Next docs.

Acceptance:

- pass current selected/active loop from compare viewer into CorrectionPanel;
  submit exactly that non-empty scope, never entire completed list;
- no exact loop/base completed => action blocked with clear Vietnamese helper;
- viewer adopts regen job and shows backend-reported affected/regenerated/reused
  evidence; no “full video rerun” or inferred success;
- five correction forms call real applied flow; error/conflict/retry/replay and
  keyboard/basic accessibility covered;
- TSC, scoped ESLint, production build and T05B production-stack test green.

### S09-T06B-C4 — discriminating production acceptance

Write only:

- new `frontend/e2e/s09-t06bc4-*` spec/setup files;
- new `frontend/playwright.s09t06bc4.config.ts`;
- `output/s09/20260823_sprint_full/t06b-c4/**`;
- append own LOG/REPORT.

Acceptance production Chromium x2, fresh DB/runtime each run, actual
`app.api.app`, production Next build/start, no route patch/mock:

1. Completed base has four loops and exact publication snapshot.
2. UI explicitly selects d4 and a non-first stable layer; stale confirm yields
   zero job/artifact/checkpoint; valid confirm applies.
3. Regeneration manifest/result/status all say affected exactly
   `[d4_group_occlusion]`; d4 `regenerated=true`, new artifact/hash and real
   target-layer compositing effect.
4. d1/d2/d3 `regenerated=false`, no `render_ms`, exact identity/hash/size/frame;
   DB attempt proves no renderer invocation/effect for them.
5. Replay same three-part tuple returns same job; different frozen-evidence test
   produces different fingerprint identity without mutating frozen files.
6. Parameterized backend/production integration proves five correction kinds
   apply their canonical effect or fail closed before job; no unchanged-media
   false success.
7. Approval route-override evidence still passes; reload + actual backend restart
   preserve generation/checkpoint evidence.

## 7. Manager final gate

Chỉ sau mọi owner exit và writers quiescent:

1. Re-hash J1-v4 manifest + 13 files: zero drift. Verify I03/I05 content SHAs
   remain exact; do not rerun measured benchmark when no drift.
2. Resolve all current `tests/test_s09*.py`, log exact file/count, run full S09
   suite in isolated basetemp with DB/PYTHONUTF8 unset: zero fail/error. Run
   T03/T04/T05 focused/adversarial lần hai và UTF8=1 encoding slice.
3. Run a Manager-owned read-only DB assertion equivalent to Codex repro:
   requested/affected exactly d4; flags `{d1:false,d2:false,d3:false,d4:true}`;
   d1/d2/d3 have no render timing/effect. Artifact equality alone không đủ.
4. Production C4 Chromium x2 fresh runtime; inspect exact E2E evidence JSON and
   DB attempt, không chỉ tin Playwright exit code/worker report.
5. Windows long-path write + HTTP serve >=260; canonical hash chain retained;
   actual 24/30/30000÷1001 fps/timebase slice retained.
6. Ruff `app tests scripts`; mypy `app --no-incremental`; Alembic one head;
   materialized OpenAPI no accidental duplicate; TSC; S09-scoped ESLint;
   production build; `git diff --check` và whitespace check cho untracked C4.
7. Audit write-set/attribution, MAIN/data/project media/protected artifacts,
   process/ports/temp ownership. Cleanup only owned resources after exact check.
8. Append reconciled final C4 state table; không để lock table PENDING khi task
   đã exit. Ghi exact commands, exit codes, counts, hashes và retries.

Nếu bất kỳ P0/P1, exact affected scope/layer, five-kind effect, three-part
fingerprint, cross-workspace refusal, no-residue cancellation, observable
generation evidence hoặc required gate fail/unknown, terminal:

`S09-C4 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Chỉ khi toàn bộ pass mới ghi:

`S09-C4 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Sau đó STOP và giao packet cho Codex review độc lập. Không APPROVED/CLOSED,
không push GitHub và không mở sprint khác.

Bắt đầu ngay: load rules đầy đủ → preflight/quiescence → re-hash J1-v4 → tạo
registry C4 → dispatch Wave A tối đa 5 exact owners theo DAG trên. Không chỉ trả
kế hoạch.
