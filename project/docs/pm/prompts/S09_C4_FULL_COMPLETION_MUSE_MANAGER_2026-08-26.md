Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, kiểm tra tiến trình, sửa tài liệu điều phối hoặc dispatch/resume worker. Sau khi đọc đủ từ đầu tới cuối, báo `RULES_LOADED` kèm đường dẫn, số dòng, SHA-256, HEAD thực tế và các mục rules đã nạp. Nếu chưa đọc đủ, file thiếu hoặc có mâu thuẫn chưa giải quyết được thì dừng `BLOCKED_RULES`; tuyệt đối không dùng trí nhớ hoặc bản tóm tắt cũ.

# S09-C4 — full completion Manager prompt, Muse Spark 1.2 Contributor

## 1. Authority, verdict và outcome

Bạn là HERMES MANAGER mới tiếp quản và hoàn tất đúng correction round
`S09-C4`. Codex PM/BA/Reviewer là gate `APPROVED` duy nhất.

Manager chỉ preflight, reconcile session/process, resume/recover đúng owner,
điều phối, monitor, review đầu ra, chạy verification gate độc lập và append
coordination evidence. Manager **không được tự viết hoặc sửa** production code,
test, fixture, schema, migration, UI hay config. Mọi correction code phải về
đúng worker owner.

Current Codex verdict giữ nguyên:

`S09-C3 = CHANGES_REQUESTED`

Mục tiêu prompt này là đóng toàn bộ C4 contract và dừng tại một trong hai trạng
thái:

- pass: `S09-C4 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`;
- fail/unknown: `S09-C4 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`.

Không `APPROVED/CLOSED`, không mở S10, production S11 hoặc production S13.
Không commit, push, merge, deploy, reset, restore, checkout, clean hoặc stash.
Cloud checkpoint chỉ sau Codex review độc lập và `APPROVED`.

Đọc toàn bộ trước khi dispatch:

1. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`;
2. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`;
3. `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`;
4. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C3_PM_REVIEW_2026-08-26.md`;
5. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S09_C4_CORRECTION_MANAGER_2026-08-26.md`;
6. `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\docs\pm\sessions\S09-C4-SESSION-REGISTRY.md`;
7. TASK/LOG/REPORT và evidence hiện hành của T05A, T03, T04, T05B, T06B.

Prompt này là authority live hợp nhất để hoàn tất C4. Original C4 prompt và C3
review là required evidence/contract input; nếu snapshot cũ mâu thuẫn actual
disk/process thì ghi discrepancy và dùng actual evidence cùng chỉ thị mới nhất
của user trong prompt này.

## 2. User-authorized model override — bắt buộc

User mới nhất yêu cầu **mọi worker được dispatch/resume bởi Manager chat này cho
S09-C4** dùng:

- provider: `muse`;
- base URL: `http://127.0.0.1:20128/v1`;
- model ID: `ocg/muse-spark-1.2-contributor`;
- reasoning: `max`;
- fallback: **disabled**.

Đây là explicit override cho cả các existing owner session S09-C4 được resume:

- `20260824_072626_645cde` — T05A nếu cần correction;
- `20260824_031524_a6bb2a` — T03 nếu cần correction;
- `20260824_052859_c6e197` — T04 final;
- `20260824_093602_af7c26` — T05B final;
- `20260824_131423_423e42` — T06B production final;
- đúng một replacement recovery session nếu điều kiện context-hỏng trong §8
  được thỏa mãn.

Mỗi worker command line và prompt phải ghi chính xác provider/model/reasoning/
fallback trên. Không dùng `custom/alpha`, `alpha`, `openrouter/stealth/ox-alpha`
hoặc model khác. Manager phải verify effective route từ command line và log
trước khi công nhận worker đang chạy. Sai route hoặc fallback xảy ra thì dừng
worker và báo `BLOCKED_MODEL_ROUTE`; không âm thầm đổi model.

Model override này chỉ áp dụng cho worker của đúng Manager chat/prompt S09-C4
này; không áp ngược cho sprint/chat khác. Manager chat dùng model nào không làm
thay đổi worker policy trên.

## 3. Trạng thái live Codex đã audit lúc 2026-08-26 khoảng 21:07 +07

Workspace:

- integration worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`;
- branch/HEAD quan sát:
  `codex/s08-integration` /
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`;
- dirty count quan sát: 117. Registry preflight cũ ghi 111 nên đã stale; không
  xóa/restore thay đổi, phải audit attribution lại.

Freeze retained:

- J1-C3-v4 path:
  `output/s09/20260823_sprint_full/j1-c3/renderer_freeze_manifest_v4.json`;
- manifest SHA:
  `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`;
- exact set: 13 files, từng re-hash 13/13 MATCH;
- I03 run-A:
  `12de134527765da2b3a2e890dc7a8d693c43b8325c2f8e122eb8886783d038c3`;
- I03 run-B:
  `dab37e418907b78e447dfe22f90001707952dc11fedf1ce607b37f32b6ddab40`;
- I05 decision:
  `d289929d948ddfa7ae961810c47e43d4e1a37bda8aea21074c5a7df8c13063e9`.

Current task ledger:

| Task | Exact owner | Live state |
|---|---|---|
| S09-T05A-C4 | `20260824_072626_645cde` | worker exit; Manager focused verify 56 passed + Ruff; read-only trừ finding được route lại |
| S09-T03-C4 | `20260824_031524_a6bb2a` | R7 exit; Manager verify 38 passed + mypy; F-A/F-B đóng; chờ J1 integration |
| S09-T04-C4 | `20260824_052859_c6e197` | previous R4 **exited without task completion**; route A chưa áp dụng |
| S09-T05B-C4 | `20260824_093602_af7c26` | PREP verified, `WAITING_JOIN`; final chờ T04/J1 |
| S09-T06B-C4 | `20260824_131423_423e42` | PREP verified, `WAITING_JOIN`; production final chờ T05B/J2 |

T04 factual state:

- source/test/LOG không có write mới sau 14:45;
- `_seed_applied_zorder_correction` vẫn chưa dùng
  `wire_extraction_segment(logical_id=fixture layer_id)`;
- `output/s09/20260823_sprint_full/t04-c4/dispatch3.log` tăng từ 307 lên 561
  byte lúc 21:00:52 và kết thúc bằng lỗi deterministic route cũ:
  `HTTP 401: [openrouter/stealth/ox-alpha] ...`, rồi wrapper ghi
  `EXIT-T04-C4-R4=0`;
- exit wrapper 0 **không phải** worker verdict và không phải task success;
- tại Codex audit sau đó không còn live process mang owner T04 hoặc sleeper cũ.

Trước khi thoát, Manager/worker cũ từng tạo double-watchdog: Manager lặp
`sleep 570`, worker lặp `sleep 480`. Đây là liveness defect đã kết thúc bằng
401 route alpha; Manager mới không được phục hồi đường alpha và không được lặp
blind sleep.

## 4. Preflight/invariant bắt buộc

1. Xác minh Manager chat cũ đã dừng và không còn tool call/watchdog active.
2. Audit actual branch/HEAD/status, `git worktree list`, dirty attribution,
   Alembic heads, DB env, process tree/command lines, ports, log stability và
   owner sessions. Không tin riêng registry/report.
3. MAIN `C:\Users\Admin\MotionForge2D` read-only tuyệt đối với Manager/worker.
4. `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi test DB, basetemp, runtime, cache,
   port và output mới phải isolated, C4-owned và không chạm user/project data.
5. Re-hash J1-v4 manifest và 13/13 files trước first dispatch và sau mỗi wave.
   Drift một byte: dừng `BLOCKED_FREEZE_DRIFT`; không tự pin v5 và không rerun
   I03/I05.
6. Không migration/schema DB mới dự kiến. Nếu cần model/migration production
   ngoài allowlist, dừng `BLOCKED_SCOPE` cho Codex.
7. Không nới benchmark threshold, bỏ/skip assertion, fake output, marker pixel,
   route patch/mock hoặc test-only bypass.
8. Append-only reconcile
   `docs/pm/sessions/S09-C4-SESSION-REGISTRY.md`: Task -> exact owner -> effective
   Muse route -> state -> process -> write-set -> dependency -> heartbeat ->
   recovery reason -> exit. Không rewrite lịch sử PENDING cũ.
9. Manager coordination được ghi tại registry, S09 sprint report và một output
   root mới dưới `output/s09/20260823_sprint_full/manager-c4-muse/**`; Manager
   không sửa code/test/UI.

## 5. BA contract C4 — full binding

### 5.1 Exact affected scope

- Correction UI phải có completed base job và exact selected/active demo loop.
- Submit scope chính xác loop đang sửa; cấm thay bằng toàn bộ
  `completedLoops`, frame-range đoán hoặc fallback all.
- Không exact selected loop hoặc base chưa completed thì block submit rõ ràng;
  không archive scope rỗng rồi gọi job.
- Applied context lưu exact non-empty `affected_loop_ids`; endpoint load
  server-side và verify subset của immutable base publication.
- T03 gọi renderer đúng số affected loops. Unaffected loop không
  decode/render/encode, không `render_ms`, giữ exact Artifact row/file/ID/hash/
  size/frame_count và ghi `regenerated=false`.

### 5.2 Stable layer binding và exact semantic effect

- `affected_layer_ids` là stable machine IDs/keys từ structural evidence, không
  display label.
- Loop manifest/program mang stable `layer_id`/binding cho operation/placement.
- Applicator nhận `correction_kind`, canonical effect và exact affected layer/
  segment IDs. Cấm `placements[0]`, array position, filename hoặc test-only map
  làm target authority.
- Mỗi target match đúng một render binding. Zero/multiple match fail closed
  trước render/publication/checkpoint.
- Z-order acceptance: target là placement/non-first group entry; chỉ target đổi
  z/compositing, overlapping unaffected layer giữ nguyên. Output affected đổi
  bytes/hash/artifact do compositor thật, không marker/pixel giả.

### 5.3 Five correction kinds không false-success

Production contract gồm năm kind:

- `mask`: exact target + immutable mask artifact/path/hash + real mask semantics;
- `z_order`: exact target + corrected z-order;
- `contact`: exact contact/end-frame/time/anchor effect trên bound operation;
- `mesh_parts`: exact target + full applied transform;
- `route_override`: exact target/segment + measured-passing `route_to`, frame
  range/anchor/provenance, targeted plan dùng override thật.

T05A applied context phải đủ canonical post-apply values để T03 tái tạo sau
restart. Handler dispatch exact kind. Unknown/malformed/unbound phải fail closed;
cấm re-encode unchanged media rồi ghi `regenerated=true`.

### 5.4 Durable generation identity

Fingerprint là canonical SHA trên đúng:

`base_job_id + correction_context_sha256 + frozen_evidence_sha256`

`frozen_evidence_sha256` là server-verified machine value binding exact I05
decision và benchmark content identity; không tin caller SHA làm authority.

- same three-part tuple -> same job, `reused=true`;
- khác correction/evidence -> different identity;
- stale/missing/tampered evidence -> zero durable mutation.

### 5.5 Observable generation evidence

`GET /api/v2/s09-demo-compare/jobs/{job_id}` expose read-only:

- generation, base_job_id, correction_id, correction_context_sha256,
  frozen_evidence_sha256;
- exact affected_loop_ids;
- mỗi publication: `regenerated`; `render_ms` chỉ affected; base publication
  identity cho unaffected.

Mapping đọc immutable attempt result; không suy luận regenerated từ hash
equality. UI hiển thị scope/evidence backend trả về.

### 5.6 Worker-side fail-closed và cancellation

- Handler verify actual base Job workspace với `ctx.workspace_id`; cấm
  self-comparison.
- Direct durable submit cross-workspace, wrong type/state/base snapshot, context
  drift hoặc affected scope ngoài base fail trước publication.
- Cancel trước/during target work không orphan Artifact/file, partial success
  hoặc false completed generation.
- Kill/restart/reconcile không rerender unaffected và không duplicate affected
  publication.

## 6. Task map, ownership và write-sets

### S09-T05A-C4 — conditional correction owner

Exact owner: `20260824_072626_645cde`.

Write only nếu J1/T06B finding thật route lại:

- `app/services/s09_correction.py`;
- `app/api/routes/s09_correction.py`;
- `app/schemas/s09_correction.py`;
- `tests/test_s09_t05_backend_*.py`;
- own output + append own LOG/REPORT.

Acceptance: five-kind canonical context restart-stable, stable machine IDs,
complete mesh/mask/contact/route values, stale/empty/malformed fail zero
mutation, CAS/idempotency/provenance tests xanh x2.

### S09-T03-C4 — conditional correction owner

Exact owner: `20260824_031524_a6bb2a`.

Write only nếu J1/T06B finding thật route lại:

- `app/workflow/s09_demo_jobs.py`;
- `app/schemas/s09_demo_loops.py` additive binding only;
- `tests/fixtures/s09_demo/**` binding metadata/generator/synthetic assets only;
- `tests/test_s09_t03_demo_loops.py`;
- own output + append own LOG/REPORT.

Acceptance: one affected loop = one render call; unaffected render calls zero;
non-first binding exact; all five kinds real; three-field fingerprint;
cross-workspace/base/context/scope fail closed; cancel/restart no residue;
long-path safe.

### S09-T04-C4 — first active task

Primary owner: `20260824_052859_c6e197`.

Write only:

- `app/api/routes/s09_demo_compare.py`;
- `app/schemas/s09_demo_compare.py`;
- `tests/test_s09_t04_demo_compare.py`;
- own output + append own LOG/REPORT.

Required final correction:

1. Read actual `wire_extraction_segment` and guards first.
2. Trong `_seed_applied_zorder_correction`, seed segment qua
   `wire_extraction_segment` với deterministic
   `logical_id == fixture layer_id`, thay `create_segment`.
3. Không sửa T05A/T03/structural-evidence/fixtures.
4. Nếu REQUIRED_JOB/source_job_id thật sự chặn route A, return
   `BLOCKED_WITH_FINDINGS` với code/line/repro; Manager route option B về T05A,
   không tự mở scope.
5. T04 focused x2, hai basetemp mới, DB unset, kỳ vọng 21/21 mỗi run.
6. Ruff + mypy scoped + diff-check.
7. Append LOG/REPORT `STATUS: TASK_SUBMITTED (S09-T04-C4)`.

Full T04 acceptance: server-side frozen identity, three-field fingerprint,
observable affected/regenerated evidence, replay identity, evidence
non-collision, tampered/stale zero mutation và long-path content serve >=260.

### S09-T05B-C4 — frontend final

Exact owner: `20260824_093602_af7c26`.

Write only:

- `frontend/src/features/demo/**`;
- T05B-owned C4 frontend/E2E/config/setup files;
- own output + append own LOG/REPORT.

Trước code đọc `frontend/AGENTS.md` và relevant local Next docs.

Acceptance: selected/active loop exact; never all completed loops; unavailable
scope/base block với helper tiếng Việt; UI adopts regen job và displays backend
affected/regenerated/reused; five forms use real applied flow; conflict/retry/
replay/accessibility; TSC, scoped ESLint, production build và production-stack
test xanh.

### S09-T06B-C4 — production acceptance final

Exact owner: `20260824_131423_423e42`.

Write only:

- new `frontend/e2e/s09-t06bc4-*` spec/setup files;
- new `frontend/playwright.s09t06bc4.config.ts`;
- `output/s09/20260823_sprint_full/t06b-c4/**`;
- append own LOG/REPORT.

T06B không sửa shared production code. Finding phải route về exact owner.

## 7. Dependency DAG và maximum safe parallelism

Current DAG:

`J0-MUSE -> T04 final -> J1-C4 -> T05B final -> J2-C4 -> T06B production x2 -> Manager final gate -> Codex review`

- Ban đầu chỉ T04 dependency-ready; T05B phụ thuộc T04/J1, T06B phụ thuộc
  T05B/J2. Không có idle slot production hợp lệ để tự mở sprint khác.
- Read-only freeze/process/model preflight có thể chạy song song nội bộ nhưng
  global/shared tests phải mutex và writers quiescent.
- Nếu J1/T06B tìm defect thuộc T03/T05A/T04/T05B, serialize correction về exact
  owner rồi chạy lại downstream gate bị ảnh hưởng.
- Worker không mở subworker.

## 8. Session recovery và T04 resume bằng Muse

### J0-MUSE

1. Xác minh không còn owner T04/old watchdog process active. Nếu có, audit
   command line, process tree, stack, CPU/log/source mtime. Chỉ terminate exact
   stale sleep/self-monitor tree sau khi chứng minh không patch/test/write và
   không chờ user input; không pkill hoặc kill toàn bộ Hermes/Python/Node.
2. Append recovery fact: old R4 exited lúc 21:00 với HTTP 401 trên alpha route;
   wrapper exit 0 không phải task success.
3. Probe Muse route nhỏ, chỉ log HTTP status/time, không lộ key. HTTP 200 thì
   resume ngay. 400/401/403/unknown Muse model/quota/credit ->
   `BLOCKED_MODEL_ROUTE`, không blind retry.
4. Re-hash freeze 13/13, DB guard, registry/model map rồi dispatch T04.

### T04 R5

Resume exact owner `20260824_052859_c6e197` với provider `muse`, model
`ocg/muse-spark-1.2-contributor`, reasoning max, fallback disabled.

Worker prompt phải cấm mọi `sleep`, self-monitor, CPU/mtime watchdog hoặc chờ
thụ động. Worker phải thực thi §6 T04 ngay hoặc trả blocker cụ thể.

Nếu exact old owner với Muse vẫn phát blind sleep/self-watch, hoặc 8 phút không
có prompt/tool/source/log progress trong khi Muse probe 200 và stack chứng minh
terminal self-monitor, coi là context hỏng. Khi đó Manager được phép:

1. capture transcript/process/stack evidence;
2. terminate exact old tree và xác minh owner cũ dead;
3. append `RECOVERY_REASON=CONTEXT_CORRUPT_DOUBLE_WATCHDOG`;
4. tạo đúng một replacement session cho cùng Task ID T04, cùng Muse policy và
   write-set;
5. ghi old -> replacement owner mapping, không để hai owner sống đồng thời.

Nếu replacement lặp lỗi hoặc route A/B không khả thi, dừng C4 blocked; không tạo
replacement thứ hai.

### Connection policy

Chỉ confirmed connection error/502/503/504/disconnect/network timeout mới dùng
chu kỳ `wait đúng 5 phút -> audit -> resume same owner/same Muse route`. Không
dùng `sleep 480/540/570` để monitor. Probe khỏe + self-sleep/no progress là
liveness defect, không phải `RUNNING_RETRY_WAIT`.

## 9. Join gates và production acceptance

### J1-C4 — backend/API integration

Sau T04 exit và writers quiescent, Manager review actual diff/ownership và chạy:

- T04 focused x2: 21/21 mỗi run;
- T03+T04 focused/adversarial x2;
- T05A five-kind context suite fresh;
- relevant T03 suite fresh;
- Ruff/mypy scoped, diff-check, freeze 13/13.

Fail phải route đúng owner. Chỉ J1 xanh mới resume T05B bằng Muse.

### J2-C4 — frontend integration

Sau T05B exit:

- inspect typed API/status/scope integration;
- TSC, scoped ESLint, production build;
- T05B production-stack test với fresh runtime;
- backend read-only và freeze 13/13.

Chỉ J2 xanh mới resume T06B bằng Muse.

### T06B production Chromium x2

Mỗi run dùng fresh isolated DB/runtime/ports/output, actual `app.api.app` và
production Next build/start, không route patch/mock. Bắt buộc chứng minh:

1. Completed base có bốn loops và exact publication snapshot.
2. UI chọn d4 và non-first stable layer; stale confirm zero mutation; valid
   confirm applies.
3. requested/affected exact `[d4_group_occlusion]`; d4
   `regenerated=true`, artifact/hash mới và real target-layer effect.
4. d1/d2/d3 `regenerated=false`, không `render_ms`, exact identity/hash/size/
   frame và DB attempt không renderer invocation/effect.
5. Same three-part tuple replay same job; different evidence gives different
   identity without frozen drift.
6. Five kinds apply canonical effect hoặc fail closed trước job; không
   unchanged-media false success.
7. Approval route-override vẫn pass; reload + actual backend restart giữ
   generation/checkpoint evidence.

Production finding route exact code owner, correction, rồi rerun cả hai
production runs bị ảnh hưởng.

## 10. Liveness/heartbeat

- Heartbeat ít nhất mỗi 20 phút: task/session, effective Muse route, phase,
  progress mới, log, blocker, next action, slot state.
- Không progress 8 phút: audit ngay process/input/log/socket/stack/lock/test và
  **đưa ra quyết định**, không lặp `wc -c`.
- Báo sự cố ngay, không chờ heartbeat kế.
- Worker cấm sleep/self-monitor; Manager chỉ chờ 300 giây sau confirmed transient
  connection error rồi phải resume thật.
- Tiếp tục `monitor -> review -> correction/resume -> verify -> report` tới
  terminal được cấp quyền; không dừng chỉ vì một worker trả lời.

## 11. Final Manager gate

Chỉ sau mọi owner exit và writers quiescent:

1. Re-hash J1-v4 manifest + 13/13; verify I03/I05 SHAs exact; không rerun
   measured benchmark khi no drift.
2. Resolve toàn bộ current `tests/test_s09*.py`; ghi exact file/count; chạy full
   S09 suite isolated với DB unset: zero fail/error.
3. T03/T04/T05 focused/adversarial repeat và UTF8=1 encoding slice.
4. Manager-owned read-only DB assertion: requested/affected d4 only; flags
   `{d1:false,d2:false,d3:false,d4:true}`; unaffected không render timing/effect.
5. Inspect cả hai Chromium evidence JSON và DB attempts; không chỉ tin exit code.
6. Windows long-path write + HTTP serve >=260; canonical hash chain và
   24/30/30000÷1001 fps/timebase retained.
7. Ruff `app tests scripts`; mypy `app --no-incremental`; Alembic one head;
   materialized OpenAPI no accidental duplicate; TSC; S09-scoped ESLint;
   production build; `git diff --check`; whitespace check untracked C4.
8. Audit write-set/attribution, MAIN/data/project media, protected artifacts,
   process/ports/temp. Cleanup only exact owned resources.
9. Append reconciled final registry state table; không để state PENDING khi
   owner đã exit. Ghi exact model route, commands, exits, counts, hashes,
   retries/recovery và evidence paths.

## 12. Required final report

Report phải có:

- task -> owner session -> effective provider/model/reasoning/fallback;
- old alpha 401 recovery và replacement reason nếu có;
- files changed theo owner/write-set;
- exact test/build/E2E commands, exit codes, counts, runtimes;
- freeze/I03/I05 hashes;
- production DB affected/regenerated/render evidence;
- findings đã route/correct/reverify;
- blockers, residual risks, process/resource cleanup;
- terminal state và packet path cho Codex.

Nếu bất kỳ P0/P1, exact affected scope/layer, five-kind effect, three-field
fingerprint, cross-workspace refusal, cancellation residue, observable evidence,
Muse route hoặc required gate fail/unknown:

`S09-C4 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Chỉ khi toàn bộ pass:

`S09-C4 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Sau đó STOP. Không APPROVED/CLOSED, không push GitHub và không mở sprint khác.

## 13. Start command

Bắt đầu ngay sau `RULES_LOADED`: đọc required files đầy đủ -> preflight actual
repo/process/model/freeze -> append J0-MUSE reconciliation -> probe provider
`muse` -> resume T04 exact owner bằng `ocg/muse-spark-1.2-contributor` -> hoàn
tất T04/J1/T05B/J2/T06B/final gate theo DAG. Không chỉ trả kế hoạch và không
phát blind sleep.
