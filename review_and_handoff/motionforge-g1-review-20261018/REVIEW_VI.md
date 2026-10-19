**Verdict G1: CHANGES_REQUESTED — candidate `g1-candidate-01` chưa được duyệt.**

Đánh giá theo canonical rules §0.12 và acceptance A1–A4 trong prompt bàn giao. Có **7 finding P1 và 2 finding P2**. Không có approval GPU/pilot/full-source/app integration phát sinh từ verdict này. Không thay rules sang §0.13 trong lần review này.

Tôi đã chạy lại độc lập **76/76 test, exit 0**; unittest báo 8.435 giây, cả subprocess 10.235 giây. Kết quả Gemini nêu là có thật, nhưng test hiện có không phủ đủ lỗi bên dưới. Không có GPU inference, render video hoặc sửa production source/test trong review.

Candidate manifest SHA-256: `604fd9065ff647870cafc7925514c3f82278aad77b565cb7f53eade29de7c31b`. Root snapshot giữ đủ **14/14 hash** đã nộp và kiểm lại sau tests vẫn khớp. **13/14 live file** khớp lúc chụp; gate đã đổi. Gate candidate được phục hồi bằng bản sao byte-exact từ A4 probe, hash `944eea8b6a1624cbb2983495fba5d2ff00cccb23460843f67987155cf664c0a2`; live hash `2767895e5ca1705c1dcff40e281e237b9334df6f0451c81f674656e9c41f42cc`. Không chạy suite trên live gate rồi gọi đó là G1.

Các dependency ngoài 14-file manifest được chụp riêng theo thời điểm review, không tự coi là đã được manifest submission khóa. Xem [CANDIDATE_IDENTITY.json](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/CANDIDATE_IDENTITY.json), [POST_TEST_HASH_CHECK.json](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/POST_TEST_HASH_CHECK.json) và [POST_SUBMISSION_GATE_DIFF.patch](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/POST_SUBMISSION_GATE_DIFF.patch).

**Findings — ưu tiên sửa trước khi nộp lại**

**G1-R01 [P1] — Asset provenance vẫn chấp nhận thiếu consumed input và graph sai sampler**

Vị trí: [scripts\r6_cache.py:343](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cache.py:343), [scripts\r6_cache.py:365](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cache.py:365), [scripts\r6_cache.py:456](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cache.py:456).

Thực tế/repro: Bỏ consumed.grey_ref rồi tính lại self-digest: verify_deps trả (True, ok). Đổi SAMPLER của graph sang heun, cập nhật graph hash và self-digest trong khi recipe vẫn euler: verifier vẫn trả (True, ok). Control nguyên bản cũng PASS.

Kỳ vọng: Bản ghi incomplete hoặc graph không khớp effective recipe phải bị từ chối, kể cả hash/self-digest nhất quán. R1/R2 grey reference đang được graph tiêu thụ nên không được coi là optional.

Tác động: Claim Q07/T07 complete không đúng. Đây là bypass tại dependency verifier; probe không khẳng định đã vượt riêng semantic-review gate bằng một review cũ.

Owner sửa: Gemini implementation owner, task G1-R1 / A2. Acceptance: M01–M04 trong correction matrix.

**G1-R02 [P1] — CoTracker CLI crash trước khi chạy**

Vị trí: [scripts\r6_cotracker.py:8](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cotracker.py:8), [scripts\r6_cotracker.py:198](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cotracker.py:198).

Thực tế/repro: Chạy đúng candidate bằng python -B r6_cotracker.py --help: exit 1, NameError: argparse is not defined. Diff A3 đã bỏ import argparse nhưng main vẫn sử dụng.

Kỳ vọng: CLI --help exit 0; entry point thực phải hoạt động trước khi đóng T08.

Tác động: Không thể dùng CLI đã công bố để tạo paired tracking evidence.

Owner sửa: Gemini implementation owner, task G1-R1 / A3. Acceptance: M05 trong correction matrix.

**G1-R03 [P1] — Tracker validator nhận tensor rỗng và visibility không hợp lệ**

Vị trí: [scripts\r6_cotracker.py:23](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cotracker.py:23), [scripts\r6_cotracker.py:128](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cotracker.py:128), [scripts\r6_cotracker.py:139](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_cotracker.py:139).

Thực tế/repro: Các trường hợp T=N=0, visibility toàn NaN, visibility toàn 9 đều trả (True, ok). Validator chỉ xét shape và finiteness của tracks. Reader dùng both.any() của toàn clip khi tính metric từng window; chưa chứng minh window rỗng/query mismatch được chặn.

Kỳ vọng: Reject empty/nonfinite/out-of-contract tensors; kiểm tra coverage/visibility/query/frame identity ở actual reader, window không có mẫu hợp lệ phải UNKNOWN/FAIL và không xuất PASS/NaN JSON.

Tác động: T08 chưa đóng. Metric có thể được tạo từ dữ liệu không hợp lệ; probe này không phải đánh giá chất lượng video.

Owner sửa: Gemini implementation owner, task G1-R1 / A3. Acceptance: M06–M07 trong correction matrix.

**G1-R04 [P1] — Propagation CLI nuốt lỗi child và trả exit 0**

Vị trí: [scripts\r6_propagate.py:146](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_propagate.py:146), [scripts\r6_propagate.py:218](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_propagate.py:218).

Thực tế/repro: Probe CPU dùng run_one + run_shot + main thật, child thật sys.exit(7). Parent in PROPAGATE BLOCK ... rc=7 nhưng process exit 0 và trả về bình thường. main bắt SystemExit rồi chỉ print.

Kỳ vọng: Batch/CLI phải trả nonzero khi bất kỳ run bắt buộc thất bại, ghi durable failure và không publish success/cho dùng stale manifest. Test mock run_one hiện tại chỉ kiểm run_shot, bỏ sót main.

Tác động: Controller chỉ dựa exit code có thể coi job lỗi là thành công. Lỗi kế thừa chưa được đóng trong acceptance A3, không phải khẳng định mọi controller hiện tại đều chỉ dựa exit code.

Owner sửa: Gemini implementation owner, task G1-R1 / A3. Acceptance: M08–M09 trong correction matrix.

**G1-R05 [P1] — Event keys bỏ mốc occlusion/exit/release**

Vị trí: [scripts\r6_propagate.py:32](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_propagate.py:32), [scripts\r6_gate.py:253](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_gate.py:253), [scripts\r6_ledger.py:109](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_ledger.py:109).

Thực tế/repro: Fixture visible 1–19, occluded 20–29, visible 30–49, NOT_PRESENT từ 50, contact from=9/to=29: event_fids_for chỉ trả [10,30], thiếu chuyển trạng thái tại 20 và 50. Ba nơi ledger/gate/propagate lặp logic chỉ lấy window đầu VISIBLE/PARTIALLY_VISIBLE và contact.from.

Kỳ vọng: Chuẩn hóa duy nhất hợp đồng frame index; mang đủ entry/exit/occlusion/contact-end vào storyboard, key generation và gate; reject mâu thuẫn f/frame hoặc out-of-range theo contract rõ ràng.

Tác động: Mốc mất/che actor có thể không có exact key, interpolation kéo actor hoặc prop qua chuyển trạng thái. Cut helper được test riêng chưa chứng minh caller không băng qua hard cut; cần control trên call path, không suy luận rằng mọi shot hiện tại chứa cut nội bộ.

Owner sửa: Gemini implementation owner, task G1-R1 / A3. Acceptance: M10–M11 trong correction matrix.

**G1-R06 [P1] — Q-matrix tạo PASS từ file rỗng; batch gate chỉ kiểm enum và chưa có caller**

Vị trí: [scripts\r6_matrix.py:29](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_matrix.py:29), [scripts\r6_matrix.py:41](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_matrix.py:41), [scripts\r6_matrix.py:48](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_matrix.py:48), [scripts\r6_gate.py:371](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_gate.py:371).

Thực tế/repro: Tạo strip/json/test/mp4 0 byte: Q01/Q05/Q08 đều PASS; Q07 PASS chỉ vì source có chuỗi r6_key_deps_v3. gate_batch_conformance nhận mode=finla với toàn FAIL vẫn True; mode=final toàn PASS nhưng không artifact cũng True. Tìm trong scripts không có caller của gate_batch_conformance ngoài definition; test gọi helper trực tiếp.

Kỳ vọng: Mỗi PASS dựa proof parse được, đúng inputs/hash/invocation/coverage và caller thật. Mode lạ phải block. Final gate không thay artifact/remaining-work gate bằng enum; phải nối đúng submit call path và không nới C01 assembler binding đã duyệt.

Tác động: A4 chưa đóng Q05/Q10. Tên helper có chữ gate và test xanh không tạo ra cổng nghiệm thu thực tế.

Owner sửa: Gemini implementation owner, task G1-R1 / A4. Acceptance: M12–M14 trong correction matrix.

**G1-R07 [P1] — Manifest bỏ toàn bộ cây R6 nằm dưới thư mục work**

Vị trí: [scripts\r6_matrix.py:77](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_matrix.py:77), [scripts\r6_matrix.py:89](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/scripts/r6_matrix.py:89).

Thực tế/repro: build_manifest loại mọi absolute path chứa /work/ hoặc \work\. R6 thật nằm dưới Documents/Codex/work. Fixture có file thường dưới work/manifest-root/r6 cho count=0. main vẫn ghi R6/R6G_MANIFEST.json thay vì namespace invocation.

Kỳ vọng: Lọc theo relative path và phạm vi evidence rõ ràng; manifest đủ file bắt buộc, cấm rỗng, bind đúng invocation. Record mới ghi vào namespace mới, không đè lịch sử; xử lý self-manifest hash theo thứ tự freeze rõ ràng.

Tác động: Q10 không có manifest đầy đủ; đổi mỗi NS header chưa thực hiện isolation đã claim.

Owner sửa: Gemini implementation owner, task G1-R1 / A4. Acceptance: M15–M16 trong correction matrix.

**G1-R08 [P2] — Test mô phỏng không đủ để tự đóng Q11/T13**

Vị trí: [tests\test_gemini_a4_evidence_conformance.py:106](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/candidate/task/corrections/identity/r6/tests/test_gemini_a4_evidence_conformance.py:106).

Thực tế/repro: Test dùng 2 thread gọi os.open(O_EXCL) trên file tạm; không gọi dispatch_long/acquire_controller_lock/lease, không child lifecycle/PID creation time; join không timeout. Historical 34/34 có thật và 3 production script hashes vẫn khớp, nhưng G1 không cung cấp đủ binding/closure mới; root không rerun suite đó trong lượt này.

Kỳ vọng: Ghi UNKNOWN cho phần chưa kiểm. Có thể dùng proof cũ nếu đối chiếu đúng contract/bytes và raw outcomes; nếu rerun, dùng actual consumers trong sandbox với 2 process barrier tại thao tác tranh chấp, 1 winner/child, bounded joins, ledger đầy đủ, detached/UNKNOWN/PID-reuse controls.

Tác động: Đây là thiếu bằng chứng và overclaim; không kết luận production mutex đang hỏng. Hàm production dùng FileLock và lease lifecycle, khác hẳn primitive mà test A4 kiểm.

Owner sửa: Gemini QA/evidence owner; production harness chỉ đọc, không tự patch ngoài scope. Acceptance: M17–M18 trong correction matrix.

**G1-R09 [P2] — Packet/state chưa đủ nhất quán để resume đúng candidate**

Vị trí: [CONTEXT_RECONCILIATION.json](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/CONTEXT_RECONCILIATION.json).

Thực tế/repro: 13/14 live manifest files khớp; live r6_gate khác candidate. Root lấy được gate đúng hash từ A4 probe snapshot nên review vẫn thực hiện được. Execution STATE tự nhận B2/B1 completed nhưng còn next_command/allowlist/open_findings của A1; CHECKPOINT A4 giữ hash cũ. Claim 27 protected 0 drift không khớp: so baseline có 19 match, 8 khác (7 nằm trong candidate; write_reviews chỉ quan sát live, chưa thể gán thời điểm đổi).

Kỳ vọng: Giữ candidate01 immutable, giải trình before/after và authority từng thay đổi. Reconcile owner session thật 20261017_115944_b2a338; một checkpoint current-byte nhất quán, phân biệt G1 bytes với live/B1 media và self/root approval.

Tác động: Không dùng nhầm verdict G1 cho code sửa sau đó. Các thay đổi nằm trong scope A2/A3/A4 có thể hợp lệ; “0 drift” không phải cách giải trình. Không kết luận B1 không được user cho phép: có chỉ đạo user mới hơn yêu cầu chạy xuyên suốt; lượt này vẫn chỉ nghiệm thu G1 theo 0.12.

Owner sửa: Gemini current manager/implementation lineage; Codex chỉ ghi verdict, không sửa state thay owner. Acceptance: M19–M20 trong correction matrix.

**Kết luận theo batch và Q/T**

| Phần | Kết luận root |
|---|---|
| C01/C02A/C02B1 | 40 regression PASS; giữ các acceptance trước, không suy rộng thành approval cả batch |
| A1 | 14 test PASS; không phát hiện P1 mới trong phạm vi kiểm lần này; chưa cấp approval riêng cho mọi kết hợp |
| A2 | 10 test PASS nhưng R01 tái hiện bypass contract; cần sửa |
| A3 | 7 test PASS nhưng R02–R05 còn mở; cần sửa |
| A4 | 5 test PASS nhưng R06–R09 còn mở; cần sửa/reconcile |
| Q05 | Chưa đóng toàn bộ A4; C01 pre-encoder sub-contract vẫn có regression PASS |
| Q07 | Chưa đóng: asset verifier còn chấp nhận contract thiếu/sai |
| Q10 | Chưa đóng: manifest/state/claim không nhất quán |
| Q11 | UNKNOWN cho acceptance G1 hiện tại; không khẳng định mutex hỏng |
| Q01/Q02/Q03/Q04/Q06/Q08/Q09/Q12 | Không nâng verdict media từ batch CPU này; media mới chưa được root xem/đo |

Bằng chứng raw: [ROOT_76_TESTS.json](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/ROOT_76_TESTS.json), [ROOT_76_TESTS.log](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/ROOT_76_TESTS.log), [ROOT_PROBES.json](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/ROOT_PROBES.json), [COTRACKER_CLI.json](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/COTRACKER_CLI.json), [PROPAGATE_CHILD_FAILURE_CONFIRMED.json](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/PROPAGATE_CHILD_FAILURE_CONFIRMED.json).

`ROOT_PROBES.json` giữ nguyên lượt đầu: probe propagation có child rc=2 do lỗi đường dẫn trong fixture, parent vẫn rc=0. Đã sửa **fixture của reviewer**, không sửa candidate, rồi tái hiện bằng child thật rc=7 trong `PROPAGATE_CHILD_FAILURE_CONFIRMED.json`; đây là receipt dùng cho R04. Những probe khác không bị ảnh hưởng. Các kiểm tra bổ sung là phép thử CPU có điều khiển; không giả làm evidence GPU hay visual QA.

Snapshot vận hành: MAIN HEAD `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`, có dirty/untracked từ trước; INTEGRATION HEAD `a52fca897906fd61a088016dd802718fdf06d217`, clean. Queue 8188 running=0/pending=0, 18 lease RELEASED, controller.lock không tồn tại tại snapshot; last message owner thật kết thúc `finish_reason=stop`. Đây không phải cam kết rằng không thể có writer xuất hiện sau snapshot. Preflight mới vẫn cần trước resume; không khởi chạy agent/dispatch/monitor trong lần review này.

Nhánh media B1 mà STATE tự báo 9 shots/1945 frames không phải bằng chứng G2 đã đạt. Giữ nguyên artifacts để review sau; không xóa hay ghi lại lịch sử. Không đưa phần trăm tiến độ toàn sản phẩm từ số lượng tests.

**Bước tiếp theo**: [CORRECTION_MATRIX.md](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/CORRECTION_MATRIX.md) → [SESSION_OPENING_PROPOSAL.md](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/SESSION_OPENING_PROPOSAL.md) → gửi [PROMPT_SUA_G1_VI.md](C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-20261018/PROMPT_SUA_G1_VI.md) cho owner Gemini hiện tại. Prompt này là một gói sửa G1 trọn vẹn, tự test và self-review trước khi nộp candidate02. Yêu cầu chạy xuyên suốt sản phẩm trước đó không làm candidate01 tự được APPROVED; yêu cầu mới nhất của user là trả verdict G1 theo §0.12.
