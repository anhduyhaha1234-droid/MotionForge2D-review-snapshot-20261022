# S03-T03 - PM correction round 1

Resume the same S03-T03 lineage. Do not commit; preserve `channels.json` and
all legacy routes/files.

## Blocking findings

1. Reorder compacts active rows to `0..N-1`, but the approved domain schema's
   `UNIQUE(project_id, position)` also covers archived rows and archive
   preserves position. With positions A=0, B=1 archived, C=2, reorder `[C,A]`
   attempts A=1 and collides with archived B, leaking IntegrityError/500.
   The domain contract only requires a unique non-negative position and owned
   ordering; it does not require gap-free numeric positions. Preserve archived
   positions and map the requested active order onto the sorted existing active
   position slots. Update TASK/API doc/report wording to clarify that logical
   active order is gap-tolerant after archive. Add reorder-after-middle-archive
   and rollback/error regression tests. Do not add a migration or weaken the
   domain-wide uniqueness constraint.

2. Probe metadata is read-only and S05-owned in this task, but VideoItemCreate,
   the route, repository/service, and tests currently accept/write
   `duration_ms`, `width`, `height`, `fps_num`, and `fps_den`. Remove these
   fields from the public create payload and from the S03 create write path;
   keep them only in response DTO/read models for later S05 population. Add a
   test proving extra probe fields are rejected (configure the request model to
   forbid unknown fields if necessary without breaking approved clients).

3. `update_video` validates a source Channel before proving the target Video
   belongs to the requested Project/workspace. Missing/cross-workspace targets
   can therefore return channel-dependent 422 instead of safe 404. Verify
   Project/workspace and target Video ownership before any reference
   validation or mutation. Add cross-workspace and cross-project PATCH tests
   with invalid and foreign Channel IDs; all must be 404 and leave state intact.

4. Repository append retry currently treats any SQLite `UNIQUE constraint
   failed` as a position race. Match only the exact
   `(project_id, position)` uniqueness failure; other unique violations must
   propagate and roll back.

5. `update_video` trims title but omits the repository-level maximum-240
   validation used by create. Apply the same validation before SQL and test
   direct service/repository behavior so DB `IntegrityError` is not the public
   validation mechanism.

6. AC8 evidence is currently false: no S03-T03 bootstrap/upgrade preservation
   test exists. Add a current-head/no-op upgrade test that seeds a Video Item
   with Channel reference, probe metadata, resume data, archived state,
   timestamps/revision/position, runs upgrade to head through a fresh engine,
   and proves exact preservation plus unchanged migration head.

7. Keep repository hook tests for the otherwise unreachable losing-CAS fresh
   read, but also prove the production `VideoItemService` writer reservation is
   entered before validation/current-state reads. Use SQL events or a service
   seam with deterministic events; no sleep/timing assertions. Ensure the
   CREATE/PATCH Channel races and reorder/append production paths exercise the
   real service, not only a bare repository.

## Required verification

Run focused and combined durable tests, legacy regression, Ruff, mypy,
`git diff --check`, and a fresh full 7/7 baseline. Update LOG/REPORT and leave
SUBMITTED for PM review. Do not claim the earlier baseline after these edits.
