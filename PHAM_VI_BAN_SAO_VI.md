# Phạm vi bản sao MotionForge2D

Ảnh chụp ngày 19/10/2026 lưu repo riêng tư và GitHub Release `v2026-10-19-portable`.

| Thành phần | Cách lưu | Kiểm chứng |
|---|---|---|
| Source hiện tại, kể cả file sửa/chưa commit và prompt/rules trong `docs/pm` | `project/` | `PORTABLE_SOURCE_MANIFEST.json`; thử dựng lại 626 file source đúng SHA-256 |
| Lịch sử branch/tag repo gốc | `source-history.bundle` | `git bundle verify` thành công |
| Prompt, rules/skills Codex và Hermes, candidate, checkpoint, review và scripts | `review_and_handoff/`, `agent_rules/`, `review_tools/`, `review_workbench/` | Manifest source và clone lại từ GitHub |
| Video, project data, output, R6 RUN, checkpoint/media lịch sử | 31 ZIP trong Release private, phần cuối cập nhật 2 log heartbeat sau khi dừng monitor | `ASSET_RELEASE_MANIFEST.json`, CRC 31/31 và 281.469 file riêng biệt |
| Runtime ComfyUI/nodes/công cụ | Commit upstream, `runtime_rebuild/` và `RUNTIME_INVENTORY.json` | Commit và SHA-256 của 12 model đã lưu |

**Phải cài lại/tự xác thực:** 12 trọng số model lớn (88,7 GB) trong runtime dùng chung không tải lên GitHub vì là dependency bên thứ ba và có thể có giới hạn phân phối. Chúng có tên, kích thước, SHA-256 và các script nguồn pin tương ứng để tải lại có kiểm chứng. Không chuyển credential, OAuth/9router account, `.env`, database phiên Hermes/Codex, venv/node_modules/cache hay thư mục `excluded_unlicensed_weights`. Các bản sao lưu Windows Notifications ở gốc repo chỉ là dữ liệu hệ điều hành, không thuộc sản phẩm và không tải lên.

Kho này đủ để phục hồi **source, prompt/rules, project media và RUN**; chưa thể bảo đảm tiếp tục đúng Hermes session cũ hay render ngay trên phần cứng khác. Cần reauth, cài lại runtime/model và review G1 candidate04 theo rules trước khi Media. Không gọi bản sao này là video hay sản phẩm đã nghiệm thu.
