# S00-T02 - Reproducible quality baseline runner

**Status:** APPROVED  
**Epic:** E00 - Baseline and Change Safety  
**Sprint:** S00 - Isolate and record the baseline  
**Gate:** G1 - Foundation green  
**Depends on:** S00-T01 APPROVED

## User outcome

PM và Hermes có một lệnh PowerShell duy nhất để chạy các quality gates hiện tại, nhận kết quả pass/fail trung thực cho từng gate và tạo report máy đọc/người đọc được mà không dừng ở lỗi đầu tiên.

## Why now

Các lệnh kiểm tra đang phân tán và tài liệu cũ báo những baseline khác nhau. Trước khi sửa dependencies hoặc lint, cần một runner lặp lại được để đo chính xác hiện trạng và so sánh các task sau.

## Required reading

Đọc đầy đủ đúng các file sau:

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/pm/sessions/S00-T02-quality-baseline/TASK.md`
3. `pyproject.toml`
4. `frontend/package.json`
5. `.gitignore`
6. `frontend/.gitignore`
7. `frontend/AGENTS.md`
8. Chỉ các local Next.js docs cần thiết để xác nhận lệnh build của phiên bản đang cài, theo yêu cầu trong `frontend/AGENTS.md`.

## Optional evidence

- `docs/pm/sessions/S00-T01-baseline-isolation/REPORT.md` — chỉ dùng để so baseline Python gần nhất.
- `README.md` và `frontend/README.md` — chỉ dùng để đối chiếu command hiện có, không coi là requirement.
- `frontend/package-lock.json` — chỉ inspect package manager/lockfile, không sửa.

Không đọc milestone/performance documents cũ; chúng không phải baseline hiện tại.

## Allowed write scope

- `scripts/quality-baseline.ps1`
- `.gitignore` — chỉ được thêm ignore rule cho generated quality artifacts nếu cần.
- `docs/quality/QUALITY_BASELINE.md`
- `docs/quality/QUALITY_BASELINE.schema.json` nếu chọn xuất JSON có schema; không bắt buộc.
- `docs/pm/sessions/S00-T02-quality-baseline/REPORT.md`
- `docs/pm/sessions/S00-T02-quality-baseline/LOG.md`

Generated runtime artifacts chỉ được ghi dưới `output/quality-baseline/` và không commit.

## Forbidden scope

- Mọi production source trong `app/`, `frontend/src/` và `tests/`.
- `pyproject.toml`, `frontend/package.json`, lockfile và dependency versions.
- Sửa lint/type/build/test failures hoặc warnings.
- PRD, Master Plan, task roadmap ngoài chuyển trạng thái do PM quản lý và `PM_REVIEW.md`.
- Chạy GPU/SAM2/integration/E2E tests.

## Current behavior/evidence

- Python non-GPU baseline gần nhất: `141 passed, 6 skipped, 7 deselected, 14 warnings`.
- TypeScript typecheck gần nhất đã pass.
- ESLint gần nhất fail với `28 errors, 21 warnings` nhưng phải đo lại.
- Next.js build từng pass nhưng phải đo lại.
- Chưa có một runner giữ exit code, duration và output của từng gate khi gate trước fail.

## Target behavior

`powershell -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` chạy tuần tự các gate, capture stdout/stderr/exit code/duration riêng, tiếp tục qua mọi gate, tạo artifact report và cuối cùng trả exit code khác 0 nếu có required gate fail.

Required gates:

1. Environment/preflight: Python, Node và npm versions; kiểm tra frontend dependencies tồn tại, nhưng không tự install.
2. Python tests: `python -m pytest -q -m "not gpu and not sam2 and not integration"`.
3. Python lint: `python -m ruff check app tests`.
4. Python typing: `python -m mypy app`.
5. Frontend typecheck: `npx tsc --noEmit` tại `frontend/`.
6. Frontend lint: `npm run lint` tại `frontend/`.
7. Frontend production build: `npm run build` tại `frontend/`.

## In scope

- PowerShell runner tương thích Windows workspace hiện tại.
- Xác định repo root từ vị trí script, không phụ thuộc current working directory.
- Capture exit code, started/finished time, duration và log path cho từng gate.
- Tạo summary JSON dưới `output/quality-baseline/` và logs riêng từng gate.
- Cập nhật `docs/quality/QUALITY_BASELINE.md` bằng kết quả thực chạy trong session này, gồm known failures nhưng không sửa chúng.
- Có chế độ/help hoặc comment usage đủ rõ để Hermes/task sau dùng lại.

## Out of scope

- CI/CD service.
- Auto-install dependencies.
- Parallel gate execution.
- Coverage threshold.
- Benchmark GPU/media quality.
- Fix bất kỳ gate nào.

## Implementation constraints

- Không dùng shell chaining khiến mất exit code của từng command.
- Không ghi machine-specific absolute path vào tracked report.
- Không ghi secret/environment dump.
- Runner phải tiếp tục sau gate fail và tổng hợp tất cả results.
- Runner phải trả non-zero khi một required gate fail, nhưng artifact/report vẫn phải hoàn chỉnh.
- Không sửa source để làm baseline xanh.
- Generated logs/JSON không được đặt trong source directories.
- Report phải phân biệt `PASS`, `FAIL`, `SKIPPED/PREFLIGHT_BLOCKED`.

## Acceptance criteria

- [ ] AC1: Một lệnh chạy được từ repo root hoặc thư mục khác và xác định đúng workspace.
- [ ] AC2: Tất cả 7 gate có record riêng gồm command, exit code, duration, status và log path; fail một gate không chặn gate sau.
- [ ] AC3: Runner trả exit code 0 chỉ khi tất cả required gates pass; baseline hiện tại có failure thì phải trả non-zero.
- [ ] AC4: Generated artifacts chỉ nằm dưới `output/quality-baseline/` và bị ignore.
- [ ] AC5: `QUALITY_BASELINE.md` ghi exact results hiện tại, timestamp, tool versions, known failures/warnings và cách chạy lại; không tuyên bố gate xanh sai sự thật.
- [ ] AC6: Chạy runner hai lần thành công về mặt orchestration; cả hai lần tạo report đầy đủ và không sửa production data/source.
- [ ] AC7: Script syntax/error handling được test; `git diff --check` pass.

## Required validation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
$firstExit = $LASTEXITCODE
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
$secondExit = $LASTEXITCODE
Get-ChildItem output/quality-baseline -Recurse
git diff --check
git status --short
```

Nếu baseline có gate fail, `$firstExit` và `$secondExit` non-zero là expected. Hermes phải xác minh report của cả hai lần vẫn chứa đủ 7 gate, thay vì dùng overall exit code làm lý do dừng session.

## Required evidence

- Exact tool versions và commands resolved.
- Exit code/duration/status của từng gate cho hai runs.
- Đường dẫn summary/log artifacts.
- Bằng chứng runner tiếp tục sau failure.
- Danh sách tracked file changes.
- Xác nhận không sửa production source/data.

## Stop conditions

- Cần sửa source hoặc dependency để runner hoạt động.
- Cần chạy/install tool ngoài dependencies đã khai báo.
- Build/test có hành động thay đổi production data.
- Cần thay đổi danh sách required gates hoặc bỏ qua một failure.
