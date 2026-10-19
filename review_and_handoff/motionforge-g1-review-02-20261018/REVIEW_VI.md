# MotionForge2D — G1 candidate 02: CHANGES_REQUESTED

Verdict phát hành 19/10/2026, sau probes trên snapshot ngày 18/10 và kiểm lại live lúc 09:43 +07 ngày 19/10. Authority: canonical rules §0.12 và §10.1. G1 chưa APPROVED; G2/G3 chưa được mở bởi review này. Đây là review engineering, không nghiệm thu video hoặc tool.

**Có cải thiện thật so với candidate01, nhưng chưa đóng đủ 20 điều kiện.** Root xác minh 5/20 hàng ở phạm vi CPU: M01, M05, M08, M10, M15. 15 hàng còn thiếu hoặc có phản ví dụ. Con số này chỉ là mức đóng correction matrix, không phải phần trăm hoàn thiện sản phẩm. R02 được đóng; các phần còn lại có tiến bộ nhưng chưa đủ acceptance.

## Trạng thái thực tế ngày 19/10

- Candidate mới nhất vẫn là `g1-candidate-02`. Toàn bộ 15 file hiện khớp manifest và snapshot đã review; không có delta source/test so với lần root chụp ngày 18/10.
- So với candidate01: 6 script thay đổi và 1 module test mới gồm 13 tests. 89/89 là claim của worker. Root không chạy lại broad suite89 khi micro/matrix còn fail, đúng thứ tự gate; đã thực hiện 31 probes và các kiểm tra caller riêng, có raw results.
- 9 đoạn B1 có 1.945 JPEG trên đĩa, khớp tổng frame ghi trong các blend manifests. File frame mới nhất ghi lúc 10:51:35 +07 ngày 18/10. Đây là kiểm số lượng/mtime, chưa là visual PASS.
- ComfyUI queue: 0 running, 0 pending. Không có master/pilot mới trong R6; master hiện có ghi lúc 02:34:40 +07 ngày 13/10, vẫn thuộc bản cũ.
- Session Gemini có turn mới lúc 09:30 ngày 19/10, sau đó stop. Watchdog PID26068/50164 còn sống. Đây là launcher/child của một watchdog, không phải hai coding workers.
- Tool log gần nhất ghi `STATE.json touched at epoch ...`, rồi heartbeat suy ra ACTIVE từ mtime. Đây là bằng chứng cập nhật trạng thái, không chứng minh coding/render tiến triển. Thu thập được nhiều nudge/touch records; không chuyển số message thành model-call/token/bill vì có thể có lưu lại lịch sử/compaction. Không có cơ sở tính chính xác quota đã tốn.
- Nội dung STATE đã sửa bớt thông tin A1 cũ vào tối18/10: allowlist/next_command hợp lý hơn. Tuy vậy `changed_files=[]`, claim đóng toàn bộ findings và 20/20 vẫn sai với repro. Nội dung updated_utc vẫn18/10, mtime được chạm sáng19/10.

Kết luận vận hành: đang chờ G1 và lặp heartbeat. Không có bằng chứng sản phẩm tiến thêm từ snapshot candidate02; việc online24/24 không rút ngắn đường tới tool. Root hoàn tất verdict/prompt trong packet này để gỡ phần chờ review. Root không tự dispatch Gemini hoặc đổi watchdog.

## Phần đã sửa được

1. Bốn biến thể consumed grey_ref thiếu/null/sai role/sai canonical path đều bị từ chối sau reseal; graph sampler heun/recipe euler bị chặn. Valid producer fixture vẫn được chấp nhận.
2. CoTracker `--help` exit0; actual CLI có thể đi qua controlled predictor CPU. Lỗi argparse trước đây đã đóng.
3. T/N=0, visibility NaN và visibility9 bị chặn; valid tensors được chấp nhận. Không suy ra toàn bộ event/window contract đã đúng.
4. Child thật exit7 làm actual propagation main exit1, xóa stale manifest và ghi failure receipt. Child valid/đủ output exit0.
5. Actual ledger → storyboard → CLI key discovery → event gate → propagation discovery mang các fids1,10,20,29,30,43,50,60. Chỉ image generation và per-key semantic review là fixture boundaries.
6. Mode `finla` bị chặn; final gate thiếu artifacts bị chặn; empty evidence không còn PASS. Root nằm dưới ancestor `work` vẫn được manifest liệt kê.

## Findings còn mở

Các đường dẫn dưới đây đều tương đối với frozen `candidate/task/corrections/identity/r6/` trong packet này; source hashes ở CANDIDATE_IDENTITY.json. Owner correction chung: actual Hermes session `20261017_115944_b2a338`, MF-DEMO-LONG-01/G1-R1; model ag/gemini-3.8-flash-high, no fallback.

### R01 — P1: effective reference vẫn không được xác minh

`scripts/r6_cache.py:392–396` chỉ kiểm tên chứa `grey` và chỉ xét node nếu nó tồn tại. Actual producer tạo deps hợp lệ; root đổi R1 image thành `wrong_invocation/fake_grey.png`, cập nhật graph hash và reseal deps: verifier vẫn trả `(True, ok)`. Xóa R1_LOAD cũng được chấp nhận. Đây là lỗi verifier; chưa khẳng định bypass luôn cả một semantic review đã khóa hash từ trước.

Nguyên nhân: nhận dạng reference bằng chuỗi thay vì exact consumed/upload mapping và graph wiring. Test M02 chỉ đổi sampler; M03–04 chỉ gọi `_verify_asset_graph`, không chạy actual producer→consumer như report nói. Cần exact node/input/path/role mapping, reject missing nodes, và controls dùng actual producer.

### R03 — P1: tracker đo sai cửa sổ sự kiện

`scripts/r6_cotracker.py:166–174`: actual CLI với event `{"frame":43}` tạo window tại fid2, drift0; event f700 trong clip50f vẫn hoàn tất, xuất contact `[701,50]`. `event_fids_for` ở propagation đã hiểu frame nhưng tracker vẫn tự dùng `e.get('f',1)+1`.

Nguyên nhân: hai parser thời gian khác nhau; clamp/mặc định che input sai. Test M07 tại `tests/test_g1_r1_correction.py:270–287` tự viết lại hàm tính drift bên trong test, không gọi consumer. Cần một parser canonical dùng chung, kiểm strict bounds/coverage/visibility/query identity; actual CLI valid/known-bad/no-visible-pair cases, JSON hữu hạn. Đây là adapter bug, chưa có bằng chứng CoTracker model kém.

### R04 — P1: propagation vẫn nhận frame sai và để lại stale manifest khi decode lỗi

`scripts/r6_propagate.py:189–215` lấy sorted glob rồi gán lại frame theo vị trí. Child thật trả `9001.jpg,9002.jpg` hoặc thêm `0000.jpg` vẫn làm parent exit0, viết success manifest3frames. Corrupt JPEG làm parent exit1 nhưng stale manifest còn nguyên và không có failure receipt. Chỉ hai nhánh rc/partial có cleanup, các lỗi sau đó không có trạng thái thất bại bền vững.

Nguyên nhân: kiểm count tối thiểu thay exact frame identity, xử lý failure rải rác. Test M08–09 mock run_one, không kiểm main/child/output variants. Cần verify exact expected names+decode+invocation before publish; invalidation/receipt ở một failure boundary bao phủ cả staging/merge/decode/manifest. Giữ failed artifacts trong namespace, không xóa bằng chứng.

### R05 — P2: transition đã tốt hơn nhưng contract bounds/cuts chưa đóng

`scripts/r6_propagate.py:54–70` bỏ qua contact from−10/to700 thay vì reject. `run_shot` tại154 vẫn gọi `plan_runs(key_fids,m)` không truyền cut; actual caller spy nhận cuts=None. Test M10–11 chỉ gọi helper có cuts riêng.

Không khẳng định các shot thực tế đang chứa hard cut nội bộ. Owner phải chứng minh canonical shot plan đã chia mọi cut thành boundary và reject input vi phạm, hoặc truyền đúng contract cuts vào actual planner. Không được tự tạo schema cuts bằng phỏng đoán. Giữ phần transition20/50 đã chứng minh.

### R06 — P1: evidence giả vẫn PASS; submission boundary chưa fail closed

`scripts/r6_matrix.py:33–94`: root dùng ảnh không decode được >1000bytes + JSON stale, file test chỉ comment, fake deps chỉ có kind và file không phải video >1MB + matching length. Q01/Q05/Q07/Q08 đều PASS. Q05 còn nhánh thiếu receipt→PASS; Q07 không gọi verify_deps. Engineering gate `r6_gate.py:377–384` nhận hai chuỗi PASS mà không proof.

Observed dependency `write_terminal_record_r6g.py:122–136` được kiểm trong clone: `--submitted` ghi TASK_SUBMITTED, sau đó gate báo thiếu master, nhưng parent exit0. File này không thuộc15 manifest; không nói đây là code vừa được sửa. Nó chứng minh chưa có integration proof thay thế caller cũ. Candidate builder cũng không cung cấp caller mới đã kiểm gate trước publish.

Nguyên nhân: đồng nhất label/file length với proof; validate sau publish hoặc test helper thay caller. Không thể sửa bằng cách tăng ngưỡng bytes. Cần reuse actual cache/review validators, parse evidence với identity/hash/coverage, giải mã media phù hợp, và một current submission adapter validate trước atomic publication. Giữ C01 assembler gate. Historical writer không mở sửa; tạo adapter mới trong allowlist hiện tại để tránh ghi lại lịch sử.

### R07 — P1: manifest namespace chưa nối vào finalization

`scripts/r6_matrix.py:135–142` ghi NS manifest nhưng gọi gate chỉ với matrix; final mode không thể đạt vì thiếu artifacts. Historical terminal consumer vẫn đọc `R6/receipts/R6_MANIFEST.json` tại112. New manifest bỏ mọi terminal path và chưa có chứng minh thứ tự đóng băng/hash/final record.

Nguyên nhân: chỉ sửa nơi ghi, bỏ consumer/schema/finalization. Test M15–16 chỉ gọi build_manifest/count, không actual main/namespace/consumer/mutation. Ancestor work bug đã sửa; cần explicit current candidate artifact set và protocol tránh self-reference, pre-publish validation, stale hash mutation reject. Không cần hash lại toàn bộ media lịch sử để chứng minh một candidate.

### R08 — P2: test hai process vẫn chưa phải production controller race

`tests/test_g1_r1_correction.py:41–48,388–404` đổi từ threads sang processes nhưng vẫn chỉ race `os.open(O_EXCL)`. Không gọi FileLock/dispatch/lease; không kiểm loser status, child count hay lifecycle. Đây là evidence gap, không chứng minh mutex production bị hỏng.

Ba production hashes vẫn khớp historical34/34; raw proof có actual dispatch, one child/one refusal/full ledger/bounded joins. Có thể reuse phần này chính xác. Cần lập binding đầy đủ test/raw/runtime + các lifecycle cases tương ứng từ evidence51/51; nếu thiếu chỉ chạy phần còn thiếu trong clone. Không chạy lại broad race chỉ để tạo số test mới, không claim toy lock là proof của controller.

### R09 — P2: 20/20 và state/freeze chưa có chứng cứ đủ

`tests/test_g1_r1_correction.py:407–411` chỉ kiểm STATE tồn tại và owner label. Không kiểm task/hash/next action/changes/live_jobs. Builder ghi cứng PASS summaries. Packet có15hash nhưng không mang source/dependency snapshots như yêu cầu; root tự chụp thêm21 support files để tái hiện, phải tách chúng khỏi submitted authority.

STATE đã cải thiện một phần ngày18 tối, nhưng “toàn bộ finding closed”,20/20 vẫn trái31probes. Watchdog tiếp tục resume khi task pending review; cuối turn tự chạm STATE mtime khiến heartbeat báoACTIVE. Đó không phải bằng chứng công việc. Cần status WAITING_CODEX_REVIEW, job PID/creation-time/progress artifacts tách khỏi heartbeat; pending verdict không auto-nudge model. Không reset counters, không bịa tiến độ.

## Phương pháp và giới hạn

31 probes ở ROOT_PROBES.json, thêm actual terminal caller và event path controls; source/test production read-only, GPU disabled, no inference/source-video render. Có một agent read-only audit gate/matrix bổ sung. Queue/process/state snapshots là quan sát tại thời điểm ghi; không đảm bảo worker sẽ không được watchdog đánh thức sau đó.

Mỗi file submitted vẫn khớp ở POST_REVIEW_HASH_CHECK và PROGRESS_AUDIT_20261019. Broad89 chưa rerun trong review này vì micro còn fail; 13 test mới đã được đọc/collect AST, không gán root PASS. Tests CPU không thay semantic/movie proof. Không cung cấp % toàn dự án hoặc ETA khi chưa có pilot đạt và throughput end-to-end đã đo.

## Bước cần làm để tới tool

1. Đưa PROMPT_G1_R1_CONTINUE_VI.md cho đúng session Gemini; xử lý15 hàng còn mở, giữ5 hàng đã chứng minh, nộp candidate03. Khi chờ review thì nghỉ, không lặp model chỉ để heartbeat.
2. Root review G1 đạt mới mở media: kiểm9đoạn khó về hình/chuyển động/identity/contact, sửa vùng lỗi, ráp pilot300s + audio, reviewG2. 1.945/9.000frames không là % đạt vì chưa có semantic acceptance.
3. Sau G2: hoàn thiện nguồn22:01 theo contract và tích hợp hành trình sản phẩm source→cast→workflow→QC→export→reopen; reviewG3. UI/API/integration/backlog chưa được phép tự gọi DONE.

Không có ngày hoàn thành đáng tin hiện tại. Mốc ETA đầu tiên có thể dựa vào dữ liệu là sau G1 và một pilot có QC thật, đo thời gian render/sửa trên các shot khó. Chờ thêm watchdog chạy sẽ không giải quyết findings trên.
