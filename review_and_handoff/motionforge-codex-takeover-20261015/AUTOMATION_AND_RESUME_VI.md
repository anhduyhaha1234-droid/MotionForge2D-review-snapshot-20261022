# Tiếp tục MotionForge2D khi context/quota gián đoạn

Đã tạo heartbeat `motionforge-checkpoint-v-quota`, ACTIVE, kiểm tra mỗi giờ trong chat gốc. Tool receipt trả về `Created automation in the app.`. Chỉ thông báo khi hoàn thành cần review, lỗi mới, cần user xử lý, hoặc quota trở lại sau block đã biết; trạng thái không đổi thì im lặng.

Nguồn trạng thái: PROJECT_STATE.json, task_packet/checkpoint của coding owner và các receipt được state trỏ tới. Canonical rules vẫn ở C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md (§0.11); file này mô tả vận hành, không tạo rules cạnh tranh.

Chỉ một coding owner hoạt động, xác định bằng PROJECT_STATE.json, model `gpt-6-sol`, reasoning `max`. C01 đã được root duyệt trong C01_REVIEW_02.md; task hiện hành là C02A, owner `/root/motionforge_c02a_coder`. Task mới chỉ mở sau gate của task trước; correction/quota continuation giữ cùng owner. Coder tự review và sửa trong allowlist; root độc lập kiểm tra actual diff, probes và output trước khi duyệt task. Không tự đổi model hoặc tạo writer khác để vượt quota. Approval một task CPU không tương đương video được chấp nhận.

Mỗi task có đầu ra kiểm chứng riêng. Chỉ nạp packet hiện tại, checkpoint, đoạn source cần thiết và vài skills liên quan. Thư viện đầy đủ nằm trên đĩa. Checkpoint giữ goal, authority, task/owner/model, allowlist, file/hash, quyết định, commands/exit, vấn đề còn mở, bước tiếp và jobs sống. Không dùng số message để suy phần trăm context; bản summary phải giữ exact IDs/paths/hashes.

Hai research agents đã gặp lỗi provider: `Your workspace is out of credits. Ask your workspace owner to refill in order to continue.` Usage API sau đó vẫn báo ordinaryUsageAllowed=true và 11%5h/2%tuần đã dùng; điều này không chứng minh credits của mọi execution route đều khả dụng. Coding agent được thử đúng model user chọn và đã gửi RULES_LOADED/preflight qua tool thật. Nếu gặp lỗi tiếp, ghi nguyên văn và thông báo ở chat này, không đoán reset time.

Heartbeat dùng cùng môi trường/tài khoản, không thể bảo đảm tự thức dậy hoặc gửi thông báo khi chính tài khoản đang bị chặn hay máy/app không chạy. Nó không mua credits, dùng reset credit, hay vượt giới hạn. Khi xác minh được quota/model khả dụng, task đã được cấp quyền có thể tiếp tục sau zero-writer preflight; nếu chưa xác minh được thì giữ checkpoint.

Để khôi phục thủ công, chỉ cần nhắn: **“Tiếp tục MotionForge từ PROJECT_STATE.json, GPT-6 Sol Max; kiểm tra owner trước, coder tự review rồi bạn review độc lập.”** Không cần dán lại toàn bộ lịch sử.
