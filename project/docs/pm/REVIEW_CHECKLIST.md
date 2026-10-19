# PM Review Checklist

## Gate A - Contract

- [ ] Đúng Task ID và đúng session.
- [ ] Không thay đổi ngoài allowed write scope.
- [ ] Không sửa PRD/MP/task contract.
- [ ] Không phá hoặc ghi đè user changes có sẵn.
- [ ] Không có scope creep được ngụy trang thành refactor.

## Gate B - Outcome

- [ ] Từng acceptance criterion có evidence.
- [ ] Happy path hoạt động.
- [ ] Empty/loading/error/retry/recovery states liên quan đã xử lý.
- [ ] Không để mock/stub trong production path ngoài điều task cho phép.

## Gate C - Engineering

- [ ] Architecture phù hợp Master Plan.
- [ ] Durable state có backend authority.
- [ ] Migration an toàn và có test nếu đổi schema.
- [ ] Long job có durable state/checkpoint nếu liên quan.
- [ ] Không có hard-coded machine path/secret.
- [ ] Delete/cleanup nằm trong managed safe paths.

## Gate D - Verification

- [ ] Targeted tests pass.
- [ ] Required regression gates pass.
- [ ] Type/lint/build status được báo trung thực.
- [ ] Screenshot/video/output evidence có nếu task UI/media yêu cầu.
- [ ] `REPORT.md` đầy đủ và `LOG.md` có thể audit.

## Gate E - Decision

Chọn đúng một:

- `APPROVED`: outcome đạt và dependency được mở cho task sau.
- `CHANGES_REQUESTED`: còn lỗi hữu hạn trong cùng scope.
- `REJECTED`: approach sai nền tảng; phải lập task lại.
- `BLOCKED`: cần quyết định hoặc external dependency.
