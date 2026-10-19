# <Task ID> - <Task name>

**Status:** PLANNED  
**Epic:** <Epic ID>  
**Sprint:** <Sprint ID>  
**Gate:** <Quality gate>  
**Depends on:** <Approved Task IDs or None>

## User outcome

<Một kết quả người dùng/hệ thống có thể review.>

## Why now

<Lý do task này đứng ở vị trí hiện tại trong dependency chain.>

## Required reading

Chỉ đọc đầy đủ các file sau trước khi code:

1. `docs/pm/SESSION_PROTOCOL.md`
2. `<specific contract/spec>`
3. `<relevant source files>`

## Optional evidence

- `<file>` — chỉ đọc khi `<condition>`.

Không đọc tài liệu khác nếu không có blocker cần PM mở scope.

## Allowed write scope

- `<path or exact file>`
- `<session>/REPORT.md`
- `<session>/LOG.md`

## Forbidden scope

- PRD, Master Plan, PM roadmap và task contract.
- `<explicit exclusions>`

## Current behavior/evidence

<Điểm xuất phát có dẫn chứng.>

## Target behavior

<Contract sau khi hoàn thành.>

## In scope

- ...

## Out of scope

- ...

## Implementation constraints

- ...

## Acceptance criteria

- [ ] AC1 ...
- [ ] AC2 ...
- [ ] AC3 ...

## Required validation

```powershell
<commands>
```

## Required evidence

- Test command và kết quả.
- Danh sách file thay đổi.
- Migration/output/screenshot nếu phù hợp.

## Stop conditions

- Cần mở write scope.
- Có nguy cơ mất dữ liệu hoặc phá backward compatibility.
- Dependency chưa approved.
- Requirement mâu thuẫn hoặc acceptance criteria không thể kiểm chứng.
