Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch/resume worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, SHA-256, HEAD thực tế và các mục rules đã nạp. Chưa hoàn tất thì dừng `BLOCKED_RULES`; tuyệt đối không dùng trí nhớ/tóm tắt cũ.

# S09 C3 — targeted regeneration, unified freeze và long-path read Manager prompt

## 1. Authority và mục tiêu

Bạn là HERMES MANAGER của đúng correction round S09-C3 do Codex PM phân rã ở
đây. Codex giữ quyền BA/roadmap, task decomposition, parallel decision và
approval. Manager không tự sửa production code, test, fixture, benchmark, UI,
schema hay config; chỉ preflight, resume đúng owner, cấp lock, monitor, review,
chạy gate độc lập và append coordination evidence.

Đóng toàn bộ F1-F6 trong:

`C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C2_PM_REVIEW_2026-08-25.md`

Ưu tiên tốc độ tối đa an toàn, không tiết kiệm quota. Không tự tạo Task ID hoặc
subtask; không cho worker mở subworker. Không `APPROVED/CLOSED`; không commit,
push, merge, reset, restore, checkout, clean, stash hay deploy. Không mở S10,
production S11 hoặc production S13.

Sau Rules, đọc toàn bộ handoff, roadmap, target profile, C2 review nêu trên,
prompt C2, S09-C2 registry và TASK/LOG/REPORT/evidence hiện tại của I03/I05,
T03/T04/T05A/T05B/T06B.

## 2. Preflight và invariant

- Integration worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, expected branch
  `codex/s08-integration`, expected HEAD baseline
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`.
- MAIN `C:\Users\Admin\MotionForge2D` read-only tuyệt đối đối với
  Hermes/worker. Manager chỉ được append coordination/evidence trong integration
  worktree theo prompt này.
- Audit actual HEAD, dirty paths, hashes, Alembic heads, DB env, process command
  line/ports và quiescence. Không tin terminal C2. Nếu writer còn active, dừng
  dispatch và reconcile theo Rules.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi DB/runtime/cache/basetemp/output C3
  dùng root mới nằm ngoài protected MAIN/data/project media; không dùng
  basetemp dưới `C:\Users\Admin\MotionForge2D` vì QA guard sẽ từ chối.
- Tạo Manager-owned
  `docs/pm/sessions/S09-C3-SESSION-REGISTRY.md`; append-only. Ghi Task → exact
  session → provider/model → process/phase/state → exclusive write-set → hashes
  → dependency → heartbeat.
- Giữ provider/model hiện hữu: `custom` qua 9Router
  `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled.
  Mọi correction phải resume exact owner; replacement session chỉ theo Rules.
- Không sửa/nới thresholds, không fake output, không dùng QA app patch/test-only
  router, không hạ assertion. Cấm đụng renderer T02 files trong C3 nếu chưa báo
  `BLOCKED_SCOPE` cho Codex.

## 3. BA/architecture contract đã chốt

### 3.1 Applied correction → một durable targeted-regeneration generation

Production flow bắt buộc:

1. Base demo job đã `completed` và có full publication snapshot.
2. Correction được submit với non-empty `affected_loop_ids`, confirm thành
   `applied`; pending/cancelled/stale/empty-scope fail closed trước job creation.
3. API tạo một durable regeneration Job mới, fingerprint từ
   `base_job_id + applied correction immutable context SHA + frozen evidence
   SHA`. Replay cùng context trả đúng cùng job; correction khác tạo generation
   khác.
4. Job mới giữ full result view: unaffected loops reuse chính xác existing
   artifact row/file/ID/hash/size/frame_count; chỉ affected loops render lại.
5. Result ghi machine-readable generation evidence cho từng loop:
   `generation`, `base_job_id`, `correction_id`, `correction_context_sha256`,
   `regenerated` và publication identity. Affected loop phải có generation mới;
   acceptance C3 dùng một z-order correction có visual effect thật nên affected
   artifact ID và content hash cũng phải đổi.
6. Không được coi route pin bị từ chối, failed job hoặc replay job cũ là targeted
   regeneration. Route override không measured-passing vẫn phải fail closed,
   nhưng không được dùng nó để thay acceptance chính.

Không cần migration mới: dùng durable Job/Attempt/Artifact hiện hữu và immutable
S09Correction row/result. Nếu worker chứng minh thật sự cần schema change, dừng
`BLOCKED_SCOPE`; Manager không tự cấp quyền migration.

### 3.2 Exact backend interface giữa owner lanes

- T05A public service trả immutable applied-regeneration context từ correction:
  correction id/kind/applied revision/natural key, affected loop/layer/segment
  IDs, canonical mutation result/effect và canonical SHA. Refuse non-applied,
  empty affected loops hoặc malformed result.
- T04 production endpoint:
  `POST /api/v2/s09-demo-compare/jobs/{base_job_id}/regenerate`, body chỉ nhận
  `correction_id` và exact benchmark content pin khi schema hiện hành cần. Caller
  không được tự truyền/tamper affected scope hay correction context.
- Endpoint load context qua T05A service, verify base job type/state/workspace,
  affected IDs là subset của base requested loops, rồi submit manifest C3 cho
  T03. Zero durable mutation khi validation fail.
- T03 handler verify canonical context SHA, load immutable base result, reuse
  unaffected publications và apply correction effect thật chỉ vào affected
  render program. Với C3 acceptance, z-order effect phải thay đổi compositing
  order của một layer trong overlap fixture; không chèn marker/test pixel giả.
- T05B truyền current base job ID vào CorrectionPanel, gửi non-empty
  `affected_loop_ids`, confirm rồi gọi endpoint regeneration, poll durable job và
  cập nhật compare result. UI hiển thị targeted generation; không ghi “full
  video rerun”.

### 3.3 Unified machine-readable freeze

- C2 J1-v3 hiện có SHA
  `b8928aeca2faedb909269372c9b08f248675b77cca835d8ae967e00cc6208a43`
  và re-hash 13/13 file tại Codex review. Manager phải re-audit actual disk trước
  dispatch.
- Nếu 13-file set không drift, Manager tạo J1-C3-v4 manifest mới, supersede v3,
  cùng exact behavior-critical set và pin manifest file SHA. Nếu drift, dừng và
  route về exact owner gây drift; không sửa constant.
- I03 measured CLI phải nhận exact Manager manifest path/SHA, verify toàn bộ
  path→hash trước và sau từng run. Không scan “newest”, không fallback v2/v1,
  không tin manifest ba-file `output/s09/contract_freeze_manifest.json`, không
  dùng prose token trong C1 registry làm authority.
- Mỗi measured row ghi exact `j1_manifest_path` + v4 manifest SHA. I05 và mọi
  downstream binding phải pin cùng SHA đó.
- `decoded_output_hash` phải dùng canonical algorithm độc lập: frame count +
  ordered frame shape + contiguous decoded bytes, và bắt buộc bằng production
  adapter `output_frame_sha256` cho từng measured row. Không gọi production hash
  helper để giả độc lập; được dùng public decoder để đọc encoded artifact.

## 4. DAG và parallel authority

### Join J0-C3 — quiescence + freeze v4

Manager audit C2 terminal, xác nhận không writer/process/port thuộc lane còn
active, re-hash v3 13-file set và pin J1-C3-v4. Chỉ sau đó dispatch Wave A.

### Wave A — tối đa 5 exact owners song song

1. `S09-T05A-C3`, resume `20260824_072626_645cde`.
2. `S09-T03-C3`, resume `20260824_031524_a6bb2a`.
3. `S09-T04-C3-PREP`, resume `20260824_052859_c6e197`.
4. `S09-T05B-C3-PREP`, resume `20260824_093602_af7c26`.
5. `S09-T00-I03-C3`, resume `20260823_173318_69a813`.

T04 PREP đóng Windows long-path read/serve và scaffold endpoint theo exact
interface; final integration chờ T05A+T03. T05B PREP đóng affected IDs,
`reasonsOf()` và UI wiring; production E2E chờ T04 final. I03 được chạy measured
A/B ngay vì bốn lane kia bị cấm sửa J1 file set.

### Join J1-C3 — backend regeneration contract

Chỉ mở khi T05A và T03 exit, tests riêng x2 xanh, code/write-set attribution
sạch. Resume T04 exact owner để hoàn tất endpoint integration và backend tests.
T04 không được chiếm T05A/T03 files.

### Wave B — decision và UI integration

- Sau I03 verified trên v4, resume `S09-T00-I05-C3` exact owner
  `20260823_233406_8d5b7b`. I05 chỉ đọc frozen inputs, tạo C3 decision/evidence;
  không sửa code/test/fixture/threshold.
- T04 final và T05B final có thể chạy song song khi T05A/T03 contract đã stable
  vì backend route/schema và frontend write-set tách biệt. Mọi final production
  binding phải chờ I05 SHA; nếu đang chờ thì state `WAITING_JOIN`, không giả
  `TASK_SUBMITTED`.

### Join J2-C3 — production acceptance

Sau I05, T04 và T05B verified/exit, pin exact I03/I05/J1-v4 chain rồi resume
`S09-T06B-C3` exact owner `20260824_131423_423e42`. T06B chỉ viết acceptance
spec/config/setup/output/LOG/REPORT của mình; finding production phải route về
đúng owner, không tự sửa shared code.

## 5. Exclusive write-sets và acceptance từng owner

### S09-T05A-C3 — applied correction context

Write:

- `app/services/s09_correction.py`;
- `app/api/routes/s09_correction.py`, `app/schemas/s09_correction.py` chỉ khi
  public context cần surface additive;
- `tests/test_s09_t05_backend_*.py`;
- own output + append own LOG/REPORT.

Acceptance:

- canonical applied context/SHA deterministic qua fresh session/restart;
- pending/cancelled/stale/empty affected-loop scope refuse với zero job/artifact/
  checkpoint mutation;
- applied row immutable và replay trả same context SHA;
- existing five correction kinds/CAS/idempotency regressions xanh.

### S09-T03-C3 — durable partial generation

Write:

- `app/workflow/s09_demo_jobs.py`;
- `app/schemas/s09_demo_loops.py` chỉ nếu manifest/result type cần;
- `tests/test_s09_t03_demo_loops.py`;
- own output + append own LOG/REPORT.

Acceptance:

- completed base job + immutable correction context tạo one new generation;
- affected z-order correction thực sự đổi rendered bytes/hash/artifact;
- unaffected publication/file/Artifact row identities byte-identical, zero
  duplicate rows;
- same correction replay same job; different correction new generation;
- kill/restart/cancel/reconcile không partial/residue và không render lại
  unaffected loops;
- tampered context/base job/wrong workspace/failure rollback fail closed.

### S09-T04-C3 — API + long-path read

Write:

- `app/api/routes/s09_demo_compare.py`;
- `app/schemas/s09_demo_compare.py`;
- `tests/test_s09_t04_demo_compare.py`;
- own output + append own LOG/REPORT.

Acceptance:

- endpoint exact §3.2, zero mutation cho invalid request;
- HTTP status/replay semantics deterministic;
- content GET thật phục vụ và hash-verify MP4 khi final absolute path >=260;
  existence check lẫn `FileResponse` đều long-path safe;
- update exact C3 benchmark/decision/J1 binding sau I05, không fallback C2/v1;
- T03+T04 focused suite x2 xanh.

### S09-T05B-C3 — production UI

Write:

- `frontend/src/features/demo/**`;
- T05B-owned E2E/config/setup files;
- own output + append own LOG/REPORT.

Acceptance:

- CorrectionPanel nhận current completed base job và gửi non-empty affected
  loops; confirm thành công tự mở/poll targeted regeneration và cập nhật viewer;
- loading/error/conflict/retry/replay states rõ, keyboard/basic accessibility;
- `ApprovalPanel.reasonsOf()` match cả reasons thường và route override
  `override_reason`/`provenance.evidence`, không né bằng warning;
- TSC, scoped ESLint, production build và T05B production-stack test xanh.

### S09-T00-I03-C3 — freeze + canonical measured evidence

Write:

- `scripts/s09_renderer_benchmark.py`;
- `tests/test_s09_t00_benchmark_harness.py`;
- `output/s09/20260823_sprint_full/t00-i03-c3/**`;
- append own LOG/REPORT.

Không sửa renderer production files, fixture media/manifests hoặc threshold
values. Acceptance:

- one explicit v4 manifest authority, pre/post drift fail-closed;
- no v2/v1/three-file/prose fallback active;
- canonical independent decoded hash equals adapter hash for every measured row;
- same-seed A/B core-identical; 6/6 classes actual route measured-pass,
  adversarial controls fail as expected; focused tests x2.

### S09-T00-I05-C3 — decision only

Write only own C3 output + append I05 LOG/REPORT. Verify exact v4 manifest,
I03 A/B SHA/determinism/canonical-hash equality. Produce 6/6
`PASS_MEASURED_ROUTE`, sample counts >0, `FAIL_OPEN_QUESTION=0`, provenance pin
same v4 and I03 SHA. Không sửa code/test/fixture/threshold.

### S09-T06B-C3 — real production acceptance

Write only T06B C3 spec/config/setup/output + append LOG/REPORT. Production
Chromium x2 với fresh DB/runtime, actual `app.api.app`, production build/start,
không patch.

Binary flow:

1. Tạo completed base job 4 loops; snapshot all publication rows/IDs/hashes/
   sizes/frame counts/generations.
2. Qua actual UI submit z-order correction có non-empty affected loop
   `d4_group_occlusion` và layer thật trong overlap fixture; stale confirm 409
   tạo zero job/artifact/checkpoint; valid confirm applied.
3. UI tự tạo targeted regeneration job; affected loop có generation mới,
   `regenerated=true`, new artifact ID và new content hash. Ba unaffected loops
   giữ exact identity/hash/size/frame_count và DB row count.
4. Replay same correction trả same regeneration job; không duplicate.
5. Pending correction vẫn block approval; sau applied regeneration thì explicit
   approval pass. Route-override evidence match được trực tiếp, không thay bằng
   warning workaround.
6. Browser reload + actual backend restart giữ regeneration evidence,
   publications và checkpoint/hash verify.

## 6. Manager final gate

Sau mọi worker exit và writers quiescent:

1. Audit write-set/attribution, J1-v4 no drift, I03/I05/T04/T06B SHA chain exact.
2. Resolve toàn bộ current `tests/test_s09*.py`, log exact list/count; chạy bằng
   isolated basetemp ngoài protected MAIN, DB env và `PYTHONUTF8` unset: 0
   fail/error. Chạy focused T03/T04/T05/I03 suites lần hai và encoding slice với
   `PYTHONUTF8=1`.
3. Explicit Windows long-path write + HTTP read/serve test >=260 chars; actual
   24/30/30000÷1001 fps probe; recompute canonical hashes độc lập cho 6 rows và
   assert equality với adapter evidence.
4. Production correction→only affected regeneration→approval→reload→actual
   backend restart E2E Chromium x2 fresh runtime.
5. Actual materialized OpenAPI no duplicate path/method; Ruff `app tests
   scripts`; mypy `app --no-incremental`; Alembic one head; TSC; S09-scoped
   ESLint; production build; `git diff --check` và explicit whitespace check cho
   untracked C3 files.
6. `rg` active gate: no production/frontend/active-test reference tới old C2/v1
   measured/decision/freeze as authority; archival logs/reports được attribution.
7. Verify MAIN/data/project media/protected artifacts unchanged. Cleanup only
   owned process/port/temp after exact ownership check; không kill process khác.
8. Registry append exact commands, exit codes, counts, hashes, process exits và
   any retry. Manager review code/evidence, không chép worker report.

Nếu bất kỳ P0/P1, targeted regeneration, canonical hash, freeze chain,
long-path HTTP read, real-stack E2E hoặc required gate fail/unknown, terminal:

`S09-C3 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Chỉ khi toàn bộ pass mới ghi:

`S09-C3 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Sau đó STOP và đưa packet cho Codex review độc lập. Không APPROVED/CLOSED, không
push GitHub và không mở sprint khác. Cloud checkpoint chỉ sau Codex APPROVED.
