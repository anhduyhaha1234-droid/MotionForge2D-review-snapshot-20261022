# S04-T05 - Guided project shell and durable resume location

**Status:** READY
**Epic:** E02 - Production Management and Product Shell
**Sprint:** S04 - New UI shell
**Depends on:** S04-T04 at commit `a43b20d`

## User outcome

The project shell shows the exact six production stages and allows safe backward navigation without losing the durable resume position.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/pm/sessions/S04-T05-guided-shell/TASK.md`
3. `docs/architecture/UI_UX_DESIGN_STANDARD.md`
4. `frontend/AGENTS.md`
5. `frontend/src/components/layout/StageRail.tsx`
6. `frontend/src/stores/project.ts`
7. `frontend/src/lib/api.ts`
8. `app/api/routes/durable_projects.py` and the `ProjectUpdate` schema

## Allowed write scope

- `frontend/src/components/layout/StageRail.tsx`
- `frontend/src/stores/project.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/app/(app)/projects/[id]/page.tsx`
- focused frontend tests for these files, if the existing test layout supports them
- `docs/pm/sessions/S04-T05-guided-shell/LOG.md`
- `docs/pm/sessions/S04-T05-guided-shell/REPORT.md`

## Forbidden scope

- `channels.json` and `data/`
- backend routes, schemas, persistence or migrations
- roadmap, task contract and PM review
- commits, pushes and creation of the next task packet

## Acceptance criteria

1. StageRail displays exactly: `Nhập video`, `Đối tượng`, `Demo thay thế`, `Áp dụng`, `Kiểm tra`, `Xuất 4K`.
2. Display stages map explicitly to the existing application screen/domain states; duplicated screen mappings must use unique display IDs.
3. Users may navigate only to the current or completed/readiness-approved stage; disabled stages expose an accessible reason/tool-tip.
4. Resume persistence calls the configured backend base URL through the typed API client. No raw relative `/api/v2/...` fetch is allowed.
5. Durable PATCH includes the required `revision`, handles `409` by refetching, and never swallows persistence failure silently.
6. Legacy/non-UUID project IDs are not sent to the durable UUID endpoint.
7. `channels.json` remains byte-identical and unstaged.
8. Typecheck, lint, build, focused tests and the fresh 7/7 quality baseline pass.

## Handoff

Finish with `REPORT.md` status `SUBMITTED`, append real evidence to `LOG.md`, then exit. Do not approve or commit.
