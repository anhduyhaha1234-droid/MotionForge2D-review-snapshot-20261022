# S00-T01 - PM Review

**Decision:** APPROVED  
**Reviewed:** 2026-08-03  
**Reviewer:** PM/Codex

## Scope review

Round 2 nằm trong allowed write scope. User changes trong preset manager, preset tests, `channels.json` và character assets được giữ. Không còn write-capable call trên production preset path trong tests.

## Acceptance review

- AC1-AC6 đạt.
- Local unpatched client đã được bỏ; toàn module dùng conftest client với `_patch_project_root`.
- Production preset directory chỉ được snapshot read-only.
- Endpoint regression test chứng minh assets được tạo dưới temp project root.
- Root channel và production preset assets không thay đổi sau hai targeted runs.

## Engineering review

Constructor injection cho `ChannelService` là thay đổi nhỏ, backward-compatible và phù hợp task. Channel fixture dùng `tmp_path`; preset unit tests dùng temporary asset root; endpoint tests dùng patched application config. Không có schema/API behavior change ngoài optional DI parameter.

## Validation review

PM independently reran:

- Targeted twice: `24 passed, 2 warnings` mỗi lần.
- Full non-GPU: `141 passed, 6 skipped, 7 deselected, 14 warnings`.
- `git diff --check`: exit 0.
- `channels.json` SHA256 unchanged: `DD7AAE26096902EFF74986B36554957D87EB8E60C5E8FF8048064C31655EB555`.
- Production preset manifest unchanged: 28 PNG files, identical per-file SHA256.

Warnings là baseline đã biết và không do task tạo ra.

## Required changes

None. Previous round findings were corrected.

## Dependency release

S00-T01 dependency is released. PM may now prepare and activate `S00-T02`; Hermes must not start it until its own session packet and start prompt are issued.
