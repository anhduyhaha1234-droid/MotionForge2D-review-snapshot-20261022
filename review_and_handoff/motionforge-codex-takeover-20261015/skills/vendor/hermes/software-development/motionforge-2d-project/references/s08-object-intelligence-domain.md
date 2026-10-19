# S08 Object Intelligence Domain (S08-T01, worktree s08-integration)

Durable video-global `ObjectRole` identity + scene/frame evidence in
`ObjectOccurrence`. Built under the S08 sprint contract; T02…T06 build on it.

## Schema (migration `e7f8a9b0c1d2`, down_revision `d5e6f7a8b9c0`, REVERSIBLE)

`object_role`:
- id String(36) UUID pk; workspace_id/project_id/video_item_id FKs RESTRICT
- source_generation String(64) NOT NULL (evidence lineage ownership)
- name String(240) — display ONLY, never authority
- kind IN ('character','prop','other') default 'character'
- status IN ('suggested','confirmed','superseded') default 'suggested'
- supersedes_role_id self-FK RESTRICT; legacy_object_id String(255) NULL;
  legacy_scene_id Integer NULL (compat refs, NOT authority)
- idempotency_key String(255) NULL with PARTIAL unique index
  `uq_object_role_workspace_idempotency` (workspace_id, idempotency_key) WHERE
  idempotency_key IS NOT NULL
- revision (CAS) + created_at/updated_at (TimestampMixin)

`object_occurrence`:
- role_id FK CASCADE; scene_id FK RESTRICT (stable Scene identity);
  frame_index/time_ms canonical coordinates; bbox_x/y/w/h ints
- confidence Float CHECK 0..1; confidence_source IN
  ('model','detector','user','manual','derived'); algorithm/algorithm_version;
  reasons_json Text default '[]'; review_state IN
  ('unreviewed','accepted','rejected','edited')
- UNIQUE(role_id, scene_id, frame_index) = natural idempotency key

## Repository (`app/persistence/object_intelligence.py`)

- `ObjectIntelligenceRepository(session)`; frozen dataclass records
  (RoleRecord/OccurrenceRecord/LegacyMappingItem/LegacyObjectMapping).
- Fail-closed ownership: `_assert_role_ownership(workspace_id, project_id,
  video_item_id)` and `_assert_occurrence_ownership(workspace_id, role_id,
  scene_id)` raise `OwnershipMismatchError`; workspace mismatch treated as
  not-found on reads (no existence leak).
- `create_role(...)` returns `(RoleRecord, created: bool)`; idempotency key
  replay + `begin_nested()` IntegrityError fallback → returns existing.
- `update_role` CAS: stale revision → `RoleConflictError`; superseded is
  terminal; status='superseded' REQUIRES supersedes_role_id. Status changes
  are explicit (suggested never auto-promotes).
- `create_occurrence` natural-key idempotency; `update_occurrence` CAS.
- `map_legacy_objects(project_id, legacy_dict)` — PURE, no DB writes; input
  legacy project.json `objects[]` (TrackedObject shape); outputs ephemeral
  uuid4 role ids + occurrence_evidence; note string declares read-only.
  Handles Pydantic enum kinds via `getattr(kind, "value", kind)`.

## API (`/api/v2/object-intelligence`, router in app/api/app.py)

- POST "" | "/" | "/roles" | "/roles/" → create role (201; replay → 200 via
  `response: Response` param + `response.status_code = 200`)
- GET "" | "/" | "/roles" | "/roles/" → list (video_item_id/status/limit/offset)
- GET|PATCH /roles/{role_id:uuid} (404/409/422 mapping; rollback before raise)
- GET|POST /roles/{role_id:uuid}/occurrences (natural-key replay → 200)
- PATCH /roles/{role_id:uuid}/occurrences/{occurrence_id:uuid}
- GET /legacy-mapping/{project_id} — read-only compat mapping; loads legacy
  project.json via pwf.get_project (FileNotFoundError → 404); ZERO writes.

Route registration: use `{role_id:uuid}` converters like durable_characters;
declare collection aliases ("", "/", "/roles", "/roles/") on the SAME handler
when tests/consumers may call either.

## Validation recipe (S08-T01 evidence trail)

1. Focused: `python -m pytest tests/test_object_intelligence_domain.py -q -p
   no:cacheprovider --basetemp=<isolated>` (21 tests)
2. Migration round trip on fresh temp DB:
   `export MOTIONFORGE_DATABASE_URL=sqlite:///<temp>/migration.db` →
   upgrade head → downgrade d5e6f7a8b9c0 → upgrade head; then UNSET the env
   var (see SKILL.md pitfall).
3. Regressions: test_persistence_bootstrap, test_durable_job_persistence,
   test_project_crud, test_video_item_crud (160 tests) + S05 suite (41) —
   S05 wiring test MUST use a SHALLOW basetemp (MAX_PATH).
4. `ruff check` on changed files; `mypy app` (strict); `git diff --check`.

## Session pitfalls found (S08-T01)

- New head revision breaks hard-coded head/table-set assertions in
  test_persistence_bootstrap.py AND test_durable_job_persistence.py — update
  expectations (S08_HEAD_TABLES, head revision) as required schema-change
  maintenance, and document it in REPORT.
- Legacy project.json objects in tests need `selection.mode` (SelectionInput
  requires it) or the mapping endpoint 500s.
- FastAPI 0.139/Starlette 1.3 `_IncludedRouter` wrappers in app.routes have no
  `.path`; debug via the router module's `router.routes`.
- Idempotent-replay 200 must use the `response: Response` parameter pattern,
  not returning `Response` objects (mypy strict).
