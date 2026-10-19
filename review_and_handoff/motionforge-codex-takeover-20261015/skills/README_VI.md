# Thư viện skills MotionForge2D

Đã import byte-identical 40 thư mục Hermes liên quan dự án (551 file), chọn từ171 skills. Manifest giữ source, SHA256 và mức độ đọc:21 đọc đầy đủ,3 đọc một phần,16 chỉ index. Toàn bộ tài liệu được lưu để truy xuất theo task; không nhét tất cả vào context.

Đã cài5 skill GitHub vào Codex và sao chép bản ghim vào thư viện này. SKILL_SOURCE_LOCK.json xác minh nguồn GitHub, commit, license và hash từng file. Bốn SKILL.md khớp exact bytes; context-compression qua git trên Windows có CRLF, khớp toàn bộ nội dung sau chuẩn hóa LF. Đây là community skills, không gắn nhãn official OpenAI/Anthropic.

Áp dụng ACTIVE_DIGEST_VI.md dưới canonical rules và chỉ thị user. Không thực thi scripts/hooks khi import. Không áp các chỉ dẫn đổi model, tự commit/push, hỏi lại approval đã có, tự mở thêm workers, hoặc total caps lịch sử. Skill writing-plans được dùng để chia việc; user đã chọn cách thực thi nên không cần một vòng xin duyệt kế hoạch mới. Skill verification áp đúng claim, không bắt render GPU lại cho mọi sửa CPU. Context sử dụng checkpoint theo task; không bịa phần trăm context. compression_evaluator.py là demo heuristic, không là quality gate.

## Nguồn5 skill đã cài
- [verification-before-completion](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/verification-before-completion/SKILL.md)
- [systematic-debugging](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/systematic-debugging/SKILL.md)
- [writing-plans](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/writing-plans/SKILL.md)
- [receiving-code-review](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/receiving-code-review/SKILL.md)
- [context-compression](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/9ff0c99108b36d3b886defd825d8ac1f47dba374/skills/context-compression/SKILL.md)
