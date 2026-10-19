# S08-T02-C1 / T03-C1 / T05-C1 correction recipes (verified 2026-08-17)

Resolves the SKILL.md pointer `references/s08-t02c1-t03c1-correction-recipes.md`.
The Codex findings B/C/D were each cleared in ONE correction round by pairing an
exact prompt skeleton (findings verbatim) with the proven validation battery.
Use as the copy-template for later finding-B/C/D-class corrections.

## Finding B — REAL PRODUCTION EXTRACTION + STABLE MEDIA IDENTITY (T02-C1)

Prompt carried 10 items verbatim (all fixed in one round):
1. Replace the stub with a functional SAM2.1 local provider: decode real
   managed source/proxy frames, generate real masks/crops/bboxes/confidence/
   provenance, inference ONLY inside the durable worker, no download/network
   fallback, fail closed when capability genuinely absent. Checkpoint is
   read-only: `C:/Users/Admin/MotionForge2D/models_checkpoints/sam2.1_hiera_large.pt`.
2. Pluggable interface for later model upgrades; no version hardwire without a
   benchmark.
3. Deterministic provider QA-only; production callers cannot select it via
   request JSON (reject with 422); choice = server policy.
4. `available()` verifies a real locator/backend capability, not an env string.
5. Stable candidate/role id in extraction output — display name never identity.
6. Durable ObjectRole↔Artifact association keyed by stable IDs + purpose +
   generation + source job; forward migration + round-trip/upgrade tests;
   preserve existing artifact rows.
7. Contained image content endpoint: ManagedRoot-only resolution, allowlisted
   MIME, size/hash check, ETag=SHA-256, `X-Content-Type-Options: nosniff`,
   404/409 for missing/stale/non-ready.
8. Backend-authoritative current-extraction lookup + generation param.
9. Source-generation filtering (historical rows auditable, not current).
10. Real read-only SAM2.1 GPU smoke on repo fixture + fresh temp root; honest
    perf/memory.

Required tests (from the finding): missing/corrupt checkpoint, unsupported
locator, production request attempting deterministic, real artifact bytes,
containment, stable mapping after rename/duplicate names, restart, source
replacement.

## Finding C — CURRENT-GENERATION GROUPING (T03-C1)

1. Group ONLY current video/source generation; historical rows never mix in.
2. Stable role IDs in suggestions AND operations; display name never identity.
3. Backend-exposed policy metadata (algorithm version, confidence semantics,
   review threshold, calibration version) via API.
4. Everything advisory — never auto-confirm/auto-merge; generate creates
   pending rows only.
5. Adversarial tests: duplicate names, renamed roles, cross-generation,
   cross-workspace/project/video/source-generation ownership fail-closed.
6. Merge/split/confirm = CAS/revision + idempotency + audit; stale→409; replay
   →same op row; split requires merge lineage (409 without); new suggested role.
7. GET/list/detail read-only (zero mutations on repeat/concurrent) + expose
   review reasons.
8. Evidence never silently rewritten/deleted (content byte-identical after
   move; superseded roles keep supersedes_role_id; no DELETE).
9. Duplicate/concurrent/restart never create duplicate active roles.
10. Preserve ALL prior guarantees (R01 queued-cancel/root/QA fail-closed, T02-C1
    provider/identity/association/content/generation); no extractor redesign,
    no frontend, no T05 preempt.

## Finding D — CORRECTED MEDIA BECOMES CANONICAL (T05-C1)

1. RECOMPUTE publishes replacement media links for affected stable role IDs.
2. Gallery/API resolve newest valid media for affected roles.
3. Unaffected links + bytes/hashes identical.
4. Superseded artifacts auditable but not current.
5. Rename-only correction must not lose media.
6. Geometry/reassign shows regenerated media after completion AND restart.
7. Cover queued cancel (not just running-cancel).
8. Preserve retry/successor, fencing, idempotency, concurrency, scope-preview,
   no-orphan.
Note line: T02-C1 already provides associations + content endpoint +
/extraction/current + generation filter — correction REPLACES media links (new
association rows; old superseded but auditable) and gallery resolves newest
valid.

## Validation battery (proven pass shape, per task)

All runs `-p no:cacheprovider`, shallow basetemps under
`C:/Users/Admin/AppData/Local/Temp/<task>-c1-*` (MAX_PATH lesson). Migration
round-trip in a subshell so `MOTIONFORGE_DATABASE_URL` dies with it.

- Focused new/corrected suite(s)
- Cross-task combined suites (T01→T03 domain files, or T01–T05 for later tasks)
- R01 lifecycle suites (queued-cancel, root-resolution) — every subsequent
  task runs on the post-R01 engine, so these must be in every battery
- S05 41-suite (shallow), S02 durable regressions
- Migration round-trip: upgrade head → downgrade <prev> → upgrade head;
  verify `alembic current` prints the NEW head
- ruff changed files; mypy app; git diff --check; final git status --short
- Protected-data comparison: MAIN channels.json SHA
  `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`;
  MAIN `data/motionforge.db` 311296 bytes; SAM2.1 checkpoint untouched

## Measured numbers (manager independent re-runs, 2026-08-17)

| Task | Focused | Cross-task | R01 | S05 | S02 | Migration head |
|---|---|---|---|---|---|---|
| T02-C1 | 46/46 (43.2s) [4 files] | T01+T03 70/70 (29.75s) | — | 41/41 (96s) | 87/87 (40s) | `f5a6b7c8d9e0` (role-artifact assoc) |
| T03-C1 | 36/36 (13.65s) | T01+T02 81/81 (54.4s) | 18/18 (5.85s) | 41/41 (92.4s) | 87/87 (38.7s) | head unchanged (policy only) |
| T05-C1 | 45/45 (28.05s) | T01–T04 116/116 (58.0s) | 18/18 (6.2s) | 41/41 (93.7s) | 87/87 (41.6s) | `f6a7b8c9d0e1` (media supersession) |

T02-C1 also ran SAM2.1 GPU smoke 1/1 (8.75s, read-only checkpoint, isolated
root). T03-C1 scope was ONLY `app/persistence/object_grouping.py` +
`tests/test_object_grouping.py` (mtime-window find). T05-C1 was backend+frontend
(new migration + gallery media + 2 REQUIRED T04-spec test updates, disclosed
publicly).

Verification scripts live OUTSIDE both repos at
`C:/Users/Admin/AppData/Local/Temp/verify-s08-<task>-c1.sh` (numbered sections,
background + notify_on_complete). `process(action='wait')` timeouts are clamped
to 180s — prefer notify_on_complete, then read each section's counts from the
full log; exit 0 alone proves nothing.
