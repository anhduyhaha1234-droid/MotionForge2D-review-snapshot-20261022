# S03-T03 - PM correction round 2

Resume the same S03-T03 lineage. Do not commit; preserve `channels.json` and
legacy routes/files. Close these final evidence inconsistencies only:

1. `TASK.md` AC3 still says numeric positions must be contiguous/no-gap, while
   the corrected domain policy intentionally preserves archived slots and is
   gap-tolerant. Formally revise AC3 to require stable logical active ordering,
   unique non-negative positions, no newly introduced gaps, and preservation
   of archived positions. Fix every stale REPORT/API-doc claim such as “no
   holes” so evidence matches behavior and the domain contract exactly.

2. The S03-T03 no-op upgrade test claims exact preservation but seeds automatic
   timestamps and only asserts non-null. Seed explicit distinguishable
   `created_at`, `updated_at`, and `archived_at` values, snapshot every field,
   upgrade through a fresh engine, and compare the full before/after record
   exactly (with a documented SQLite timezone-normalization comparison).

3. `_is_position_unique_failure` must match the exact SQLite column pair for
   `video_item.project_id, video_item.position`, not merely the substring
   `video_item.position`. Test reordered/partial text and the legacy-id unique
   error remain false while the exact position pair is true.

Run focused Video/bootstrap tests, Ruff, mypy, diff check, and a fresh full 7/7
baseline after edits. Update LOG/REPORT to SUBMITTED; do not reuse prior run.
