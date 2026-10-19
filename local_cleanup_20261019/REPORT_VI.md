# Biên bản dọn dữ liệu cục bộ MotionForge2D — 19/10/2026

Theo yêu cầu của chủ dự án, đã dọn **208/208 mục, không lỗi** trên máy cũ. `PLAN.json` ghi đường dẫn, lý do và kích thước trước khi xóa; `RECEIPT.jsonl` ghi kết quả từng mục; `SUMMARY.json` ghi tổng và dung lượng ổ đĩa quan sát được.

| Nhóm | Dung lượng file trước khi xóa |
|---|---:|
| 31 ZIP trung gian của bản Release đã đối chiếu SHA-256/CRC | 23,52 GiB |
| Run `MF-DEMO-LONG-01` đã có trong Release private | 20,39 GiB |
| Hai môi trường Python `venv` có thể cài lại | 9,56 GiB |
| Tám thư mục `demo-*` thuộc evidence lịch sử | 8,59 GiB |
| `node_modules`, `.next` và cache trong các Git worktree cũ | 7,10 GiB |
| Demo package/runtime, bản clone thử phục hồi, cache gốc và output test | 1,52 GiB |

**Tổng file đã xóa:** 745.707 file, 75.893.132.154 byte (**70,68 GiB**). Dung lượng trống ổ C tăng từ khoảng **321,54 GiB** lên **392,92 GiB**, tức **71,38 GiB** theo số đo ổ đĩa. Chênh lệch so với tổng kích thước file có thể do cách ổ đĩa tính dung lượng và hoạt động khác cùng thời điểm.

Đã giữ nguyên `C:/Users/Admin/MotionForge2D` và commit HEAD `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`; số mục Git đang sửa/chưa theo dõi vẫn là **104**. Giữ mã nguồn của **101 Git worktree** đã đăng ký, evidence không mang nhãn demo, dự án gốc và các trọng số model runtime khoảng **88,7 GB** vốn không được tải lên Release. Một số thư mục demo/evidence lịch sử bị xóa theo yêu cầu và **không thuộc Release**; file nguồn và evidence phục vụ G1 candidate04 vẫn nằm trong repo private.

Trước khi xóa, `REMOTE_RELEASE_AUDIT.json` xác nhận repo private và 31/31 asset đúng SHA-256; `ARCHIVE_VERIFY_RECEIPT_FINAL.json` xác nhận CRC. Sau khi xóa, 208/208 đường dẫn vắng mặt và Git root vẫn đúng HEAD. Gate G1/G2/G3 không thay đổi.
