# G2-B1-PREFLIGHT-01 — báo cáo cho root review

**Kết luận: BLOCKED.** Đây là kiểm tra sẵn sàng chỉ đọc, dùng CPU; chưa chạy pilot 300 giây, dựng hình, suy luận mô hình hay khởi động dịch vụ. Biên nhận máy đọc là `READINESS.json`, tạo lúc `2026-10-22T04:45:10.914294+00:00`, gồm 19 PASS, 25 FAIL, 7 UNKNOWN. PASS chỉ áp dụng cho phép kiểm cụ thể; không phải product PASS.

## Checkpoint và phạm vi

Đã đọc toàn bộ `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md` và `C:/Users/Admin/MotionForge2D/AGENTS.md` trước khi viết. Root review `C:/Users/Admin/Documents/Codex/g2-readiness-audit/ROOT_REVIEW_G2P01.md` có SHA-256 `6bfb1d71b900a84ca84df0e765c839202a24c96cf90738577c1c1c36aaa082ce` và chỉ chấp thuận transport. Write-set duy nhất là `C:/Users/Admin/Documents/Codex/g2b1-readiness/`, xác nhận ban đầu chưa tồn tại. Các nguồn, candidate C16, pilot đã duyệt, MAIN, runtime, lease và thư mục agent khác chỉ đọc. Không import module R6 vì `r6_common.py` tạo thư mục lúc import; chỉ phân tích cú pháp/byte.

## Bằng chứng chính

- C16: SHA-256 `MANIFEST.json` = `4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82`; 74 mục khai báo, 75 file thực tế, không thiếu/thừa/đổi byte. Pilot: cùng manifest và 76 file, gồm source bổ sung, không thiếu/thừa/đổi byte. Receipt transport SHA-256 `e9bf67facc7e6a0debc0d8251460551a26d7cface9a264ae8d78f3ec388bb47f` đúng pin.
- `task/source/source_full.mp4`: 36,971,916 byte, SHA-256 `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`; `ffprobe` exit 0: H.264/AAC, 640×360, 30/1 fps, 1321.215420 giây.
- Plan: 54 shot S0021–S0074 phủ liên tục `[2820,11820)` = 9,000 frame / 300 giây. S0074 gốc `[11679,11980)`; pilot dùng `[11679,11820)` = 141 frame và bỏ 160 frame cuối. Việc full-shot vượt mốc 11820 không phải lỗi plan.
- CAST atlas lịch sử có SHA-256 `e847acb8d30f120bcaffb81b1e5048baf3e32280bcd74e9e5688b20a56149a4e` và 14 pin PNG front/profile duy nhất. **0/14 file tương ứng có trong pilot** tại `task/corrections/identity/r4/assets/cast_b`. Checker yêu cầu SHA đúng, ít nhất 1024 byte và decode PNG; fixture 15 byte không thể đạt PASS.
- Pilot thiếu `task/input`, R6 ledger/atlas/storyboard, R5 storyboard, R4 CAST và SAM2 model, R5 CoTracker model, cùng `task/graph/reuse_bundle/shot_anchor_v1.baseline.api.json`. Ledger lịch sử tại portable handoff tồn tại và được hash, nhưng không phải ledger của pilot. Chỉ có fixture storyboard S0021 trong handoff lịch sử; không có bộ 54 shot, nên không sao chép và không xác nhận Q02.
- `ComfyUI/main.py` và `serve_video14b.py` tồn tại, phân tích cú pháp được. Python do R6 khai báo tại `runtime/video14b/venv/Scripts/python.exe` **không tồn tại**, do đó import runtime là UNKNOWN. Năm weight FLUX/VACE liên quan có file, SHA-256 và header safetensors hợp lệ (chi tiết path/size/hash trong `READINESS.json`); **loadability là UNKNOWN**. R6 nhắm `127.0.0.1:8188`, trong khi server lịch sử mặc định 8210: cấu hình lệch.
- Các probe TCP trực tiếp đến 8188 và 8210 đều timeout trong giới hạn 2 giây; chưa phát HTTP GET. Endpoint ComfyUI, node API và queue là UNKNOWN. Snapshot process không thấy lệnh ComfyUI/video14b; lease instance còn ghi PID 21092 và reservation chưa giải quyết ghi PID 31024, cả hai PID không sống ở thời điểm kiểm tra. Quyền sở hữu lease vẫn UNKNOWN cho tới khi controller helper được audit; không xóa/reconcile lock.

## Lệnh và kết quả

Working directory: `C:/Users/Admin/Documents/Codex/g2b1-readiness/`.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m unittest -v test_readiness
# exit 0; 9/9 test PASS; raw log TESTS-final.txt

python -B readiness.py --output C:/Users/Admin/Documents/Codex/g2b1-readiness/READINESS.json
# exit 2 (BLOCKED có chủ đích); 19 PASS / 25 FAIL / 7 UNKNOWN
```

Negative tests: thiếu CAST, CAST bị đổi byte, fixture PNG 15 byte, source lệch hash, thêm file ngoài manifest, runtime Python vắng, plan có gap, đường dẫn escape/trùng case. Positive synthetic: manifest/source pin, 54-shot plan với S0074 cắt 141 frame, 14 PNG thật decode được. Synthetic fixtures nằm trong write-set và đã dọn sau test. C16 và pilot đều có 0 `.pyc` sau kiểm tra.

## Tự rà soát

Checker từ chối đường dẫn manifest tuyệt đối, traversal, dấu `:`/backslash và mục trùng không phân biệt hoa-thường; inventory từ chối symlink/reparse/nonregular, tên CAST không được chứa đường dẫn hoặc `:`. Output phải là file mới trực tiếp trong write-set và dùng chế độ tạo độc quyền. FAIL là thiếu/sai bằng chứng chặn chạy; UNKNOWN là chưa chứng thực qua phép kiểm chỉ đọc này. Mã không ghi vào pilot, C16, runtime hay lease, và không tự nâng weight hiện hữu thành khả năng chạy mô hình.

Artefact chính: `readiness.py` SHA-256 `b0166ccda1b4ca6a2bac00b3ba7a0a75c0df9ff1c35030a137f02a3f6d7b5e3c`; `test_readiness.py` SHA-256 `3dd6f66c36cbca4e654f9ea755270853e80f94f39c73fac5b693ed0a2bdb4bde`; `READINESS.json` SHA-256 `b6915e05aec0fb57cc15880bf0f796cb867304e324816715f417a1d4fa736657`. Dừng tại đây để root quyết định đường repin/recovery trước mọi media job.
