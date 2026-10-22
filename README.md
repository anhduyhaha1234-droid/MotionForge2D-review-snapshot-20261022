# MotionForge2D — snapshot private và review độc lập đến 22/10/2026

**Đọc trước:** [Báo cáo review code 22/10](REVIEW_CODE_20261022_VI.md) giải thích mục đích sản phẩm, kiến trúc, phần đã chạy, lỗi lặp lại và các blocker hiện tại. [Phiếu kiểm thử](updates/20261022/TEST_AUDIT_VI.md) tách rõ test nào được chạy và giới hạn của chúng. Repo này là snapshot mới từ bản bàn giao 19/10; nguồn chọn lọc trong `project/` được cập nhật ba file rules/guard và có [manifest SHA-256](updates/20261022/SNAPSHOT_MANIFEST.json) cùng packet G1/G2. **Mã nguồn app tích hợp đầy đủ** ở [nhánh `review/20261002-full-code`](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022/tree/review/20261002-full-code), commit `f3917d1`, không phải cùng candidate với G1 C16.

**Trạng thái hiện tại:** G1 candidate 16 được reviewer độc lập duyệt **chỉ về engineering evidence**, đúng bytes của manifest. G2 transport, preflight và recovery đã được review; G2 media **BLOCKED/NOT_RUN** vì thiếu CAST images, storyboard/media inputs và runtime đã xác minh. Video 5 phút mới và sản phẩm end-to-end **chưa được nghiệm thu**. Repo public cũ và repo private 19/10 vẫn được giữ nguyên.

Kho này lưu **ảnh chụp mã nguồn đang sửa**, prompt/rules/skills của Codex và Hermes, các packet review, checkpoint, cùng chỉ mục dữ liệu video để tiếp tục trên máy khác. Kho gốc `anhduyhaha1234-droid/MotionForge2D` vẫn là lịch sử public; kho này là bản sao **private** và không thay đổi repo gốc.

Đọc [hướng dãn cài lại để chạy tiếp dự án.md](./hướng%20dãn%20cài%20lại%20để%20chạy%20tiếp%20dự%20án.md) trước khi chạy bất kỳ agent hay render nào.
Xem [phạm vi bản sao](./PHAM_VI_BAN_SAO_VI.md) để biết chính xác phần đã lưu và những dependency phải cài lại.
Đọc [lịch sử hội thoại Codex](./conversation_history/LICH_SU_HOI_THOAI_20261019.md) trên máy khác để tra lại các quyết định và trao đổi trong chat này. Đây là ảnh chụp văn bản; các tin nhắn sau thời điểm ghi trong `conversation_history/MANIFEST.json` không tự đồng bộ vào file.
Xem [biên bản dọn máy cũ](./local_cleanup_20261019/REPORT_VI.md) để biết các bản demo/cache đã xóa và những phần vẫn được giữ.

- `project/`: tập source chọn lọc từ bản bàn giao 19/10, gồm thay đổi chưa commit, prompt và rules trong `docs/pm/`; không phải full app integration.
- `source-history.bundle`: lịch sử các branch/tag của repo gốc, dùng để khôi phục Git history.
- `review_and_handoff/`: các prompt, candidate, receipt và review packet đã có trong workspace Codex.
- `agent_rules/`: skills/rules hiện có của Codex, Hermes, cùng `HERMES_SOUL.md`; ví dụ token trong một skill đã được che.
- `review_tools/`: script kiểm chứng của reviewer, lưu để tái lập bằng chứng.
- `conversation_history/`: bản xuất các tin nhắn người dùng/trợ lý hiển thị cùng manifest kiểm tra; không chứa log công cụ hay session database.
- `local_cleanup_20261019/`: kế hoạch, receipt từng mục và số đo dung lượng sau khi dọn máy cũ.
- `ASSET_RELEASE_MANIFEST.json`: tên và SHA-256 của các phần ZIP dữ liệu lớn trong GitHub Release `v2026-10-19-portable`.
- `PORTABLE_SOURCE_MANIFEST.json`: hash byte của source/rules/handoff trong repo này.
- `PAUSE_STATE_20261019.json`: trạng thái gate, owner và tiến trình khi dừng máy cũ.
- `REMOTE_RELEASE_AUDIT.json` và `ARCHIVE_VERIFY_RECEIPT_FINAL.json`: xác nhận 31/31 asset trên GitHub khớp digest và CRC ZIP.

Trạng thái lịch sử của bản đóng gói 19/10 là `g1-candidate-04` chờ review. Xem báo cáo 22/10 ở đầu trang cho verdict G1 candidate 16 và trạng thái G2 mới hơn; các packet cũ không bị sửa để giữ provenance.
