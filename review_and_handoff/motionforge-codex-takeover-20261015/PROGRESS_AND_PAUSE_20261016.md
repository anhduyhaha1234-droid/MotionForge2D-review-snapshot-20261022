# Báo cáo tiến độ và dừng lịch — 16/10/2026

Theo yêu cầu của user, automation motionforge-checkpoint-v-quota đã được công cụ xác nhận PAUSED và file cấu hình đã kiểm tra lại. Không tiếp tục coder. Owner /root/motionforge_c02b2_coder hiện terminal errored vì usage limit; không có writer mới được mở.

## Tiến độ có bằng chứng

| Phần việc | Kết quả |
|---|---|
| Thư viện kỹ năng | Đã nhập 40 thư mục Hermes liên quan (551 file) và cài 5 community skills GitHub có commit/license/hash. Đây là tài liệu/phương pháp, không phải 45 tính năng sản phẩm. Coverage Hermes: 21 SKILL.md đọc đầy đủ, 3 một phần, 16 chỉ index. |
| C01 | APPROVED: chặn dùng review sai artifact hoặc thiếu frame để qua cổng ghép video. Root probes 30/30 + 3/3; module 17/17. |
| C02A | APPROVED: chặn dependency thiếu, sai kiểu, thay đổi hoặc JSON quá sâu; tránh nhận nhầm cache hợp lệ. Root probes 55/55 + 8/8; full affected modules 30/30. |
| C02B1 | APPROVED: frame trích xuất gắn với đúng source/frame/output; đổi nguồn phải tạo lại, lỗi trích xuất giữ cặp cũ. Root probe 7/7; new tests 10/10 và 30/30 hồi quy. Có fixture FFmpeg thật. |
| C02B2 | Dở dang, NOT APPROVED. Đã sửa producer/cache và thêm helper/test. Probe của coder cho thấy lần đầu tạo ảnh 1 lần, chạy lại đầu vào giữ nguyên tạo 0 lần. Chưa hoàn tất negative matrix, self-review/freeze hay root review. |
| Sản phẩm bàn giao mới | 0 video mới được nghiệm thu; 0 tính năng mới tích hợp và nghiệm thu trong tool. Pilot 300s, full source và parent MF-DEMO-LONG-01 vẫn chưa đạt. |

Ba trên bốn gói coding đã mở có verdict APPROVED ở snapshot của từng gói (75% theo số gói đã mở). Đây KHÔNG phải 75% toàn dự án, không phản ánh trọng số công việc. Các giai đoạn sau chưa làm và chưa có baseline có trọng số để tính phần trăm hoàn thành toàn dự án. Không cộng các lượt chạy lại cùng test thành số tính năng hoặc số test độc lập mới.

Code hiện tại có sửa đổi C02B2 chưa được nghiệm thu, gồm cả cache đã từng được duyệt ở snapshot C02A. Vì thế không được coi toàn bộ working tree hiện tại là đã APPROVED.

## Quota và hiệu quả

Các snapshot cùng tài khoản ngày16/10 ghi quota tuần đã dùng 16% lúc04:05, 48% lúc14:12, 63% lúc19:17 (UTC+7): tăng47 điểm phần trăm từ snapshot đầu đến cuối. Đây là hạn mức TOÀN TÀI KHOẢN, không có attribution theo chat/agent, nên không thể quy tất cả cho MotionForge hay tính chính xác quota bị lãng phí.

Snapshot mới lúc dừng ghi 5h dùng7%, tuần dùng1%. Mốc reset đã khác các snapshot cũ; không lấy số1% để kết luận công việc trước đây tốn ít quota. Root không thực hiện mua/reset credits trong lượt này. Workspace credits và account quota là các tín hiệu khác nhau.

Coder đã báo usage limit và mốc thử lại17/10 00:16; đây là thông báo của provider được lưu nguyên trong receipt, không phải lịch tiếp tục mới. User đã yêu cầu dừng nên không resume dù API hiện cho phép ordinary usage.

Có tiến bộ kỹ thuật được chứng minh, nhưng chưa có đầu ra sản phẩm mới để user sử dụng. Chưa có dữ liệu token/chi phí theo task để xác định tỷ lệ lãng phí. Quy trình trước đó tạo nhiều hồ sơ/checkpoint; file PROJECT_STATE còn ghi RUNNING và checkpoint001 sau khi worker đã lỗi và đạt checkpoint015. Sai lệch trạng thái này đã được sửa ở lần dừng.

## Điểm dừng

Checkpoint gần nhất c02b2-worker/CHECKPOINT_015.json. Bốn source/test hiện tại đều khớp SHA256 checkpoint015. Bản sao và receipt dừng lưu riêng; không rollback hay sửa production code. State chuyển PAUSED_BY_USER, automation PAUSED, active_writer=false. Chỉ tiếp tục khi user yêu cầu.

Bằng chứng chính:
- [C01 review](C01_REVIEW_02.md)
- [C02A review](C02A_REVIEW_02.md)
- [C02B1 review](C02B1_REVIEW_01.md)
- [Checkpoint C02B2](c02b2-worker/CHECKPOINT_015.json)
- [Probe coder C02B2](c02b2-worker/v4-replay-03/RESULT.json)
- [Nguồn và cài đặt skills](skills/README_VI.md)

