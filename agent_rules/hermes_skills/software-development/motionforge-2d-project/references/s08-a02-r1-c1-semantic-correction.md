# S08-A02-T01-R1-C1 — semantic correction contract + timezone bookkeeping

Use when resuming/continuing the S08-A02 structural-evidence correction cycle after Codex
came back CHANGES_REQUESTED on R1. Captures C1-F1..F7 (normative) plus a durable
timestamp/bookkeeping pitfall that bit the R1 evidence chain.

## Timestamp / UTC bookkeeping pitfall (user-corrected 2026-08-20)

- Machine timezone is Asia/Bangkok (+07:00). Local times 00:00–07:00 map to the **PREVIOUS UTC
  day** (17:00–24:00Z). E.g. `2026-08-20T02:20+07:00` = `2026-08-19T19:20Z`, NOT `2026-08-20T19:20Z`.
- R1 post-verification artifacts (manager addendum, MANAGER_STATE, preflight evidence) wrote
  `2026-08-20T1x:xxZ` for `02:xx+07:00` local — a full 24h off. The user's recovery brief
  flagged this as an explicit bookkeeping correction to append (not silently edit).
- RULE: whenever you record both local and UTC in the same artifact, DERIVE the UTC with
  `TZ=UTC date '+%Y-%m-%dT%H:%M:%SZ'` at write time (or today's date − 1 when local hour < 7 and
  you are manually offsetting). Never hand-roll the offset. A wrong same-day UTC is a silent
  ~24h lie in every downstream report/handoff.
- Correction policy: append a timestamp-correction section to the prior REPORT.md naming the
  wrong UTC values and their correct local↔UTC pairs; never rewrite history.

## C1 scope and verdict

- R1 (DeepSeek Core Recovery) reached `MANAGER_VERIFIED_PENDING_CODEX_REVIEW` with production
  model/migration/repo hashes `4B7D30B6…` / `85EEE1D5…` / `1A5C3D39…` and 345-passed full
  regression. Codex then returned **CHANGES_REQUESTED** — F1..F11 NOT fully closed.
- Mandated active task: `S08-A02-T01-R1-C1` (Generation, Idempotency and Temporal Integrity
  Correction), packet under `docs/pm/sessions/S08-A02-T01-R1-C1-semantic-safety/`. R2 (schema/API)
  must NOT start until C1 is writer-submitted AND manager-verified.
- C1 allowlist: models.py A02 block, `app/persistence/structural_evidence.py`,
  migration `a0b1c2d3e4f5` (down `f7a8b9c0d1e2`; rewrite allowed, temp DBs only), the 3 existing A02
  test files (extend), NEW `tests/test_s08_a02_r1_c1_semantic_safety.py`, NEW packet dir +
  `output/s08-a02-t01-r1-c1/` evidence. Forbidden: schemas, api, app.py, deps.py, frontend,
  extraction/grouping/correction production code, S07/S09, the 8 pre-existing head-bump test
  files, MAIN. Writer must STOP BLOCKED (one question) on any out-of-allowlist need — do NOT
  re-run the R1 "best judgement after clarify timeout" mistake; overnight brief §16 forbids it.

## C1-F1 — generation semantics (two workflows, never arbitrary)

- Old bug: `supersede_segment()` REQUIRED `source_generation != prior`, then minted a successor at
  an arbitrary generation — but `ObjectIntelligenceRepository.current_generation()` still returns
  the OLD generation, so the successor is stale-on-arrival.
- Workflow A (manual/user correction in the CURRENT generation): predecessor current+active;
  successor keeps the SAME `source_generation`; same `logical_id`; new record id; predecessor →
  historical/read-only, successor → current/mutable; CAS predecessor; atomic; provenance/
  `confidence_source` must say `user`/`manual` (never silently inherit `model`).
- Workflow B (re-analysis TRANSITION): target generation MUST equal
  `ObjectIntelligenceRepository.current_generation()`; `source_job_id` REQUIRED; job completed
  DISCOVER_OBJECTS with matching workspace/video/source-SHA/input-generation; prior may be older
  generation but must be the active lineage version.
- Public create must FAIL CLOSED on: generation ≠ backend authority, model/detector evidence
  lacking a producing job, job generation mismatch, role-generation mismatch, source-SHA mismatch.
- Tests: manual same-gen ok; successor updatable; predecessor read-only; future gen rejected;
  stale gen rejected; correct re-analysis ok; wrong/missing job rejected; role-gen mismatch
  rejected; zero mutation on failure.

## C1-F2 — logical identity & branch safety

- `logical_id` was caller-arbitrary with only a plain index. Change to: repo mints root
  `logical_id`; only the controlled successor/re-analysis path reuses it; never reusable across
  workspace/project/video/role; length/format validated; no branches (1 predecessor ≤ 1 successor).
- Recommended: `lineage_version`/`version_number` (start 1, successor = prior+1), with
  `UNIQUE(workspace_id, logical_id, lineage_version)`; repo checks no gap/branch; current version
  explicitly determinable. Concurrent supersede = single winner, loser rolls back. Cycle/dangling/
  duplicate-predecessor fail closed.

## C1-F3 — complete idempotency

- Motion equivalence must include: occurrence_segment_id, transform_type, start/end_frame,
  start/end_time_ms, transform_json, point_track_flow_ref, algorithm/version, confidence/source,
  reasons/provenance.
- Occlusion: project_id, video_item_id, occluder/occludee_segment_id, all temporal, algorithm/
  version, confidence, reasons/provenance. Contact: same + source/target_segment_id + contact_kind.
- Same workspace/key + identical canonical identity → replay existing; any differing field →
  stable conflict, zero mutation. Empty key rejected/normalized per explicit contract; over-length
  key rejected before flush.

## C1-F4 — frame AND time containment

- `_assert_range_within` checked frames only. Must ALSO enforce `segment.start_time_ms <= child.*`
  and `child.* <= segment.end_time_ms` for motion/occlusion/contact create AND update. Contact/
  occlusion range must fit BOTH endpoint segments. Reject wins → zero mutation.

## C1-F5 — ownership/artifact

- Mask artifact: same workspace + `kind=image` + `state=ready` (plus ownership/purpose if the
  contract supports it). Reject video/audio/document, staging/trash/missing/failed.
- Model/detector evidence REQUIRES completed DISCOVER_OBJECTS job matching workspace/video/
  generation/SHA. Manual evidence: explicit provenance, `user`/`manual` confidence_source.
- Segment kind must stay compatible with ObjectRole.kind; updates must not diverge from the role
  taxonomy; reclassification uses the explicit role/correction contract, never standalone kind edits.

## C1-F6 — domain validation (before flush)

- lengths (algorithm, algorithm_version, idempotency key); `reasons` = list[str], `provenance` =
  dict; `prompt.points`/`prompt.boxes` = list; point exact shape + non-empty label; box w/h valid;
  NaN/Infinity rejected; malformed durable JSON fail-closed (never silently becomes default).
- Do NOT catch every IntegrityError and mislabel it duplicate — translate only the true
  unique/idempotency constraint; FK/CHECK/ownership errors get stable domain errors.

## C1-F7 — durable delete policy

- `object_role → occurrence_segment` CASCADE and `occurrence_segment → segment_motion` CASCADE
  silently erase history. Change to RESTRICT unless an equivalent history-preserving design is
  proven. Tests: referenced-role delete leaves segments; referenced-segment delete leaves motion;
  delete fails closed; rows byte-identical; `foreign_key_check` empty.

## C1 validation order (normative, 20 steps)

1 import smoke → 2 C1 semantic-safety suite → 3 A02 migration → 4 A02 domain → 5 phone scenario → 6
combined A02 focused → 7 A01-C1/object-intelligence regression → 8 full S08 regression → 9
persistence bootstrap/durable-job → 10 ruff → 11 mypy → 12 diff --check → 13 migration/ORM parity →
14 empty up/downgrade round-trip → 15 downgrade refusal atomic → 16 integrity_check ok →
17 foreign_key_check empty → 18 fresh quality-baseline 7/7 → 19 protected hashes → 20 no-listeners.
Never weaken/delete old tests; never adjust expected results to match wrong code. Manager re-runs
everything; ≤2 bounded correction cycles; final C1 = MANAGER_VERIFIED_FOR_OVERNIGHT_CONTINUATION_
PENDING_CODEX_REVIEW (or BLOCKED).
