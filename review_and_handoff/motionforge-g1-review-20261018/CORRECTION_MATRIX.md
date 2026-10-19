**Finite correction matrix — G1-R1, 20 hàng acceptance.**

Mỗi hàng có raw command, exit code, timing, source hashes, observed/expected và owner; tên test dưới đây là tên yêu cầu cho lượt sửa, không phải test root đã chạy. Không tính số hàng thành số test hoặc % hoàn thành sản phẩm. Từng biến thể phải có subcase receipt; không bỏ negative controls để làm xanh.

| Row | Finding | Test/receipt cần có | Điều kiện đóng |
|---|---|---|---|
| M01 | R01 | test_asset_missing_ref_rejected | Xóa grey_ref / null / wrong role / wrong path; self-digest hợp lệ; từng trường hợp verifier từ chối. |
| M02 | R01 | test_asset_effective_graph_mismatch | Sampler khác recipe; R1/R2 reference sai; graph hợp hash nhưng sai effective inputs: phải block. |
| M03 | R01 | test_asset_actual_producer_consumer_contract | Actual run_key → deps → skip/key gate; graph mutation phải block trước publish. Không chỉ gọi helper. |
| M04 | R01 | test_asset_controls_and_regressions | Restyle, black passthrough hợp lệ, unchanged replay không gọi thêm stage/upload/post; 14 A1 + 10 A2 + 40 regression giữ. |
| M05 | R02 | test_cotracker_cli_help_and_fixture_entry | Subprocess --help exit0; actual CLI controlled predictor/CPU fixture đến validation; không inference GPU. |
| M06 | R03 | test_cotracker_invalid_tensor_matrix | T/N=0, tracks NaN/Inf, vis NaN/Inf/invalid type/range, shape/query mismatch, out-of-canvas: không PASS. Valid bool/probability theo contract rõ ràng vẫn đúng. |
| M07 | R03 | test_cotracker_window_coverage_controls | Window không có visible pair, empty/out-of-range event, f/frame mapping; valid/known-bad fixture phân biệt; JSON không NaN; source/output query/time identity khớp. |
| M08 | R04 | test_propagate_cli_child_nonzero | Child process thật rc7 → parent nonzero, receipt failure, không success/publish/assemble. Control rc0 + đủ output vẫn thành công. |
| M09 | R04 | test_propagate_partial_stale_retry | Missing/partial/corrupt/extra/wrong-name output và stale prior manifest/retry khác invocation: fail closed; stdout-only BLOCK không được coi là thành công. |
| M10 | R05 | test_event_transition_end_to_end | Fixture off-grid entry/exit/occlusion/reappearance/contact end đi qua ledger → board → key discovery → gate/propagate; boundary 20/50 phải có exact key. |
| M11 | R05 | test_event_bounds_and_cut_call_path | Conflict f/frame, 0/negative/out-of-range, final endpoint; actual shot-plan caller không interpolate qua hard cut; không lấy helper-only test làm closure. |
| M12 | R06 | test_matrix_empty_stale_wrong_evidence | 0-byte/malformed/stale/wrong hash/other invocation/missing coverage → UNKNOWN/FAIL; file tồn tại hoặc code substring không đủ PASS. |
| M13 | R06 | test_batch_gate_strict_modes_and_evidence | Mode lạ/thiếu; final allPASS thiếu artifact; fake engineering PASS thiếu proof: block. Giữ phân biệt historical technical PASS với candidate hiện tại. |
| M14 | R06 | test_submit_actual_caller_gate | Actual submission/assembler caller dùng gate trước publish/copy/encode; encoder-spy negative controls; giữ C01 positive. Không sửa historical writer/terminal để tạo caller giả. |
| M15 | R07 | test_manifest_work_ancestor | Windows root chứa work vẫn liệt kê mandatory artifacts; chỉ loại đúng R6-relative work nếu contract yêu cầu. Không empty-success. |
| M16 | R07 | test_manifest_namespace_and_finalization | Namespace unique; sentinel lịch sử bytes giữ; manifest đủ required hashes, không self-hash stale; artifact mutate sau freeze làm gate block. |
| M17 | R08 | test_q11_existing_proof_binding | Đối chiếu source/runtime/test/raw evidence hashes với historical proof; claim chính xác coverage; không coi mock os.open là controller proof. |
| M18 | R08 | test_q11_actual_race_and_lifecycle | Nếu cần rerun: 2 live process rendezvous ngay contested operation, 1 winner/1 child, bounded joins, full ledger; PID reuse/UNKNOWN/detached child giữ lease. Chạy cloned sandbox, không patch harness ngoài scope. |
| M19 | R09 | test_candidate_identity_reconciliation | 14 candidate hashes rõ; live drift và 8 protected differences giải trình từng file/thời điểm/scope; giữ snapshot01 và B1 evidence. Current deps mới được freeze/hash đầy đủ. |
| M20 | R09 | test_resume_state_truth | STATE/CHECKPOINT/RESUME cùng task/hash/owner/next action; owner thật vs label; no stale A1 facts; rootG1 CHANGES_REQUESTED; live_jobs theo process/queue hiện tại. |

Thứ tự: micro repro → 20 hàng matrix có evidence (M18 chỉ có thể dùng VERIFIED_UNCHANGED nếu M17 chứng minh đầy đủ contract/bytes/raw outcomes; không N/A vì thiếu thời gian) → focused tests/static actual callers → cả 7 module của suite 76 và tests mới. Dừng mở rộng kiểm tra khi closure đủ, không render GPU để chứng minh parser. Giữ riêng self-review và root approval.

M01–M16: implementation owner sửa trong A2/A3/A4; M17–M18 QA proof, harness production read-only; M19–M20 manager evidence owner. Maximum concurrent production writer = 1.
