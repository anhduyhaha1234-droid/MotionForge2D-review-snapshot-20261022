# MotionForge2D — bản bàn giao riêng tư ngày 19/10/2026

Kho này lưu **ảnh chụp mã nguồn đang sửa**, prompt/rules/skills của Codex và Hermes, các packet review, checkpoint, cùng chỉ mục dữ liệu video để tiếp tục trên máy khác. Kho gốc `anhduyhaha1234-droid/MotionForge2D` vẫn là lịch sử public; kho này là bản sao **private** và không thay đổi repo gốc.

Đọc [hướng dãn cài lại để chạy tiếp dự án.md](./hướng%20dãn%20cài%20lại%20để%20chạy%20tiếp%20dự%20án.md) trước khi chạy bất kỳ agent hay render nào.
Xem [phạm vi bản sao](./PHAM_VI_BAN_SAO_VI.md) để biết chính xác phần đã lưu và những dependency phải cài lại.
Đọc [lịch sử hội thoại Codex](./conversation_history/LICH_SU_HOI_THOAI_20261019.md) trên máy khác để tra lại các quyết định và trao đổi trong chat này. Đây là ảnh chụp văn bản; các tin nhắn sau thời điểm ghi trong `conversation_history/MANIFEST.json` không tự đồng bộ vào file.

- `project/`: source hiện tại, gồm thay đổi chưa commit, prompt và rules trong `docs/pm/`.
- `source-history.bundle`: lịch sử các branch/tag của repo gốc, dùng để khôi phục Git history.
- `review_and_handoff/`: các prompt, candidate, receipt và review packet đã có trong workspace Codex.
- `agent_rules/`: skills/rules hiện có của Codex, Hermes, cùng `HERMES_SOUL.md`; ví dụ token trong một skill đã được che.
- `review_tools/`: script kiểm chứng của reviewer, lưu để tái lập bằng chứng.
- `conversation_history/`: bản xuất các tin nhắn người dùng/trợ lý hiển thị cùng manifest kiểm tra; không chứa log công cụ hay session database.
- `ASSET_RELEASE_MANIFEST.json`: tên và SHA-256 của các phần ZIP dữ liệu lớn trong GitHub Release `v2026-10-19-portable`.
- `PORTABLE_SOURCE_MANIFEST.json`: hash byte của source/rules/handoff trong repo này.
- `PAUSE_STATE_20261019.json`: trạng thái gate, owner và tiến trình khi dừng máy cũ.
- `REMOTE_RELEASE_AUDIT.json` và `ARCHIVE_VERIFY_RECEIPT_FINAL.json`: xác nhận 31/31 asset trên GitHub khớp digest và CRC ZIP.

Trạng thái đóng gói: Gemini đã nộp `g1-candidate-04` nhưng **chưa có verdict G1 độc lập**. Gói B Media và full-source/app integration vẫn khóa theo `project/docs/pm/HERMES_AUTOPILOT_RULES.md` §0.12.
