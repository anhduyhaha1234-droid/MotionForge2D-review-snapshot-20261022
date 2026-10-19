# S00-T03 - Runtime dependencies and portable FFmpeg discovery

**Status:** APPROVED  
**Epic:** E00 - Baseline and Change Safety  
**Sprint:** S00 - Isolate and record the baseline  
**Gate:** G1 - Foundation green  
**Depends on:** S00-T02 APPROVED

## User outcome

MotionForge tìm FFmpeg/ffprobe theo một contract dùng chung, không phụ thuộc username/máy của developer; dependencies đang được runtime import được khai báo đúng core/optional scope và clean-install instructions phản ánh sự thật.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. File task này.
3. `pyproject.toml`
4. `README.md` phần install/run.
5. `app/services/ffmpeg_utils.py`
6. `app/workflow/scene_chunking_service.py`
7. `app/workflow/scene_stitch_service.py`
8. `app/workflow/audio_dubbing_service.py`
9. Các test trực tiếp của ba workflow/service trên.
10. `docs/quality/QUALITY_BASELINE.md` để giữ baseline gate trung thực.

## Optional evidence

- `tests/conftest.py` — chỉ khi cần hiểu test FFmpeg PATH behavior.
- Các caller của `_find_ffmpeg/_find_ffprobe` tìm bằng `rg` — chỉ đọc dependency trực tiếp.

## Allowed write scope

- `pyproject.toml`
- `README.md` — chỉ phần dependency/install/FFmpeg configuration.
- `app/services/ffmpeg_utils.py`
- `app/workflow/scene_chunking_service.py`
- `app/workflow/scene_stitch_service.py`
- `app/workflow/audio_dubbing_service.py`
- Targeted tests cho discovery/dependency behavior trong `tests/`.
- Session `REPORT.md` và `LOG.md`.

## Forbidden scope

- Frontend.
- Dubbing UX/API/business behavior.
- Cài đặt package hoặc update lock ngoài việc sửa declaration.
- Thay đổi media commands/codecs/timebase.
- Sửa mypy/eslint baseline ngoài lỗi trực tiếp do task tạo.
- PRD/MP/Roadmap/TASK/PM_REVIEW.
- User data, channels và character assets.

## Target contract

1. `app.services.ffmpeg_utils` là authority duy nhất cho FFmpeg/ffprobe discovery.
2. Resolution order rõ ràng và test được:
   - explicit environment override (`MOTIONFORGE_FFMPEG`/`MOTIONFORGE_FFPROBE`);
   - executable trên `PATH`;
   - Windows WinGet Links dựa trên `LOCALAPPDATA`;
   - portable app-managed location nếu đã có contract hợp lý trong repo;
   - nếu không có thì lỗi actionable, không đoán username.
3. Explicit override phải kiểm tra file tồn tại/executable suitability và không silently fallback khi override invalid.
4. Các workflow không còn private discovery copy/hard-coded `C:\Users\Admin...`.
5. Core dependencies vẫn tối thiểu. `edge-tts` và Whisper/dubbing dependencies được khai báo optional theo Phase 2, hoặc import được guard với actionable error. Không buộc Phase 1 cài model dubbing nặng.

## Acceptance criteria

- [ ] AC1: Không còn hard-coded user-specific FFmpeg/ffprobe path trong `app/`.
- [ ] AC2: Ba workflow dùng shared discovery authority, behavior media ngoài discovery không đổi.
- [ ] AC3: Tests cover valid override, invalid override, PATH, WinGet/LOCALAPPDATA and not-found error without relying on machine installation.
- [ ] AC4: Runtime imports absent from package contract are declared in the correct optional group or guarded/documented consistently.
- [ ] AC5: README gives clean, portable install/config instructions without machine-specific paths.
- [ ] AC6: Targeted tests, full non-GPU tests and Ruff pass; type/build baseline has no new failure attributable to task.
- [ ] AC7: Existing user/S00 changes and production data remain untouched; report/log complete.

## Required validation

```powershell
rg -n "C:\\Users\\Admin|_find_ffmpeg|_find_ffprobe" app
python -m pytest -q <targeted tests>
python -m pytest -q -m "not gpu and not sam2 and not integration"
python -m ruff check app tests
python -m mypy app
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
git status --short
```

Mypy/overall quality runner may remain red only for the exact approved baseline failures. Hermes must compare counts/files and report deltas, not claim a false green.

## Stop conditions

- Need to install or download FFmpeg/packages/models.
- Need to redesign dubbing or modify API behavior.
- Need to change command/codecs/timebase.
- Need to touch files outside allowed scope.
- Existing dirty changes overlap in a way that cannot be safely preserved.
