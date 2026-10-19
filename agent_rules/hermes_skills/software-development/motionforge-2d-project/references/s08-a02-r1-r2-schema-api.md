# S08-A02-T01-R2 — Structural Evidence Schema & API on the verified C1 core

Use when building the schema/API layer on top of a manager-verified persistence core (the R2
pattern), or when authoring strict FastAPI routers with JSON NaN/Infinity rejection plus stable
error mapping. Session `20260820_043341_c2c01a` (ocg/deepseek-v4-flash, reasoning max) delivered
R2; manager verified independently (API 50 / combined 205 / full 446 passed; baseline 7/7 Run
20260820-053350).

## R2 boundary (the discipline that keeps a verified core safe)

- R2 ONLY creates `app/schemas/structural_evidence.py`, `app/api/routes/structural_evidence.py`,
  `tests/test_s08_a02_structural_evidence_api.py`; modifies `app/api/app.py` for import +
  `include_router` ONLY. Persistence, migration, `deps.py`, frontend, the 8 pre-existing head-bump
  test files, MAIN — all forbidden.
- If R2 exposes a CORE bug, it STOPS and reports a C1-core-correction finding; it never silently
  patches persistence from the API task. No core bug was found in this run.
- Defaults: current generation + ACTIVE record only; historical access is explicit AND read-only;
  never mix historical into current lists. **No DELETE endpoints anywhere.**

## Strict Pydantic v2 schema rules (all mandatory)

- `model_config = ConfigDict(extra="forbid")` on a base model; every request inherits it
  (unknown field → 422, proven by a test).
- Finite numbers only: `Field(..., allow_inf_nan=False)` per float PLUS a recursive finite-walk
  over JSON payload dicts — a JSON literal `NaN`/`Infinity` bypasses Pydantic float coercion, so
  the walk is the actual guard (asserted by tests).
- Enums/patterns DERIVED from `app/persistence/models.py` constants (OBJECT_KINDS, visibility,
  CONTACT_KINDS, confidence sources) — one authority, no duplicated taxonomy literals.
- frame/time non-negative, `end >= start`; confidence 0..1; bounded algorithm/version/key strings;
  `reasons: list[str]`; `provenance: dict`.
- Client CANNOT supply `logical_id` or `source_generation` — they are server/repo-owned and simply
  absent from request models (a test pins the 422).
- Explicit current vs historical state on every segment read response.

## CRITICAL FastAPI lesson: NaN-safe validation must live in the ROUTER, not FastAPI body params

FastAPI's default `RequestValidationError` handler echoes the RAW parsed body, and Starlette's
`JSONResponse` uses `allow_nan=False` — so a request carrying a JSON `NaN`/`Infinity` that fails
validation produces a 422 body containing the raw NaN, which then CRASHES serialization into a 500.

Fix pattern (scope-compliant when app.py may only be touched for router registration):
- Routes declare an untyped `dict` body, then call a router-private `_validate_body(body, Model)`
  → strict Pydantic model (or a stable `HTTPException(422)`), so validation and serialization happen
  under your control and NaN never round-trips through the default handler.
- Trade-off (document it in REPORT §Deviations): OpenAPI request-body schemas for those endpoints
  are not embedded (FastAPI sees an arbitrary dict); every other surface (paths, methods, responses,
  no DELETE) stays intact. "OpenAPI generation" is still satisfied by a smoke test that lists paths.

## Router / transaction / error contract

- Single prefix `/api/v2/structural-evidence`, disjoint from all legacy + `/api/v2/object-intelligence`.
- Segments: create current / get current / get historical (explicit) / list current / list historical
  versions (explicit) / update current (CAS) / manual correction+supersede (CAS) / lineage oldest→newest.
  Motion + occlusion + contact: create / get / list / update (CAS). 24 paths total, methods GET/PATCH/POST.
- SessionDep/repository pattern; one request = one transaction; commit after repository success;
  rollback before every mapped error; DTO boundary (never return ORM objects).
- Stable mapping: malformed/enum/range → 422; not found / cross-workspace → 404 (no existence leak);
  stale revision / historical mutation / generation / idempotency-payload conflict → 409;
  unexpected DB error → rollback + fail-closed 500 (never raw SQL).
- Manual-correction response shows predecessor historical, successor current, shared logical
  lineage, revisions, provenance — no silent mutation.
- Verification is `app.openapi()` inspection: count structural-evidence paths, assert `DELETE` absent,
  assert object-intelligence paths still present.

## Test matrix (30 items — real SQLite/FK/CHECK/index/transaction, NO mocks)

create/get/list current; history read-only; lineage oldest→newest; arbitrary-gen/job/role rejection;
CAS 409; motion CRUD+CAS+frame/time containment; occlusion CRUD+CAS (both endpoints); contact CRUD+CAS
+ self-edge + cross-video; idempotency replay/identity-conflict/payload-conflict; end-before-start
422; cross-workspace 404; 422 unknown fields; NaN/Infinity reject; no DELETE; rollback on induced
conflict; concurrent CAS single winner; full phone-interaction graph API round-trip (write→read-back,
canonical JSON, FK/integrity checks); OpenAPI generation; object-intelligence unchanged.

## Protected-hash clarification (the channels.json mix-up)

- THE protected user file is MAIN root `C:\Users\Admin\MotionForge2D\channels.json` = DD7AAE26…555.
- The `e3ef6fbd…` value that a writer reported is a DIFFERENT file — test fixture
  `tests/fixtures/legacy_import/importable/channels.json` (worktree), equal to its committed blob.
- An earlier C1 REPORT attributed `dd7aae…` to the fixture — a paper artifact. When auditing
  protected hashes, verify the EXACT path (MAIN root vs tests/fixtures) before flagging a mismatch.
