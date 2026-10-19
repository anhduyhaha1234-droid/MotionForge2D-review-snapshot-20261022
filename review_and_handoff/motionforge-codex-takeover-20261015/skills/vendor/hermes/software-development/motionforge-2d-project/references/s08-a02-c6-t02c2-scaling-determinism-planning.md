# S08-A02 C6/T02-C2 + Post-A02 Planning — Query Scalability & Truthful-Determinism Lessons (verified 2026-08-20)

Lessons from the final S08-A02 correction cycle (C5→C6, T02-C1→T02-C2, and the read-only
post-A02 planning lane).  Extends `s08-a02-c4c5-t02-truthfulness-parallel-lanes.md` — read that
first for the C5/T02-C1 round.

## 1. SQLite bind-parameter / compound-SELECT limits → the C6 blocker

**Limits (real, verified):**
- SQLite default **max bind parameters = 999** per statement (`SQLITE_MAX_VARIABLE_NUMBER`).
- **Compound SELECT limit = 500 terms** (`SQLITE_LIMIT_COMPOUND_SELECT`) → the C4/C5
  `union_all`-of-literal-columns approach died at 501 videos with
  `OperationalError: too many terms in compound SELECT`.

**The getcha that survived C5:** chunking `stale_vids` into 900-size `IN(...)` clauses and then
OR-ing them (`or_(superseded, IN(chunk1), IN(chunk2), ...)`) means the **final COUNT and page
SELECT each carry a total number of bind params equal to the whole stale-video count** — still
unbounded, just hidden. Codex rejected C5 for this exact reason.

**C6 accepted solution — JSON1 `json_each()` fixed-bind:**
- Bind the stale ID list as **ONE JSON text parameter** (e.g. `json.dumps(vids)`), then
  `WHERE video_item_id IN (SELECT value FROM json_each(:stale_json))`.
- Bind count for that predicate is **fixed at 1** regardless of video count.
- JSON1 is built-in on modern SQLite; capability-check it (`PRAGMA compile_options` or a
  `SELECT json_each('[]')` probe) and **fail clearly if unavailable** — never fall back to raw
  string interpolation of IDs.
- Enforce a **declared fixed budget across ALL predicates** (workspace_id, source_generation,
  role_id, job_type, job.state, video ids...), not just the video-id predicate.
- **Instrumentation must measure real SQL**: hook `before_cursor_execute` and count
  `len(parameters)` per statement; assert **no statement exceeds budget**, that final COUNT/page
  bind counts are bounded, and that no `OR IN` chain / `UNION ALL` is emitted. Grep-on-source is
  NOT proof — the test must run the query and inspect actual emitted SQL + params.

Test bar: ≥5001 stale videos, capture EVERY statement + param collection, mixed
current/stale/superseded total+page correct, offset near end correct, role_id filter correct,
wrong-workspace fail closed.

## 2. Python `hash()` is NOT cross-process deterministic

`hash(str)` is randomized per-process by `PYTHONHASHSEED` — using it for derived ids/transforms
(was in object_extraction motion tx: `tx = float((hash(seg_id) % 20) - 10)`) breaks
"deterministic evidence" guarantees across runs.

**Fix:** derive from a stable digest, e.g.
`int.from_bytes(hashlib.sha256(seg_id.encode()).digest()[:4], "big")` (or `uuid5`).

**Real cross-process determinism test (T02-C2 mandate):**
- Must run the **ACTUAL application path** (handler/worker → real `StructuralEvidenceRepository`
  → real publication → fresh isolated SQLite), NOT recompute the formula in a subprocess harness.
- Two subprocesses with **different PYTHONHASHSEED** (e.g. `1` vs `999`).
- Query evidence from the DB after publication; compare prompt/segmentation JSON, mask SHA256,
  transforms, motion refs, occlusion/contact kind+ranges, synthetic provenance, ordering.
- Normalize only env/job-specific identifiers the contract permits to differ (e.g. record id,
  job id) — content must match.
- Must FAIL if implementation reverts to `hash(seg_id)`. Do not copy the implementation formula
  into the test (that silently re-encodes the same bug).

## 3. Idempotency conflict handling — never swallow typed conflicts

Repository gives `(record, created)`: equivalent replay → `created=False`; a DIFFERENT payload
with the same idempotency key → typed `MotionConflictError`/`OcclusionConflictError`/
`ContactConflictError` (message contains "already bound").

- **SWALLOWING the typed conflict is the bug** (C1 code did
  `try/except ... if isinstance(exc, X) and ("already bound" in str(exc)): pass`).
- Requirement: call the repository plainly, branch on `created`; let conflict exceptions
  propagate → rollback the whole publication; **never classify by substring-matching message**.
- C1 also had a real **operator-precedence bug**:
  `if isinstance(exc, X) and "already bound" in str(exc) or "already bound" in str(exc)`
  — `and` binds tighter than `or`, so ANY exception whose str contains "already bound" (wrong
  type included) gets swallowed. Always parenthesize: `isinstance(exc, X) and ("already bound" in str(exc))`.
- Test with REAL publishes, not monkeypatch-only: publish QA evidence → byte-identical replay
  (counts unchanged, completed) → then mutate transform / motion ref / occlusion endpoint/range /
  contact kind/range with the same idem key → each must raise, roll back, and NOT mutate the row.

## 4. Flaky statement-counter tests — count only SELECT, not BEGIN/ROLLBACK

C4's `test_c4_multi_video_no_nplus1` used `event.listen` + a counter over
`before_cursor_execute` and asserted `counter <= 10`. It was order/flaky (~1/12 in full combined,
passes alone) because:
- it wrapped setup `_advance_generation` in `contextlib.suppress(Exception)` — if it threw, the
  SQLAlchemy session was left in pending-rollback, so the next statements emitted extra
  ROLLBACK/BEGIN that the counter counted, tipping the bound.
- the counter counted EVERY statement, not just SELECTs.

**Fix pattern (accepted):** remove `suppress(Exception)` — setup must be deterministic and a setup
error must fail the test immediately; instrumentation counts only statements whose SQL is a
`SELECT`; run the test ≥20–30× in a row and require all pass.

## 5. QA-provider provenance must be truthful per provider

QA synthetic records must carry provenance with the ACTUAL provider name —
`deterministic` OR `deterministic-identity` — never hardcode `"deterministic"` when running the
identity adapter. Add tests for BOTH QA providers. Production non-QA keeps: zero synthetic
motion/contact/occlusion, no fake sparse-flow reference, actual provider algorithm, invalid
confidence fail-closed, no fabricated bbox.

## 6. Read-only planning lane → BLOCKED_NEXT_SPRINT_AUTHORITY

A planning lane (no code writes) producing `output/post-a02-planning/<run-id>/` artifacts
(`AUTHORITY.md`, `DEPENDENCY_DAG.md`, `PARALLELIZATION.md`, `NEXT_SPRINT_DRAFT.md`) should NOT
self-declare a next sprint. When the roadmap gates the next sprint on Codex approval + user
decisions, the correct terminal state is `BLOCKED_NEXT_SPRINT_AUTHORITY` with a numbered,
one-decision-per-item list (e.g. D1 ordering, D2 scope, D3 FK timing, D4 migration head policy,
D5 data source). Listing the exact missing decisions is the deliverable — not guessing the scope.

## 7. Parallel lanes — file-ownership discipline

When dispatching 2–3 writers on the same worktree concurrently:
- **Non-overlapping allowlists are mandatory** and must be verified by mtime after the run
  (e.g. Lane A touched `object_intelligence.py`/`structural_evidence.py`/`c3_corrections.py`;
  Lane B touched `object_extraction.py`/`test_object_extraction.py`; nothing else).
- A writer that runs `git checkout HEAD -- <file>` on an **untracked** A02 file is a no-op
  (`pathspec did not match`) — verify the file still exists and its line count is intact, don't
  assume data loss; but flag the forbidden command.
- `models.py` pre-existing dirty mtime (from an earlier phase) must not be mistaken for this
  cycle's work — check mtime window before blaming a lane.

## 8. Heartbeat while orchestrating writers (user requirement, 2026-08-20)

User flagged silence repeatedly while the manager drove 3 background lanes: "sao t ko thấy
heartbeat", "cứ phải đợi hỏi mới có báo cáo", "sao t thấy mày dừng". Durable rules:
- **End EVERY turn with a short heartbeat** — lane table (writer/session/state), % done, ETA.
  Do not batch all `process(wait)` into one silent mega-turn.
- An out-of-band user message **interrupts the in-flight turn and swallows the drafted heartbeat
  text** (`[This response was interrupted...]`). If the user asks mid-turn, answer immediately
  with a status table, then resume.
- `process wait` clamps to 180 s here — poll in ~180 s chunks and emit a heartbeat between polls.
- On "bao giờ xong" / "báo cáo tiến độ": reply with real numbers read from logs (exact passed
  counts, remaining suites, wall-clock ETA) — never "still working".
- Long suite runs will `exit 124` (timeout) inside a writer's combined fase — that is a
  duration artefact, not a failure; writers re-run in staged batches. Manager should expect it.

## 9. SKILL.md is at its size cap

`motionforge-2d-project/SKILL.md` exceeded 100 KB, so new lessons from this cycle go into
references/ (as here) — keep the body trimmed; favour references for session detail.
