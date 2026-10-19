# S03-T04 - Project summary read model for dashboard

**Status:** APPROVED
**Epic:** E02 - Production Management and Product Shell
**Sprint:** S03 - Production management API
**Gate:** G2 - Production shell
**Depends on:** S03-T03 (APPROVED)

## User outcome

The upcoming dashboard and Project Overview can load one honest, durable,
workspace-scoped summary containing project identity, channel references,
Video Item state, a deterministic next action, active jobs, recent activity,
and known managed storage without navigating the filesystem.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/pm/ROADMAP.md` (E02/S03/S04)
3. `docs/PRODUCT_REQUIREMENTS_V2.md` (Home, Project Detail, FR-PM)
4. `docs/architecture/UI_UX_DESIGN_STANDARD.md`
5. `docs/architecture/PROJECT_API.md`
6. `docs/architecture/VIDEO_ITEM_API.md`
7. `docs/architecture/DURABLE_JOB_CONTRACT.md`
8. Current Project, Channel, VideoItem, Job, and Artifact models/repositories

## Route contract

Add read-only routes only under the isolated durable namespace:

- `GET /api/v2/projects/summaries`
- `GET /api/v2/projects/{project_id:uuid}/summary`

The collection defaults to active projects, supports exact project-status
filtering plus bounded `limit`/`offset`, and has deterministic ordering by
`last_activity_at DESC`, then project ID. The item route may read archived
Projects. Do not change any legacy `/api/projects` route.

## Read-model contract

- Derive results live from durable rows in one consistent read boundary. Do
  not persist aggregates, create a cache/table/migration, or write files.
- Include Project identity/status/revision/timestamps and source/production
  Channel display references. Archived referenced Channels remain visible.
- Include active/archived/total/completed/attention counts and `by_status` with
  all 13 Video Item statuses, including zeroes. Completion is
  `completed / active * 100` (zero when there are no active videos); never
  invent ordinal pipeline progress.
- Include one stable semantic `next_action` code, optional Video Item ID,
  `enabled`, and optional blocker code. Backend returns codes, not localized UI
  prose. Select deterministically from state/position/ID. Archived Projects use
  `none`; unavailable future capabilities remain disabled with a blocker.
- Include a bounded newest active-job list and full active-job count. Exact
  active states are `pending`, `queued`, `running`, `cancelling`. Include jobs
  owned by the Project or its real Video Items only; reject orphan and
  cross-workspace polymorphic owners. Expose no internal/error JSON.
- Include `last_activity_at` from durable Project/Video/Job activity.
- Storage aggregation must deduplicate Artifact IDs, never expose paths, state
  a policy for missing/trash/unknown sizes, and never count another workspace.
- Collection and item routes must share one summary algorithm, avoid count/byte
  multiplication from joins, and use a query count bounded independently of
  the number of Projects (no N+1).
- Do not fabricate QC blockers, output versions, human activity, ETA, or
  capability/system readiness before their authoritative domains exist.

## Acceptance criteria

1. Both routes are read-only, workspace-scoped, and return safe 404 for a
   cross-workspace Project.
2. DTO is exact and leaks no ORM object, internal JSON, absolute path, or
   sensitive job error.
3. Video counts/status map/completion ratio are exact without join inflation.
4. Next action is deterministic, state-driven, capability-honest, and points
   to the correct Video Item when applicable.
5. Active job membership/count/order are exact and bounded; orphan or foreign
   owners are excluded.
6. Storage totals deduplicate Artifact IDs and document missing/trash/unknown
   size behavior.
7. `last_activity_at`, pagination, and tie ordering are deterministic.
8. Archived Project/detail and archived Channel reference behavior are correct.
9. Collection query count is bounded and item/collection summaries agree.
10. No migration, persistent aggregate, DB/filesystem/JSON write, or legacy
    route behavior change.
11. Focused, combined, legacy regression, Ruff, mypy, diff-check, and the full
    mandatory quality baseline all pass.
12. `channels.json` remains byte-identical and unstaged.

## Owned scope

Expected new files: summary repository/service, v2 route, API contract doc, and
focused tests. Minimal registration/schema/export/conftest edits are allowed.
Do not edit ORM models, migrations, worker transitions, frontend, legacy
routes, or `channels.json`. Do not commit. Leave the report `SUBMITTED` for PM.
