# S08-A02 truthfulness + scalability correction rounds (2026-08-20/21)

Codex reviewed the structural-evidence / object-extraction core across
C3→C6 (structural persistence) and T02-C1/C2 (extraction evidence wiring) and
kept returning CHANGES_REQUESTED on the same families. This file records the
exact repros that proved each defect and the fix that satisfied the review.

## Rounds at a glance
| Round | Scope | Blocker class | Fix |
|---|---|---|---|
| C3/C4 | historical pagination, target-role ownership | unbounded IN-list + OR-chain; missing project_id guard on supersede | COUNT after filter; batch current-generation; project ownership check |
| C5 | batch-generation scalability | per-video `literal_column` UNION ALL → SQLite "too many terms in compound SELECT" at 501 videos; 4 unbounded `in_(...)` | authoritative `batch_current_generation` in `ObjectIntelligenceRepository` (`_SQLITE_MAX_PARAMS=900`, `_chunked`, `_resolve_generation_from_jobs`), fail-closed ownership (`RoleNotFoundError`, no `except Exception→None`) |
| C6 | bind-parameter budget | `or_(IN(chunk1),IN(chunk2),...)` still makes final COUNT/page bind count = total stale videos | SQLite JSON1: `video_item_id IN (SELECT value FROM json_each(:stale_json))` — ONE JSON text param, ≤6 total binds regardless of stale count; capability probe + fail-clear |
| T02-C1 | truthful evidence | `hash(seg_id)` non-deterministic; unconditional synthetic motion/occlusion/contact; `deterministic-layout` in production; fabricated bbox; confidence clamp `get("confidence",0.7)`; operator-precedence `and ... or` swallow | sha256 stable digest; QA gate `_is_qa_synthetic`; provenance `{provider,qa_mode,synthetic,test_adapter}`; bbox omit vs fabricate; confidence fail-closed; typed-only catch with parens |
| T02-C2 | conflict safety + real determinism | service still swallowed typed "already bound"; cross-process test recomputed SHA in-process | delete try/except around create_*; use `(record, created)`; wrong-type "already bound" propagates; real subprocess test with actual publication path |

## Repro: 5001-video SQL bind instrumentation
```bash
# capture EVERY statement + its bound params via SQLAlchemy before_cursor_execute
MOTIONFORGE_DATABASE_URL= python -m pytest tests/test_s08_a02_c3_corrections.py \
  -k test_c6_5001_stale_videos_fixed_params -v -p no:cacheprovider \
  --basetemp=C:/Users/Admin/AppData/Local/Temp/mgr5001_$(date +%s)
```
Expected (verified): 23 statements total — distinct(1) + video(6, chunked
900) + project(1) + artifact(6) + job(6, 900/513) + probe(1) + COUNT
`n=3 <=6` + page SELECT `n=5 <=6`; `OVER_BUDGET 0`; no OR-chain; no UNION.

## Repro: cross-process determinism (two PYTHONHASHSEED)
```bash
# Test spawns two real subprocesses with PYTHONHASHSEED=1 vs 999; each runs the
# ACTUAL publication path (real repo, real table, fresh SQLite, QA provider +
# qa_mode), then queries evidence from the DB and compares normalized output.
MOTIONFORGE_DATABASE_URL= python -m pytest \
  tests/test_object_extraction.py::test_c1_cross_process_deterministic_qa_byte_identical \
  -p no:cacheprovider --basetemp=C:/Users/Admin/AppData/Local/Temp/mgrcross_$(date +%s)
```
Compare: prompt/seg JSON · mask SHA256 · camera/object transforms · motion
refs · occlusion/contact kind+ranges · synthetic provenance · ordering.
Must FAIL if implementation reverts to `hash(seg_id)`.
Note: normalize only env/job-specific identifiers the contract allows; do NOT
copy the implementation formula into the test.

## Repro: conflicting-idempotency (real, no monkeypatch)
Publish QA evidence once, replay byte-identical → counts unchanged. Then reuse
the SAME idempotency key but mutate one field: motion transform, motion ref,
occlusion endpoint/range, contact kind/range. EACH must raise the correct
typed conflict (MotionConflictError / OcclusionConflictError /
ContactConflictError), roll back the publication, and leave the existing row
unchanged. Wrong-type exception whose text contains "already bound" must
propagate (previously swallowed by the precedence bug).

## Repro: flaky statement-counter test (C4)
```bash
# 30 consecutive runs of the no-N+1 test; ALL must pass.
for i in $(seq 1 30); do
  MOTIONFORGE_DATABASE_URL= python -m pytest \
    tests/test_s08_a02_c3_corrections.py::test_c4_multi_video_no_nplus1 \
    -p no:cacheprovider -q --basetemp=C:/Users/Admin/AppData/Local/Temp/fx_$(date +%s)
done
```
Root cause of historical flakiness: brittle counter counted BEGIN/ROLLBACK
too; `contextlib.suppress(Exception)` around setup could leave a pending
rollback. Fixed: count only statements whose SQL starts with `SELECT`
(`statement.lstrip().upper().startswith("SELECT")`), deterministic setup
(position=max+1, hashlib-derived values, timestamped jobs), and remove
`suppress(Exception)` so setup failure fails the test immediately.

## Notes
- `pytest --count=N` requires pytest-repeat (not installed here); use a shell
  loop for N× repetition.
- SQLite limits: 500 terms in a compound SELECT; 999 bind params. JSON1
  `json_each()` is the idiomatic fixed-bind escape hatch; probe capability and
  fail clear (never raw interpolation).
