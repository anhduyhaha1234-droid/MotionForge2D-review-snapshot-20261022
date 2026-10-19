# S00-T01 - Isolate test data from production-root storage

**Status:** APPROVED  
**Epic:** E00 - Baseline and Change Safety  
**Sprint:** S00 - Isolate and record the baseline  
**Gate:** G1 - Foundation green  
**Depends on:** None

## User outcome

Chạy test không còn tạo, sửa hoặc làm bẩn dữ liệu channel/preset thật trong workspace; hành vi hiện tại của service vẫn được bảo toàn bằng test cô lập.

## Why now

`channels.json` ở root đang chứa nhiều bản ghi test lặp lại. Không thể tin các baseline hoặc migration tiếp theo khi test còn ghi vào dữ liệu production-like dùng chung.

## Required reading

Đọc đầy đủ đúng các file sau:

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/CODEBASE_STRATEGY_REVIEW.md`
3. `app/services/preset_manager.py`
4. `tests/test_preset_manager.py`
5. Các module channel storage và test trực tiếp của chúng được tìm thấy bằng `rg`, chỉ trong phạm vi `app/` và `tests/`.

## Optional evidence

- `channels.json` — chỉ inspect read-only để xác nhận hình thức pollution; không sửa, xóa hoặc normalize file.
- `pyproject.toml` — chỉ đọc test configuration nếu cần fixture design.

Không đọc PRD, Master Plan hoặc các milestone docs; chúng không cần thiết cho task hạ tầng này.

## Allowed write scope

- `tests/` — fixtures và test trực tiếp cho channel/preset storage isolation.
- Module channel/preset persistence cụ thể trong `app/` nếu dependency injection/configuration tối thiểu là bắt buộc.
- `docs/pm/sessions/S00-T01-baseline-isolation/REPORT.md`
- `docs/pm/sessions/S00-T01-baseline-isolation/LOG.md`

## Forbidden scope

- `channels.json` và mọi character image/preset data hiện có.
- Frontend.
- PRD, Master Plan, roadmap, task contract và `PM_REVIEW.md`.
- Chuyển toàn bộ persistence sang SQLite; đó là Epic E01.
- Refactor rộng Preset Manager hoặc thay đổi business behavior.

## Current behavior/evidence

- Root `channels.json` có các bản ghi test lặp lại.
- `app/services/preset_manager.py` và `tests/test_preset_manager.py` đang có user changes chưa được phép ghi đè.
- Baseline gần nhất: Python `144 passed, 6 skipped`; task phải đo lại thay vì giả định.

## Target behavior

- Mỗi test dùng temporary storage riêng qua fixture/configuration/dependency injection.
- Test chạy lặp lại không thay đổi hash/content/timestamp logic của root `channels.json` theo cách do test gây ra.
- Test không phụ thuộc thứ tự và không để lại channel/preset test records trong workspace.
- Existing user changes được giữ nguyên và tích hợp cẩn thận.

## In scope

- Tìm tất cả test trực tiếp ghi channel/preset storage dùng chung.
- Tạo fixture storage tạm và inject path/repository phù hợp.
- Bổ sung regression test chứng minh root data không bị ghi.
- Chạy targeted tests và full non-GPU Python suite.

## Out of scope

- Làm sạch dữ liệu root đã bị pollution.
- SQLite/migration production.
- Sửa lint frontend hoặc warning không liên quan.
- Thay đổi schema/channel UX.

## Implementation constraints

- Không hard-code machine path.
- Dùng pytest temporary directory/fixture phù hợp.
- Không monkeypatch global path theo cách khiến test chạy song song tranh chấp.
- Không xóa hoặc rewrite user data để làm test pass.
- Không dùng skip/xfail để che lỗi.

## Acceptance criteria

- [ ] AC1: Tất cả test channel/preset dùng storage cô lập, không ghi root `channels.json` hoặc real preset data.
- [ ] AC2: Có regression evidence chạy test ít nhất hai lần mà root `channels.json` không thay đổi do test.
- [ ] AC3: Targeted channel/preset tests pass.
- [ ] AC4: Full non-GPU Python suite pass hoặc mọi failure mới được chứng minh không do task; không được submit nếu có regression do task.
- [ ] AC5: Existing user changes trong preset manager/tests/assets được bảo toàn.
- [ ] AC6: `REPORT.md` liệt kê chính xác file thay đổi, commands, results và mọi issue ngoài scope.

## Required validation

Hermes phải ghi hash trước/sau và dùng lệnh tương đương PowerShell sau; có thể điều chỉnh test path sau khi inventory:

```powershell
Get-FileHash channels.json -Algorithm SHA256
pytest -q <targeted channel/preset tests>
pytest -q <targeted channel/preset tests>
Get-FileHash channels.json -Algorithm SHA256
pytest -q -m "not gpu and not sam2 and not integration"
git diff --check
git status --short
```

## Required evidence

- Hash root `channels.json` trước/sau hai lần targeted test.
- Test commands và exact summary.
- Giải thích isolation mechanism.
- Danh sách file thay đổi.
- `git diff --check` result.

## Stop conditions

- Cần sửa hoặc xóa `channels.json`.
- Cần overwrite user changes mà chưa hiểu intent.
- Cần mở write scope sang domain/persistence lớn hơn.
- Không thể xác định đâu là production data và đâu là test data một cách an toàn.
