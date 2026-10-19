# Kết quả 9router / Antigravity — 17/10/2026

Đã dùng được Gemini 3.8 Flash (High) qua 9router, có streaming, gọi hàm và round-robin giữa hai tài khoản. Kiểm tra trực tiếp sau sửa lúc 11:40 UTC+7, ngày17/10/2026.

## Cấu hình client

- Loại API: OpenAI-compatible Chat Completions.
- Base URL: http://127.0.0.1:20128/v1
- Model: ag/gemini-3.8-flash-high
- API key: dùng gateway key hiện có trong trang API Keys của 9router; không dùng Google token.
- Chat endpoint: POST /v1/chat/completions.
- Có thể bật stream=true và gửi tools theo OpenAI Chat Completions.

Alias ag/gemini-3.8-flash cũng đã trả lời thành công trước sửa. Model ID Google trả về trong response là gemini-3.8-flash-n; request test đã chọn rõ ag/gemini-3.8-flash-high.

## Round-robin đã bật và kiểm chứng

providerStrategies.antigravity:
```json
{"fallbackStrategy":"round-robin","stickyRoundRobinLimit":1}
```

Chỉ thay strategy Antigravity; các setting và provider khác được so sánh trước/sau, không đổi. Không cần restart cho thay đổi strategy.

Sau sửa streaming, usageHistory ghi:
- ID63140: tài khoản6c18a210, status ok, stream đúng marker, HTTP200,4.093giây.
- ID63141: tài khoản68c0064d, status ok, gọi router_ping đúng argument, HTTP200,5.407giây.
- ID63142: tài khoản6c18a210, status ok, trả đúng kết quả tool, HTTP200,3.984giây.

Đây là luân phiên A→B→A thật, gồm cả hai bước tool call/result qua hai tài khoản khác nhau. Hai tài khoản đều active, lastError=null sau kiểm tra. Tài khoản thêm sau sẽ tham gia strategy này khi active và đủ điều kiện cho model. Router bỏ qua tài khoản inactive hoặc đang bị khóa/quota cho model; round-robin áp dụng mỗi lần chọn tài khoản, không bảo đảm tất cả request đều thành công khi Google từ chối.

## Lỗi đã sửa

9router0.5.95 dịch Antigravity SSE sang OpenAI nhưng không phát data: [DONE] ở EOF. Đã tái hiện hai lần trực tiếp. Bản sửa chỉ thêm sentinel cuối trong nhánh Antigravity→OpenAI; giữ nhánh Gemini native, Claude và provider khác.

File thay: app/.next-cli-build/server/chunks/8895.js, module71857. Đã backup preimage, kiểm tra đảo diff khôi phục đúng byte, node --check, rồi restart riêng 9router. Không đổi credentials hoặc model entitlement. Các bản vá CommandCode/OpenCode trước đây giữ nguyên hash; bài kiểm tra cache hiện có6/6 đạt.

Regression dùng bộ chuyển đổi/translator thật, thay biên ghi usage DB bằng no-op:7/7 đạt (UTF-8 bị chia chunk, upstream có DONE, tool call, EOF thiếu newline, Claude/native/other-provider controls). Live sau sửa3/3 đạt, stream có đúng kết thúc mong đợi. Đây là kiểm tra smoke, không phải cam kết mọi model hoặc mọi tải đều thành công.

## Gemini mới nhất / lỗi404

Nguồn chính thức công bố Gemini4Argon, còn kết nối Antigravity đang dùng không cung cấp model này. Lần thử ag/gemini-4-argon-high trả upstream404 NOT_FOUND; router trình bày ngoài thành503 với cooldown model. API fetchAvailableModels của cả hai tài khoản trả200 nhưng không có Argon. Không có bằng chứng đây là lỗi đăng nhập; Gemini3.8 chạy thành công và lỗi account cũ đã tự được xóa sau request hợp lệ.

Tài liệu Google phân biệt Antigravity App/CLI/extensions và IDE; Argon không có trong Antigravity IDE. Transport của 9router đang dùng đường IDE. Chỉ thêm tên model vào catalog hoặc cập nhật danh sách không tạo quyền truy cập ở Google. Không đổi token/client identity hoặc gọi reset/mua quota để vượt hạn chế.

Nguồn:
- [Google Antigravity: chọn model](https://antigravity.google/docs/models)
- [9router: registry Antigravity](https://github.com/decolua/9router/blob/master/open-sse/providers/registry/antigravity.js)
- [9router: xử lý stream](https://github.com/decolua/9router/blob/master/open-sse/utils/stream.js)

Npm latest được kiểm tra là0.5.104; bản đang chạy giữ0.5.95 cùng bản vá hẹp để bảo toàn các sửa CommandCode/OpenCode hiện có. Bản vá bundle cục bộ có thể bị ghi đè khi nâng cấp9router, nên kiểm tra streaming lại sau update.

## Bằng chứng

- [Live smoke sau sửa](smoke-high-fixed-01.json)
- [Regression bản đã cài](sse-fixture-installed.json)
- [Cấu hình round-robin](round-robin-config.json)
- [Model Google thực sự trả về cho hai tài khoản](upstream-model-availability.json)
- [Receipt, SHA256 và đường dẫn preimage](sse-fix-receipt.json)

Lịch MotionForge vẫn PAUSED; không được bật lại trong việc này.

