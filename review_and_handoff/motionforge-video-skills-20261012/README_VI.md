# MotionForge2D — tiếp nhận bàn giao và áp dụng video skills

Ngày 12/10/2026. Đây là bộ kiến thức và hợp đồng tính năng để tái sử dụng; **không phải review R6, bản build tool hay giấy phép dispatch Hermes**.

Đã đọc rules canonical, AGENTS, SESSION_PROTOCOL, Current execution của handoff/roadmap, packet R5 và bản technology-conformance thay thế. Trạng thái kế thừa: R5 CHANGES_REQUESTED; QUALITY_ACCEPTED=0; pilot CAST B/flat2D 5 phút; full22/tool/integration còn BLOCKED_DEPENDENCY. Lượt này không xem lại phim, chạy inference, kiểm owner live hoặc đưa verdict mới.

MAIN được kiểm đọc: master `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`, có thay đổi sẵn. INTEGRATION: `a52fca897906fd61a088016dd802718fdf06d217`, sạch tại lần kiểm. Không sửa hai checkout, PM docs, registry hay media; không mở chat/worker hoặc liên hệ Hermes.

## Kết quả sử dụng được

- [Đánh giá 15 nguồn và quyết định tái dùng](motionforge-video-craft/references/TECH_ADOPTION_VI.md): kiểm README/SKILL, các call path liên quan, điều kiện sử dụng và giới hạn.
- [Hợp đồng tính năng để đưa vào tool](motionforge-video-craft/references/FEATURE_CONTRACT_VI.md): vị trí nối vào code hiện hữu, đầu vào/đầu ra, điều kiện kích hoạt, nghiệm thu và thứ tự triển khai.
- [Skill MotionForge đã điều chỉnh](motionforge-video-craft/SKILL.md): đọc theo loại công việc; không mang các yêu cầu đổi style, cắt nhạc hay mở nhiều agent vào pilot giữ nguồn.
- [Bộ kiểm cue-plan chạy độc lập](motionforge-video-craft/scripts/validate_cues.py), [ví dụ](motionforge-video-craft/assets/cue-plan.example.json) và [kết quả kiểm](CONTRACT_CHECKS.json): kiểm hợp đồng dữ liệu bằng fixture tổng hợp, không render video.
- [Khóa nguồn](motionforge-video-craft/references/SOURCE_LOCK.json): commit và SHA256 tài liệu đã tải. `downloaded` khác `read`; chỉ các phần liên quan được kiểm đọc, không tuyên bố đọc toàn bộ mọi repo.

Skill được đóng gói trong outputs, chưa cài global và chưa nạp vào Hermes đang chạy. Các nguyên tắc đã được áp dụng vào quyết định và hợp đồng của bộ này; chưa có integration hay media proof mới. Khi cần dùng ở lượt sau, mở SKILL.md này cùng rules canonical hiện hành.

Prompt Hermes đang có hiệu lực vẫn là `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012/NEXT_HERMES_MANAGER_PROMPT.md`. Bộ này không thay prompt đó, không sửa 12Q/T01–T15 hoặc counters. Bạn tự giao Hermes và báo khi cần review.
