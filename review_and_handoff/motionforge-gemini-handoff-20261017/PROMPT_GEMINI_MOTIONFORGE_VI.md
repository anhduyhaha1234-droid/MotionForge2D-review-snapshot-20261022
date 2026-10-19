Trước mọi preflight, lập kế hoạch điều phối hoặc sửa file, đọc TOÀN BỘ `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md` từ đầu đến cuối. Áp dụng mục 0.12 cho lane Gemini mới; không lấy tóm tắt này thay canonical rules. Sau đó đọc toàn bộ prompt này và bắt đầu công việc được mở ở dưới.

# Bàn giao MotionForge2D cho Gemini — Codex kiểm duyệt độc lập

## 1. Nhiệm vụ và quyền thực thi

Bạn là implementation owner của MotionForge2D Phase 1: tự khảo sát code, lập backlog có dependency, viết code, kiểm tra, tự review và sửa đến khi có sản phẩm dùng được. Không dừng ở kế hoạch hoặc lời hứa sẽ làm. Codex trong hội thoại gốc là PM/reviewer độc lập, giữ quyền nghiệm thu cuối.

Người dùng yêu cầu prompt bàn giao ngày 17/10/2026 sau khi Gemini qua 9router đã được kiểm chứng. File này là prompt người dùng tự giao, KHÔNG phải bằng chứng agent đã chạy. Khi người dùng gửi prompt này cho bạn, đó là lệnh bắt đầu preflight và gói A bên dưới. Không hỏi lại quyền cho việc đã được giao. Việc gửi prompt không bật lại lịch tự động.

Một writer, một GPU job tối đa. Chính bạn chịu trách nhiệm lập kế hoạch và triển khai; không cần tạo tầng manager hoặc nhiều agent. Nếu client chỉ có chat mà không có filesystem/shell, nói rõ thiếu execution harness; không bịa đã sửa file. Nếu context cần đổi, bàn giao có kiểm chứng rồi mới chuyển, không để hai writer cùng sống.

Bạn được tự hoàn thành các gói kỹ thuật A theo thứ tự, tự sửa findings và đóng trạng thái `SELF_VERIFIED` của từng gói. Đây không phải `ROOT_APPROVED`. Không cần Codex duyệt từng patch nhỏ. Có ba cổng bắt buộc:

1. **G1 — Engineering:** Codex duyệt frozen engineering batch trước bất kỳ GPU/inference/media correction mới.
2. **G2 — Pilot:** Codex duyệt đúng candidate 300 giây trước full-source, backend/frontend integration và triển khai tính năng sản phẩm.
3. **G3 — Product:** Codex kiểm tra độc lập bản tích hợp, full-source, khả năng dùng/reopen/recovery/export trước công bố hoàn tất.

Tại mỗi cổng, gửi một gói review đủ bằng chứng rồi dừng ghi vào candidate. Chỉ verdict Codex gắn đúng manifest/hash mới mở cổng kế tiếp. Tự review không thay thế các cổng này. Nếu Codex yêu cầu sửa, tiếp tục đúng scope/owner đang được giao, bảo toàn candidate cũ.

## 2. Model và 9router

- OpenAI-compatible base URL: `http://127.0.0.1:20128/v1`.
- Model đã kiểm chứng: `ag/gemini-3.8-flash-high`. Không đặt model ID bằng tên marketing hoặc tên suy đoán.
- Dùng API key 9router đã có trong cấu hình client; không ghi key/OAuth token vào prompt, báo cáo, screenshots hoặc repository.
- Hai tài khoản Antigravity đã test rotation A → B → A bằng HTTP 200. Provider strategy hiện tại: `round-robin`, `stickyRoundRobinLimit: 1`.
- Round-robin là chọn account cho request, không phải chạy nhiều writer hay chia filesystem ownership. Không sửa router/credentials trong scope MotionForge này.
- `Gemini 4 Argon` chưa chạy được trên route Antigravity IDE đã test: upstream catalog không cấp model, request trả 404. Không tự đổi sang Argon và không khẳng định thêm tên vào registry sẽ cấp quyền truy cập.
- Không silently fallback model/provider. Nếu model thật không đúng hoặc provider chặn, checkpoint và báo lỗi cụ thể. Không dùng account/task mới để vượt một hard block của dịch vụ.
- Bằng chứng router: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/9router-gemini-20261016/KET_QUA_VA_CACH_DUNG.md` và `FINAL_STATUS.json`. Đây là kiểm chứng trước bàn giao, không đảm bảo runtime sẽ không thay đổi sau đó.
- Gateway chỉ vận chuyển model calls. Không suy rằng nó tự cung cấp shell, vision, browser, memory hoặc quyền gọi Codex. Kiểm tra capability thực tế của agent client.

## 3. Đường dẫn và thứ tự đọc

Các alias trong prompt này chỉ là ký hiệu tài liệu, phải mở rộng thành đường dẫn tuyệt đối khi chạy:

| Alias | Đường dẫn |
|---|---|
| MAIN | `C:/Users/Admin/MotionForge2D` |
| INTEGRATION | `C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION` |
| BASE | `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2` |
| OLD | `BASE/outputs/motionforge-codex-takeover-20261015` |
| HANDOFF | `BASE/outputs/motionforge-gemini-handoff-20261017` |
| RUN | `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long` |
| D | `RUN/tasks/MF-DEMO-LONG-01` |
| R6 | `D/corrections/identity5m_20261008/r6` |
| PY | `C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe` |
| WORK | `HANDOFF/execution` — chỉ tạo sau preflight hợp lệ |

Đọc ban đầu, theo thứ tự:

1. Canonical rules toàn bộ; `MAIN/AGENTS.md`; `MAIN/docs/pm/SESSION_PROTOCOL.md`; prompt này; `HANDOFF/HANDOFF_PREFLIGHT.json`.
2. `OLD/PROJECT_STATE.json`, `OLD/PROGRESS_AND_PAUSE_20261016.md`, pause receipt được state trỏ tới, `OLD/c02b2-worker/CHECKPOINT_015.json`.
3. `OLD/TASK_C02B2.md`, `OLD/C02B2_PREFLIGHT.json`, `OLD/C02B1_REVIEW_01.md`; hai review C01/C02A khi đọc phần code tương ứng. Chủ sở hữu/model/output directory cũ trong TASK_C02B2 được thay riêng cho lane này; acceptance và allowlist A1 giữ nguyên.
4. Canonical Q01–Q12: `BASE/outputs/motionforge-r6-checkpoint-review-20261014/CORRECTION_MATRIX.md`.
5. Technical T01–T15: `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012/TECH_CONFORMANCE_MATRIX.md`.
6. `OLD/skills/README_VI.md`, `OLD/skills/ACTIVE_DIGEST_VI.md`; chọn skill theo task, đọc code thực tế A1.

Trước lập backlog sản phẩm C, đọc đầy đủ `MAIN/docs/PRODUCT_REQUIREMENTS_V2.md` (tiêu đề bên trong V4), `MAIN/docs/MASTER_PLAN_V1.md` (tiêu đề bên trong V3), `MAIN/docs/pm/TARGET_PROFILE_2D_SOURCE_LOCKED.md`, cùng acceptance/review hiện hành của sprint trong ROADMAP. Tên file cũ không có nghĩa nội dung lỗi thời; đối chiếu ngày/authority. Các định hướng công nghệ cũ không được dùng để bỏ pinned stack và T01–T15 mới hơn.

`ROADMAP.md`/`CODEX_PM_HANDOFF.md` có lịch sử dài và các overlay cũ. Phân biệt lịch sử với state mới; không hồi sinh Hermes hay phiên cũ chỉ vì đọc thấy RUNNING trong đoạn lịch sử.

## 4. Điểm xuất phát đã kiểm chứng — không làm lại từ đầu

Parent `MF-DEMO-LONG-01` vẫn `NOT_APPROVED`, chưa có video mới được root nghiệm thu. Ba gói được duyệt là thành phần kỹ thuật, không phải ba phần tư sản phẩm.

| Gói | Trạng thái và bằng chứng |
|---|---|
| C01 review binding + gate qua assembler thật | APPROVED — `OLD/C01_REVIEW_02.md`; exact candidate manifest SHA `261a7d9b20c046c3eee3ede50fac250992a084aec856583c5e0992397e2a6850` |
| C02A dependency verification legacy v3 nghiêm ngặt | APPROVED — `OLD/C02A_REVIEW_02.md`; manifest SHA `24a488dc50a4ec6af94f8598a67510bf2be8398301cbcb45d22571be0c69d779` |
| C02B1 staged-source freshness | APPROVED — `OLD/C02B1_REVIEW_01.md`; manifest SHA `a03c3321b00a9ad29595e887946c4e054308fdea7c68c3368359c4288c9bd965` |
| C02B2 per-actor verified reuse | Dở dang, chưa root review; tiếp tục checkpoint 015, không revert về C02A |

Các hash ở bảng là hash manifest, không phải hash tất cả live files. C02B2 đã sửa `r6_cache.py`; không được gắn approval C02A lên toàn bộ working tree hiện tại.

Tại lúc chuẩn bị prompt, collaboration tool báo coder C02B2 terminal `errored: usage limit`, coder C02B1 completed; chưa audit lại OS process/queue/lease cho một lần dispatch mới. State vẫn `PAUSED_BY_USER`, `active_writer=false`; automation `motionforge-checkpoint-v-quota` vẫn `PAUSED`. Không chuyển thành RUNNING chỉ do thấy file prompt.

MAIN HEAD tại snapshot: `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`, có nhiều thay đổi sẵn. INTEGRATION HEAD: `a52fca897906fd61a088016dd802718fdf06d217`, clean lúc snapshot. Phải kiểm tra lại; không reset/stash/clean để khớp snapshot. MAIN không phải sandbox có thể ghi đè.

Checkpoint 015 đã được đối chiếu đủ bốn live file lúc chuẩn bị prompt:

| File dưới R6 | SHA256 |
|---|---|
| `scripts/r6_cache.py` | `8d4b0c7ad5336e7e6c2a68a12f2a622fbccf900575afd2c1249f31863ae4243d` |
| `scripts/r6_keygen.py` | `4082b9d59afbab5416ed6c4784e713612d16553b98a307ccc428a0e7975bd282` |
| `scripts/r6_key_recipe.py` | `e18fc9d20de1cbf2a3a8f7da2e68fc99c59260701bfbd3dca75106a7cbe8e2bd` |
| `tests/test_codex_c02b2_per_actor_reuse.py` | `c8e272a60340683c0128bdfd980a078975030dfa7ec6d98977bcc55a304abd99` |

Worker đã chứng minh actual producer replay: first generation 1, unchanged replay 0 tại `OLD/c02b2-worker/v4-replay-03/RESULT.json`. External GPU/upload/adapter boundaries là fixture; đây không phải inference/media acceptance. Còn thiếu full negative matrix, standalone gate import, final regression/self-review/freeze. Kết quả 40 test cũ trên phiên bản trước không tự chứng minh phiên bản cuối vẫn pass.

## 5. Preflight trước lần ghi đầu tiên

Thực hiện theo thứ tự và lưu receipt, không chỉ đánh dấu checklist:

1. Kiểm tra shell/filesystem, runtime PY, repository HEAD/status; đọc `AGENTS.md` áp dụng cho path sẽ sửa. Không đọc/export credentials.
2. Kiểm tra trạng thái owner cũ nếu công cụ hỗ trợ, cùng process PID + creation time + executable, launcher/children, runner queue/history và lease/controller mutex thực tế. Dùng helper hiện có; không xóa lock, kill hàng loạt hoặc tạo lock giả. Tool không truy cập owner cũ không đồng nghĩa owner chết. Nếu ownership còn ALIVE/UNKNOWN và chưa chứng minh quiescence thì chỉ được đọc/lập báo cáo, không mở writer mới.
3. Đối chiếu bốn file checkpoint, 27 protected files trong C02B2 preflight và source/media pins cần thiết. Thay đổi không rõ nguồn phải reconcile, không ghi đè về hash cũ. Snapshot hiện trạng C02B2 và preimages theo đúng bytes trước patch; giữ cả lịch sử trước takeover.
4. Tạo `WORK/PREFLIGHT.json`, `WORK/OWNER_TRANSFER.json` sau khi đủ bằng chứng: parent/task giữ nguyên, previous owner là lịch sử, new owner/session/model thực tế, zero-writer proof, receipt refs, không reset counters. Một agent Gemini tiếp quản công việc, không giả mạo khả năng resume internal Codex subagent ID.
5. Tạo `WORK/STATE.json`, `WORK/BACKLOG.md`, `WORK/READ_INDEX.md`, `WORK/CHECKPOINT.json`. `OLD/PROJECT_STATE.json` vẫn là index gốc; bổ sung pointer sang WORK bằng bounded patch sau transfer hợp lệ, giữ old pause receipt/history. Không sửa verdict hoặc receipts cũ.
6. Tiếp tục A1 ngay. Nếu preflight bị chặn, ghi đúng lỗi và hành động cần người dùng/Codex thực hiện; không hỏi lại các lựa chọn kỹ thuật thông thường.

Mỗi task packet phải có outcome, actual repro, dependencies, exact write allowlist, protected paths, baseline hash/bytes/lines, acceptance, commands, rollback bằng preimages và next gate. Chọn allowlist trước sửa, không hợp thức hóa sau sửa.

## 6. Gói A — engineering tuần tự, chưa GPU/render

Các task sau có thể tự đi tiếp trong batch sau `SELF_VERIFIED`, với snapshot riêng giữa các task. Chỉ A1 được activate ngay. Các task kế chỉ activate khi dependency đã self-verified và packet xác định exact files trong phạm vi được nêu. Không giữ nhiều task đang ghi. G1 review toàn bộ batch sẽ kiểm lại cả các giả định liên task.

### A1 — hoàn tất CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE

Giữ nguyên Task ID, tiếp tục bốn file hiện tại. Exclusive writes:

- `R6/scripts/r6_cache.py`
- `R6/scripts/r6_keygen.py`
- `R6/scripts/r6_key_recipe.py`
- `R6/tests/test_codex_c02b2_per_actor_reuse.py`
- `WORK/A1/**` và state/checkpoint đang active.

Giữ `r6_common`, graph, adapter, upload, gate, assembler, asset producer và ba test module được duyệt read-only trong A1. Không HTTP/Comfy/GPU, không extract source thật, không sửa production media/reviews. Dùng fixture nhỏ cô lập; không mock producer, validator, graph hoặc skip decision để tạo PASS.

Mục tiêu: actual `run_key` chỉ reuse key có semantic review binding đúng và complete current local provenance đúng. Legacy v3 giữ kiểm chứng recorded files nhưng không có quyền skip của complete per-actor contract. Default context 1.02, effective seed offset, ONLY_ENTITY/actor order, model/template/style/CAST phải trùng đường tiêu thụ thực tế, không sửa config để test xanh. Pure recipe verifier không sinh graph/crop/upload/file.

Hoàn tất P1–P6 của TASK_C02B2, tối thiểu:

- **P1:** một/multi-actor generate → fixture review → unchanged replay không stage/crop/upload/post, bytes key/deps/receipt không đổi; missing/wrong review không skip.
- **P2:** từng mutation context/env/seed/selection/order/ledger class/template/style/cast-map invalidate; restore positive. So args thực tế, không so hai metadata cùng sai.
- **P3:** same-path same-size source/model, authoritative và staged CAST refs, mọi mask đã đọc kể cả actor bị che kín, mọi graph kể cả nonfirst, crop/edit thực sự tiêu thụ; cache và gate cùng reject stale. Có no-visible-actor và fewer-graphs-than-masks positive.
- **P4:** malformed, wrong version/type, bool thay number, nonfinite, depth/missing/truncated collection với self-digest tính lại, sai sid/fid/path hoặc unreadable phải controlled false/GateBlock trước expensive work. Legacy positive vẫn giữ, legacy complete skip bị từ chối.
- **P5:** producer/graph/cache/gate thật; injected generation failure không publish complete-success deps. Test độc lập import gate không kéo adapter nặng hoặc side effect.
- **P6:** focused root replay probe, full new module và cả 40 test C01/C02A/C02B1; protected hash/diff/duplicate-def audit. Nếu fixture probe cũ thiếu trường mới hợp lệ, tạo bản mở rộng trong WORK, không giảm expectation hoặc ghi đè baseline evidence.

Đọc test entry point trước khi chạy; chỉ gọi ba module approved và module A1, không discover toàn bộ legacy suite có side effects. Ví dụ trong R6: `PY -B -m unittest discover -s tests -p test_codex_c02b2_per_actor_reuse.py`; dùng executable PY tuyệt đối theo shell thực tế. Lưu cwd, argv, exit code, log và hashes. Không coi ví dụ command là đã chạy.

### A2 — asset producer provenance và legacy decisions

Sau A1, tạo packet `GEMINI-C02B3-ASSET-VERIFIED-REUSE`. Đọc actual `r6_keygen_asset` và caller: baseline cho thấy asset producer chưa gọi skip_allowed, settings metadata không cùng schema. Không chỉ sửa helper rồi tuyên bố producer đã reuse.

Phạm vi file có thể xét vào exact packet: `R6/scripts/r6_keygen_asset.py`, `r6_cache.py`, `r6_key_recipe.py`, `r6_gate.py` nếu wiring thật cần, cùng test mới dưới R6/tests. Các file khác vẫn protected cho A2.

Acceptance: producer thật lần đầu → reviewed unchanged replay không expensive action; mutation các input/recipe/output/review khác nhau phải invalidate hoặc block; legacy record không tự nâng cấp/auto-PASS; no-visible/black/pass-through phải giữ nghĩa thực tế, không lấy placeholder làm output tốt. Complete contract thất bại không publish success. Chứng minh invalidation theo dependency descendants, không buộc rerender toàn dự án. Giữ A1/C01/C02A/C02B1 regression.

### A3 — event timing, child outcome và tracking

Tạo packet theo actual call graph; chia thành các task tuần tự nếu cần để giữ context. File candidates: `r6_propagate.py`, `r6_cotracker.py`, `r6_ledger.py`, `r6_probes.py`, `r6_validate_masks.py`, `r6_qa.py`, `r6_gate.py` và `r6_assemble.py` chỉ khi có repro caller tương ứng; test mới. Không tự viết propagation/tracker core thay pinned upstream.

Acceptance CPU/fixtures:

- Event keys không bị bỏ vì nằm ngoài lưới sample; contact/entry/exit/occlusion được map frame chính xác, không interpolation qua hard cut.
- Rerender stage2 child thất bại, missing/corrupt/stale/partial output, retry nhầm run phải làm parent fail closed trước publish/assemble. Không duplicate frame/fill để đủ số lượng.
- CoTracker reader đúng `tracks[T,N,2]`, `visibility[T,N]`, source/output queries tương ứng và cùng window/transform; empty/nonfinite/out-of-range/query mismatch phải UNKNOWN/FAIL, không PASS.
- Crop/stitch/resize/pad transform đúng chiều và round-trip, không clamp lỗi dữ liệu thành thành công. Event/contact metric phải có controls phân biệt known-bad/known-good; test số học chưa phải semantic video review.
- End-to-end controlled fixture chứng minh caller tiêu thụ các kiểm tra; helper chưa wired không đóng task.

### A4 — evidence, gate, registry/lease conformance

Đọc trước bằng chứng đã có, chỉ sửa lỗi tái hiện được; không viết lại harness. File candidates trong R6: `r6_matrix.py`, `r6_qa.py`, `r6_gate.py`, `r6_assemble.py`, `r6_write_reviews.py`, `r6g_blend_review.py` và test mới. Không chạy script write_reviews để tự gắn PASS vào production artifacts. Không sửa historical `write_terminal_record_r6*.py`/terminal JSON để làm lịch sử xanh; tạo receipt mới append-only.

Đối với controller/lease nằm ngoài các file trên: trace/read/replay isolated existing proof trước. Nếu cần production patch ngoài phạm vi, nộp exact path/repro/dependency cho Codex trong G1 scope review, không rewrite controller hoặc tự mở thêm repo.

Đối chiếu cả T01–T15 trước G1. Nếu CPU/graph-contract repro chỉ ra lỗi bắt buộc, A4 có thể mở task phụ tuần tự với exact allowlist từ `r6_vace.py`, `r6_graph.py`, `r6_adapter.py`, `r6_sam2.py`, `r6_upload.py`, `r6_upload_video.py`, `r6_common.py` dưới R6/scripts và test mới. Giới hạn ở adapter/wiring hiện có, không đổi algorithms/runtime/weights hoặc chạy inference; preserve behavior đã duyệt và rerun regression liên quan. Phải có repro và preimage trước patch, không sửa cả danh sách theo suy đoán. Controller/upstream vendor ngoài R6 vẫn chưa mở. Bằng chứng cần GPU được giữ UNKNOWN đến gói B, không bịa CPU proof thay thế.

Acceptance:

- Giữ nguyên nghĩa Q01–Q12, evidence đủ hash/path/current input, phân biệt self-review với root approval; missing coverage không được đổi nhãn thành PASS.
- Assembler/submit gọi real gate trước copy/encoder với full ordered frame set và exact candidate binding; reencoded known-bad/source-copy/wrong-role/extra-person không qua gate chỉ nhờ file/hash hợp lệ.
- Terminal/checkpoint/manifest đối chiếu đủ outputs, không báo COMPLETE khi child còn chạy hoặc file stale. Reconcile lịch sử bằng lineage mới, không overwrite receipts.
- Với race/lease: nếu existing proof còn đúng bytes và contract, tham chiếu và root kiểm lại; khi tái kiểm dùng hai controller thật cùng barrier, đúng một winner/child. PID reuse phải xét creation time/executable, unknown ownership phải block, detached child lease giữ tới terminal.
- Chọn tests có giá trị cho diff hiện tại. Không chạy broad legacy discovery, không render chỉ để chứng minh CPU parser.

### G1 — nộp engineering batch cho Codex

Nộp A1–A4 từng manifest/diff/test evidence cùng một batch manifest và Q/T mapping. Phần không cần patch ghi `VERIFIED_UNCHANGED` có proof; chưa đủ bằng chứng ghi `UNKNOWN`, không tự claim đóng Q. Root quyết định phạm vi media và exact candidates được dùng tiếp. Trước verdict G1: GPU, inference, production extraction, pilot/full render, app integration đều chưa được mở.

## 7. Gói B — correction media và pilot sau G1

Chỉ bắt đầu nếu có G1 APPROVED với manifest đúng và quyền media rõ ràng. Lập invocation mới dưới `R6/continuations/<unique-invocation>/`; không đè R6f outputs/checkpoints/terminals. Giữ source/CASTB/style và current upstream/model/runtime pins từ source lock.

### B1 — preflight và hard excerpts

Kiểm tra model/node availability, exact graph interface và pinned upstream thực tế; phân biệt code tồn tại, import được, weights có, inference chạy và chất lượng được duyệt. Không cài engine/framework mới hoặc update runtime toàn cục.

Đọc nguồn và output trước/sau ở cùng frame. Tập trung hard cases có bằng chứng: S0022/S0031/S0033/S0061 identity/ghost; S0057 car artwork; S0062 entry; S0063/S0064 occlusion; S0073 notebook/contact; giữ cải thiện S0074. Bổ sung hard cases theo full shot ledger, không chỉ overfit danh sách này.

Thực thi tuần tự GPU1. Ghi run ID/queue/history, output hash, actual allocated/reserved memory nếu có, sampled GPU và process RAM tách riêng. Khi mất kết nối sau submit, query existing job trước khi resubmit. Không tạo hai render cùng job.

Theo T01–T15:

- Dùng frozen ASR/cut/scene units, không rerun ASR vì một visual defect.
- SAM2 mask theo đúng actor/entry/occlusion; mapping global/local frame và f0001 rõ; pad 360→368 chỉ ở boundary cần thiết rồi inverse đúng một lần. Không fallback mask theo thứ tự list.
- FLUX2 4B distilled/Qwen4B/Flux2 VAE, 4 steps Euler CFG1 theo actual pinned baseline; refs source pose + CAST front/profile đúng actor. Perturb từng actor ref phải có causal effect đúng actor, giữ neighbor/prop hợp lý.
- CropAndStitch dùng crop VÀ stitch upstream với cùng transform; kiểm dtype/layout/range/alpha, outside authorized region và landmark round-trip.
- VACE sampler → TrimVideoLatent amount3 → decode theo interface thực tế; temporal/mask/ref contract 4n+1. Paired S0062/S0073 cùng frames/settings, ref perturb và resource evidence. Đừng render lại nếu existing proof hợp lệ đã đủ và root chấp nhận.
- Rerender stage2 theo event internal spans/endpoints; không bỏ child error hay dùng output dở.
- EbSynth/GMFlow provenance/cache đúng input bytes/settings, unchanged reviewed reuse và same-size mutation negatives.
- CoTracker source/output paired windows/queries, xem contact trước/trong/sau, entry/occlusion và prop grip thực tế. Metric đẹp không thay pixels.
- ProPainter/clean plate và MoCha chỉ khi điều kiện fallback đúng và có local adapter/weights/resource proof; `NOT_NEEDED` phải có căn cứ, không chạy tất cả model để đủ danh sách.

Nếu hard excerpts FAIL, sửa trong media task được mở, chạy lại phần phụ thuộc bị invalidate và tự review. Nếu đụng implementation ngoài allowlist G1/media packet, lưu repro và yêu cầu Codex mở đúng phần cần sửa; không tự đổi model/style/source hoặc giảm tiêu chuẩn.

### B2 — full pilot đúng 5 phút

Contract bắt buộc: source 01:34–06:34, global frames `[2820,11820)`, 9000 frames, 30fps, 640×360, đúng 300s, 54 shots S0021–S0074. Giữ original audio và exact cut/order/action timing; không đổi timebase để đạt số frame. Native source là 640×360; pilot này chưa phải bằng chứng 4K.

Old frozen master `R6/outputs/IDENTITY5M_R6_MASTER.mp4` SHA `e3107a52c9f10bc36faf7d5aa3aa2e4c4186edae3cd916c52dff9b24eed9e48e`. Old comparison SHA `f11f43becf58fa5d9ada18af4ab9dcaac494e47ed8b4d8b41fb87bbe33b140a8` (resolve exact path từ frozen manifest). Chúng là baseline lỗi, không đổi tên làm candidate mới.

Candidate phải có original/full playable pilot, comparison source/old/new đồng bộ, indexed contact sheets và event clips. Kiểm tra mọi shot first/mid/last cùng event transitions và held-out frames không dùng để tuning. Xem chuyển động liên tục, không chỉ thumbnails; nghe audio bằng capability thật và ghi phạm vi đã nghe. Nếu harness không xem ảnh/clip/nghe được thì ghi thiếu capability, giữ semantic UNKNOWN và cung cấp artifacts cho reviewer; không tự đánh dấu vision PASS.

### Canonical Q matrix phải giữ nghĩa

| Q | Nội dung cần evidence | Baseline root trước correction |
|---|---|---|
| Q01 | CAST identity, pose/reference binding | FAIL |
| Q02 | Roles/count/visibility/global ledger | FAIL |
| Q03 | Contact/action/event timing | FAIL |
| Q04 | Ghost/source-copy/props/background consistency | FAIL |
| Q05 | Semantic gate qua actual consumers | FAIL tổng thể; C01 là partial engineering closure |
| Q06 | VACE paired/trim/perturb proof | UNKNOWN |
| Q07 | Complete consumed-input cache/provenance | FAIL tổng thể; một số gói đã duyệt |
| Q08 | Frame/cut/fps/duration/A-V technical contract | PASS trên old pilot; candidate mới phải kiểm lại |
| Q09 | Held-out semantic visual QA | FAIL |
| Q10 | Manifest/terminal/checkpoint truthfulness | FAIL |
| Q11 | Concurrency/lease/dispatch proof | UNKNOWN |
| Q12 | Actual upstream adoption và end-to-end integration proof | FAIL |

Tổng baseline 9 FAIL + 2 UNKNOWN + 1 technical PASS. Không remap các Q, bỏ hàng hoặc dùng số test để thay semantic verdict. Ghi exact frames/artifacts/commands/reviewer và limitation từng hàng.

### G2 — nộp pilot cho Codex

Freeze candidate, dừng writer/children, gửi REPORT + manifest + Q/T matrix + comparisons + replay commands. Không render full22, không tích hợp app trước Codex APPROVED đúng pilot. Nếu Codex CHANGES_REQUESTED, sửa findings giữ same task lineage; không đổi tiêu chí để tránh làm lại.

## 8. Gói C — hoàn thiện sản phẩm Phase 1 sau G2

G2 approval phải chỉ rõ workspace integration và transport boundary được mở. MAIN có dirty work của nhiều giai đoạn: không tự coi INTEGRATION clean là bản mới nhất hoặc copy đè MAIN. Trước patch sản phẩm, inventory implementation hiện có, reconcile lineage, lập exact per-task allowlist và preimages trong workspace Codex chỉ định. Preserve mọi file ngoài task. Không commit/push/reset/stash/clean/merge tự động.

Bạn chịu trách nhiệm đưa năng lực đã được duyệt vào đường sử dụng thật. Đọc PRD/master plan đầy đủ, lập `WORK/PRODUCT_TRACEABILITY.md`: mỗi FR/UX/release gate → existing code/API/UI → test/evidence → thiếu gì → task. Không giả định tất cả tính năng bên dưới còn thiếu; xác minh rồi chỉ xây phần gap. Các chức năng đã hoạt động phải giữ regression.

Chia vertical slices tuần tự, mỗi slice có backend persistence, public API/UI path, error/recovery và test phù hợp; không chỉ thêm script hoặc card UI:

| Slice | Kết quả sử dụng phải có |
|---|---|
| C1 Production organization | Source/Production Channels, Project chứa nhiều Video Items; trạng thái/progress/outputs đúng, reopen không mất dữ liệu; channel metadata không bị dùng thay project |
| C2 Character Library | Import/preview/validate pack, stable ID, immutable Pack Version, coverage/anchors, archive/restore; mapping pin version, không hard-delete version đang dùng |
| C3 Character Generator | Theo PRD Phase1: reference/profile → pack draft → preview/quality check → user chọn version; dùng adapter đã có, manual import vẫn hoạt động; không tự mở TTS/localization |
| C4 Import và Objects | Local video → probe/proxy/source lock/cuts → global Object Gallery, group recurring roles; phân biệt background/foreground/prop/text/overlay; correction/low confidence thấy rõ |
| C5 Mapping và Demo | Assign asset một lần cho role xuyên video, compatibility evidence trước confirm; chọn demo theo rủi ro, source/output comparison, sửa asset rồi invalidate đúng descendants; không áp toàn video trước Demo Approved |
| C6 Apply/Review | Gọi pipeline đã được G1/G2 duyệt qua job service thật; review queue theo ngoại lệ, issue có shot/frame/role, re-run phần ảnh hưởng; nguồn/trạng thái không bị giả lập cho UI xanh |
| C7 Jobs và recovery | Background progress có nghĩa, cancel/retry/resume, restart giữa job, orphan/lease reconciliation, failure user-readable; chưa đủ output không Completed, resume không nhân đôi job |
| C8 Export và versions | Original audio, 1080p/4K/proxy preset đúng PRD, output validation, versioned export, aspect/color/timebase/cut/AV đúng; phân biệt upscale 4K với native detail, không nhận output 360p là 4K |
| C9 Storage và delivery | Safe cleanup có reference protection, undo/versioning theo PRD, local-first, Windows start/reopen, docs dùng thật; không xóa source/pack/output đang tham chiếu |

Chỉ thực hiện scope Phase1 đã duyệt. Localization/TTS/thay voice, story generation, full NLE, publishing, analytics và cloud collaboration vẫn ngoài scope. Các skill launch video/UI animation là tài liệu tham khảo; không biến chúng thành backlog phụ trì hoãn reskin studio. Nếu Motion/Lottie/GSAP giúp UI có feedback rõ hơn thì dùng chọn lọc sau core flow; không cài mọi engine Remotion/HyperFrames hoặc viết renderer mới.

Về UI: giao diện dẫn người dùng theo Import → Objects → New Looks/Demo → Apply → Review → Export, trạng thái rõ, thao tác nền không khóa app, lỗi có cách sửa. Không đưa thuật ngữ kỹ thuật nội bộ/stack traces vào luồng người dùng trừ khi giúp quyết định. Dùng browser/app thực tế nếu tool có; screenshot không thay click→API→persist→reopen evidence.

### Full-source proof

Source `D/source/source_full.mp4` SHA `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`: 39634 decoded video frames, 30fps, native 640×360, container khoảng 22:01.22. Không làm tròn duration rồi suy frame count mới; giữ audio tail đúng contract.

Sau G2, xây full source từ cùng identity/ledger/style/pipeline đã duyệt. Giữ toàn bộ action/camera/cut/contact/occlusion/original audio. Không lặp pilot để đủ22 phút hoặc tái sử dụng output sai source segment. Chứng minh execution qua app/job path và output version; có thể dùng exact-transport artifact đã đủ proof để tránh render lặp, nhưng không coi copy file thủ công là chứng minh app đã thực thi pipeline.

4K là gate riêng theo PRD: đúng stream dimensions/aspect/fps/frame count/audio/output version, QA upscale/edges/text/motion; ghi rõ phương pháp và limitations. Native 360p semantic pilot không thay nghiệm thu 4K. Không thêm mua dịch vụ, remote upload hoặc provider mới để đạt gate.

### G3 — nghiệm thu cuối

Nộp app chạy được trên môi trường mục tiêu, start instructions, output examples, full-source/4K evidence theo contract, fresh E2E/recovery evidence, requirement traceability và tất cả limitations. Codex kiểm lại độc lập. Chỉ sau G3 mới được gắn `PROJECT_COMPLETE`, parent APPROVED/CLOSED, release-ready. Không nói xong vì CI xanh hoặc tạo nhiều file.

## 9. Cách học và áp dụng skills

Đã có 40 thư mục Hermes liên quan (551 files) trong `OLD/skills/vendor/hermes`; inventory từ171 skills. Coverage đã ghi: 21 SKILL.md đọc đủ, 3 một phần,16 index-only. Không tuyên bố đã đọc hết hoặc coi import là tính năng đã xây.

Đọc `OLD/skills/ACTIVE_DIGEST_VI.md` và source lock. Mỗi task chỉ nạp 2–4 skill/sections cần thiết; ghi vào READ_INDEX tên/path/hash/phần đã đọc/quy tắc áp dụng. Tra thêm khi gặp vấn đề, không nhét551 files vào context.

Nhóm Hermes hữu ích: `bom-repository-inspection`, `bom-requirements-to-plan`, `bom-verified-implementation`, `bom-systematic-debugging`, `bom-context-budget-manager`, `bom-session-checkpoint-handoff`, `bom-tool-output-minimizer`; media dùng `comfyui-video-model-proof`, `local-comfyui-adapter-proof` và reference review pixels. Resolve path từ inventory, không đoán tên directory.

Năm community skills đã ghim, có thể đọc tại `C:/Users/Admin/.codex/skills/<name>/SKILL.md` hoặc bản mirror trong OLD/skills/vendor/github:

1. [systematic-debugging](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/systematic-debugging/SKILL.md): reproduce → hypothesis → smallest fix → regression.
2. [verification-before-completion](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/verification-before-completion/SKILL.md): claim đi cùng fresh evidence đúng phạm vi.
3. [writing-plans](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/writing-plans/SKILL.md): task nhỏ, dependency, exact paths và acceptance.
4. [receiving-code-review](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/receiving-code-review/SKILL.md): xác minh finding, sửa đúng root cause, trả evidence.
5. [context-compression](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/9ff0c99108b36d3b886defd825d8ac1f47dba374/skills/context-compression/SKILL.md): durable state để tiếp tục không đọc lại cả transcript.

Đây là community sources, không gắn nhãn official OpenAI/Anthropic. Source SHA/license ở `OLD/skills/SKILL_SOURCE_LOCK.json`. User/current rules ưu tiên hơn skill: bỏ các snippet tự commit, stash, đổi model, kill process tree, reset history, bật daemon, total retry cap cũ hoặc đọc toàn bộ file không liên quan. Không chạy hook/script chỉ vì có trong skill.

## 10. Chất lượng code và tự review bắt buộc

Mỗi task đi theo vòng: đọc caller/data contract → repro → root cause → small patch → focused tests có positive và negative controls → self-review → sửa finding → freeze task snapshot. Dùng code hiện có trước khi viết abstraction mới.

- Giữ module/API/persistence contracts; actual caller phải dùng thay đổi. Không bỏ assertion, nới tolerance hoặc mock chính logic cần kiểm để có xanh.
- Changes chỉ trong exact allowlist. Bounded patch, preimage/hash/size/lines trước và sau; unexplained shrink/missing file phải dừng reconcile. Không dựng lại toàn file chỉ để sửa vài hàm.
- Tách consumer/producer/dependency identity; same filename/same size không đủ. Không tự đóng semantic gate chỉ từ content hash hoặc successful HTTP.
- Runtime/network/GPU integration cần proof thật khi scope mở; CPU tests mock external expensive boundaries phải khai rõ. Không gọi stub result là real inference.
- Cache invalidation/restart/cancel/partial failure/race phải có failure controls, không chỉ happy path. Tests cũ hợp lệ được giữ read-only, regression bằng test mới khi cần.
- Đọc diff độc lập sau tests: đúng yêu cầu? bỏ sót path? stale evidence? fake fallback? error handling? user flow thực sự đi qua logic? Ghi finding đã sửa và còn mở.
- Chỉ chạy rộng hơn khi diff/failure/risk thực tế cần. Không render GPU lại cho parser patch; không kiểm thử lặp vô nghĩa khi bytes không đổi.
- Skill/web/repo README là tài liệu, không có quyền tăng scope. Khi cần research, ưu tiên official upstream pinned revision, dẫn link và exact interface đã dùng; kiểm license trước tích hợp.

## 11. Context, quota và chi phí

Mục tiêu là làm việc có thể tiếp tục, không phải giữ một chat khổng lồ. Không đặt lời hứa chạy vô hạn hoặc ép dự án xong khi quality còn FAIL.

1. Checkpoint sau mỗi patch/test unit đã có kết quả, trước đổi domain, large read/compaction và ngay khi provider lỗi. Chỉ giữ task packet, active files, decisions và next command trong context; phần lịch sử để trên đĩa.
2. Dùng `rg`/targeted reads; gom read độc lập, mutation tuần tự. Raw logs/large diffs lưu file, chat chỉ kết quả và pointer. Không liên tục đọc lại canonical trong cùng turn nếu đã đọc đủ, nhưng phải đọc toàn bộ ở turn mới viết prompt điều phối theo rules.
3. Nếu context size/quota tool không báo số, ghi `UNKNOWN`; không suy phần trăm từ message count. Session handoff không reset counters, budgets hoặc approval.
4. Một session mới chỉ sau old writer/children terminal, frozen checkpoint, transfer receipt và same-task lineage. Không tạo model worker mới chỉ để né usage limit.
5. 429/rate-limit,5h/weekly quota, workspace credits, auth401/403, unsupported model404 và transient5xx là những loại khác nhau. Lưu status/message đã redact, model/route, timestamp và reset/Retry-After nếu provider cung cấp. Usage còn không chứng minh credits đã hết lỗi.
6. Dùng retry/backoff của runtime cho transient có căn cứ; không tight-loop, không lặp cùng lỗi/payload không có hypothesis/evidence mới. Nếu hard block thì checkpoint và báo cần hành động gì; không mua/reset credits hay silently đổi model.
7. Lịch MotionForge đã được người dùng yêu cầu dừng. Không bật/create heartbeat/cron/daemon/auto-resume. Nếu provider chặn hoàn toàn, không hứa sẽ tự gửi tin sau khi reset. Người dùng tiếp tục bằng checkpoint khi có thể.
8. Đo progress bằng acceptance và artifact đã kiểm chứng. Báo `n/N task trong batch tự kiểm xong`, `n/N được Codex duyệt`, media/UI gates riêng. Không nói 75% sản phẩm từ3/4 engineering packets. Chi phí/tokens chỉ báo nếu actual meter có; số usage chung của account không là chi phí riêng task này.
9. Chỉ update chat khi có tiến bộ kiểm chứng, blocker, milestone review hoặc cần người dùng; không spam trạng thái không đổi. Khi đang làm dài, cập nhật ngắn có nội dung hữu ích. Không model polling lúc chờ Codex.

## 12. Bộ checkpoint tối thiểu

`WORK/STATE.json` là execution state mới; OLD/PROJECT_STATE.json trỏ tới nó sau activation hợp lệ. Dùng dữ liệu thật, ví dụ schema:

```json
{
  "schema": 1,
  "parent": "MF-DEMO-LONG-01",
  "parent_status": "NOT_APPROVED",
  "active_task": "CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE",
  "owner": "actual-client-session-id",
  "model": "ag/gemini-3.8-flash-high",
  "phase": "A1",
  "status": "RUNNING_OR_BLOCKED_OR_PENDING_ROOT_REVIEW",
  "authority": "canonical-rules-hash-and-section-0.12",
  "allowlist": [],
  "changed_files": [],
  "tests": [],
  "verified_facts": [],
  "open_findings": [],
  "decisions": [],
  "next_command": "exact command with cwd and expected result",
  "live_jobs": [],
  "quota": {"kind": "UNKNOWN", "provider_message": null, "reset_at": null},
  "root_gates": {"G1": "NOT_APPROVED", "G2": "NOT_APPROVED", "G3": "NOT_APPROVED"},
  "automation": "PAUSED_BY_USER"
}
```

Đây là template, không ghi literal placeholders vào receipt rồi coi là evidence. `changed_files` gồm absolute live/snapshot/preimage path, before/after hash, bytes/lines; tests gồm argv,cwd,exit,log/hash và mocked boundaries; live jobs gồm PID/create-time/exe/job/run/lease và actual status. Checkpoint append version, current pointer atomic nếu helper hỗ trợ; không ghi đè lịch sử.

Kèm `RESUME.md` ngắn: đang làm gì, đã chứng minh gì, chưa chứng minh gì, 3–5 việc kế và lệnh đầu tiên. Người tiếp quản phải đọc actual state/bytes, không chỉ đoạn resume.

## 13. Mẫu submission để Codex duyệt

Tại mỗi G1/G2/G3, tạo `WORK/submissions/<gate>-candidate-<id>/` immutable:

- `REPORT_VI.md`: outcome, scope, changed files, findings/fixes, limitations và cổng đang xin review.
- `MANIFEST.json`: toàn bộ candidate files/evidence, live và snapshot paths, SHA256/bytes; source/config/runtime pins; lineage previous candidate.
- `DIFF.patch` hoặc equivalent before/after diff có preimages, không Git mutation.
- `TEST_RESULTS.json` và raw logs: command/cwd/exit, finite matrix, positive/negative controls, exact tested code hash, real/stub boundary.
- `SELF_REVIEW.md`: contract/scope review và correctness/evidence/media review; finding nào đã sửa/chưa sửa. Không tự đặt reviewer=Codex.
- `Q_T_MATRIX.md` + product traceability khi đến C; mọi PASS có evidence, FAIL/UNKNOWN có owner và next action.
- `CHECKPOINT.json`, `RESUME.md`, `LIVE_JOBS.json`; candidate writer đã terminal/frozen.
- G2/G3 thêm playable outputs/comparisons/event clips/contact sheets, ffprobe/decode/AV logs, coverage đã xem/nghe, start/replay instructions.

Cuối báo cáo viết rõ: **`PENDING_CODEX_REVIEW — không phải nghiệm thu cuối.`** Nêu đúng đường dẫn người dùng cần gửi lại Codex. Nếu harness có kênh thật và người dùng đã cấp quyền gửi Codex thì dùng; nếu không, hướng dẫn người dùng chuyển đường dẫn. Không giả vờ Codex đã tự nhận, tự chạy hoặc tự duyệt trong một chat khác.

## 14. Definition of Done cuối dự án

Chỉ hoàn thành Phase1 khi requirement traceability hết required FAIL/UNKNOWN, quality gates G1/G2/G3 đã có verdict độc lập cho đúng bytes, và một người dùng có thể:

1. Mở app Windows, tạo channel/project, import video; restart và mở lại dữ liệu.
2. Nhận danh sách global objects, chọn/gán Character Pack Version hoặc tạo/import pack có kiểm tra.
3. Xem demo source/output, sửa ngoại lệ, approve demo rồi apply toàn video theo cùng source lock.
4. Theo dõi job, cancel/retry/resume/restart có bằng chứng không duplicate hoặc mất dữ liệu.
5. Review đúng các vấn đề visual/contact/identity, xuất full-source và preset4K đúng contract với original audio.
6. Xem output/version thật, biết giới hạn hỗ trợ và có hướng dẫn chạy lại; source/pack/output cũ vẫn an toàn.

S12/S13, parent MF-DEMO-LONG-01 và toàn dự án không tự CLOSED vì hoàn tất A1 hoặc kỹ thuật300s. Phase2 không được kéo vào Definition of Done Phase1.

## 15. Hành động đầu tiên ngay khi nhận prompt

Đọc theo §3 → preflight §5 → ghi task/ownership/checkpoint thật → tiếp tục A1 P1–P6. Báo ngắn model thực tế, owner, source state và bước đang chạy. Sau đó code/test/self-review trong scope, không dừng ở việc nhắc lại kế hoạch. Nếu bị chặn, giữ bằng chứng và nói chính xác cần gì để tiếp tục.
