# MotionForge 2D Local Orchestrator

Orchestrator này tự động hóa việc mở và tiếp tục Hermes session nhưng không thay thế PM gate.

Mọi session được cấu hình ở reasoning effort `max`; không dùng mức `medium`.

## Bất biến

- Một Task ID mới luôn tạo một Hermes session mới.
- Sessions use Hermes source `cli` so they remain visible in Hermes Desktop history.
- `CHANGES_REQUESTED` tiếp tục đúng session ID của task đó.
- Chỉ PM được ghi `APPROVED` và phát hành task kế tiếp.
- Không tự commit, push, merge, xóa dữ liệu hoặc sửa roadmap.
- Mặc định mọi lệnh là dry-run; phải thêm `-Execute` mới gọi Hermes.

## Runtime files

State, lock, stdout/stderr và envelopes được ghi dưới `output/pm-automation/`, đã nằm trong vùng ignored `output/`.

## Commands

Kiểm tra môi trường và packet:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation/orchestrator.ps1 `
  -Action Validate `
  -SessionPath docs/pm/sessions/S00-T02-quality-baseline
```

Xem state:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation/orchestrator.ps1 -Action Status
```

Preview session mới, không gọi Hermes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation/orchestrator.ps1 `
  -Action Start `
  -SessionPath docs/pm/sessions/S00-T03-runtime-dependencies
```

Chạy thật sau khi user xác nhận:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation/orchestrator.ps1 `
  -Action Start `
  -SessionPath docs/pm/sessions/S00-T03-runtime-dependencies `
  -Execute
```

Tiếp tục cùng session sau PM correction:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation/orchestrator.ps1 `
  -Action Resume `
  -CorrectionPromptPath output/pm-automation/inbox/S00-T03-correction-01.txt `
  -Execute
```

Xóa active state chỉ sau khi PM đã đóng task:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation/orchestrator.ps1 `
  -Action Close `
  -TaskId S00-T03 `
  -Execute
```

## Trước lần chạy thật đầu tiên

1. Chạy `hermes doctor` và xử lý runtime warning phù hợp.
2. Chạy một prompt read-only nhỏ để xác nhận custom model endpoint.
3. Dùng một sandbox documentation task để xác nhận session ID parser.
4. Không thử trực tiếp trên roadmap task cho tới khi ba bước trên đạt.
