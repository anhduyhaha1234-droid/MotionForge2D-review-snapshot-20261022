# S08-A02 C4/C5 + T02-C1 correction-cycle lessons (verified 2026-08-20)

Proven patterns from the Codex CHANGES_REQUESTED rounds for C4 (historical-query scalability)
and T02 (extraction-evidence truthfulness/determinism), including the parallel two-lane dispatch.
Complements `references/s08-a02-t01-c3-correction-cycle.md`.

## C4 flaky test — ROOT CAUSE (do not just re-run "it flaked")

`test_c4_multi_video_no_nplus1` was order/flaky (fail ~1/12 in full combined, pass alone 10/10).

ROOT CAUSE: the test wrapped `_advance_generation(session, seed, "4")` in
`contextlib.suppress(Exception)`. If that call throws (e.g. UNIQUE role collision), the SQLAlchemy
session enters a **pending-rollback** state; the next statements emit `ROLLBACK`/`BEGIN` which the
`before_cursor_execute` statement counter counts, so the N+1 guard `counter <= 10` trips for the
WRONG reason.

FIX (both code style + instrument):
- Remove `contextlib.suppress(Exception)` around setup; deterministic setup; if setup errors the
  test FAILS immediately.
- Instrumentation counts ONLY relevant `SELECT` statements
  (`statement.lstrip().upper().startswith("SELECT")`), never BEGIN/ROLLBACK/COMMIT.
- Re-run the formerly-flaky test at least 20× in a loop (`pytest-repeat`/`--count` NOT installed —
  use a shell `for i in $(seq 1 20)`).

Manager rule: a "flaky" statement-count test is a boundary/setup bug, not luck. Find the counted
non-SELECT statement before re-running.

## SQLite "too many terms in compound SELECT" — 501-term UNION ALL

`list_historical_segments(video_item_id=None)` originally built per-stale-video
`literal_column(f"'{vid}'")` UNION ALL terms → at 501 videos SQLite raises
`OperationalError: too many terms in compound SELECT`.

RULE (any scalable query):
- NEVER interpolate IDs into SQL strings (`literal_column(f"'{v}'")` is a hard blocker).
- ONE statement must not grow unbounded in parameters/compound terms. SQLite caps params ~999;
  keep chunk size comfortably below (project uses 900).
- Batch/chunk with SQLAlchemy bindparams (`in_(chunk)`), fixed chunk size, parameterized.
- Create an AUTHORITATIVE batch API in the repository that owns the semantics (here:
  `ObjectIntelligenceRepository.batch_current_generation`) — do NOT replicate
  `_current_generation_for_source` inside a second file. One semantic source; the Nth-video
  loop in the caller just consumes the map.
- Unknown/corrupt ownership FAILS CLOSED (raise), never `except Exception -> cur=None`.
- `total` = COUNT after filter; offset/limit after filter; deterministic ordering; do not load all
  history rows into RAM.
- Verify SQL is parameterized by test (grep `literal_column(` must be 0; assert emitted SQL has no
  raw UUID string interpolation).

## Determinism across Python processes

- Python `hash(str)` is salted by PYTHONHASHSEED → NOT stable across processes. Any derived
  id/transform/order key that must be byte-identical across runs MUST use a stable digest:
  `hashlib.sha256(seg_id.encode()).digest()[:4]` or `uuid.uuid5(...)`.
- Test determinism with TWO FRESH SUBPROCESSES, e.g. `PYTHONHASHSEED=1` and `PYTHONHASHSEED=999`,
  each running full QA extraction; compare normalized prompt/seg JSON, mask sha256, transforms,
  ids byte-identical. "Replay same job in same process" is NOT an independent determinism proof.

## Truthful evidence gating (T02-C1 Codex blocker set)

- Synthetic motion/occlusion/contact must be gated: `qa_mode and provider in
  (deterministic, deterministic-identity)` ONLY. Production writes graph edges ONLY when the
  provider actually returns that evidence; never infer an edge from "two segments exist"; never
  fabricate a sparse-flow reference.
- QA synthetic rows carry provenance `{provider:"deterministic", qa_mode:true, synthetic:true,
  test_adapter:true}`.
- Production segments use the ACTUAL provider algorithm — never a `deterministic-layout` fallback
  (missing algorithm → fail closed).
- Missing/malformed bbox → omit prompt evidence or fail closed; NEVER fabricate a default
  (e.g. 10/10/50/50).
- Confidence: missing / NaN / +Inf / -Inf / out-of-range → fail closed; NEVER clamp to a default
  like 0.7.
- "Production no-false-evidence" test must actually drive a NON-QA production path, not submit
  provider=deterministic + QA mode.

## Operator-precedence exception-swallow bug (grep this!)

AUTHORED pattern was:
```python
if isinstance(exc, MotionConflictError) and "already bound" in str(exc) or "already bound" in str(exc):
    pass  # idempotent replay
else:
    raise
```
Because `and` binds tighter than `or`, this is `(isinstance(...) and "already bound" in ...) or
("already bound" in ...)` → ANY exception whose message contains "already bound" is swallowed,
even a WRONG exception type. Fix with explicit parentheses: `isinstance(exc, MotionConflictError)
and ("already bound" in str(exc))`. Test must prove a wrong-type exception bearing the text
(e.g. `ValueError("already bound")`) PROPAGATES.

## Parallel two-lane dispatch (allowlists disjoint)

Codex launched C5 (scalability) and T02-C1 (truthfulness) as two concurrent writers:
- Two `hermes chat` background processes, each with its own Muse session, `notify_on_complete`,
  verbose log tee'd to its own file. Allowlists must not overlap ANY file.
- Manager alternates bounded `process wait`/`poll` between the two; do not attach to just one.
- AFTER both exit, run the integration gate: file-ownership check by mtime window per lane
  (`ls --time-style=full-iso`), grep the FAIL-condition list across code, re-run each lane's suites
  + combined ×2 + flaky ×20 + cross-process PYTHONHASHSEED repro + 501/1001-video repro; ruff/mypy/
  alembic/OpenAPI/git diff --check/MAIN-protected.

## Writer `git checkout HEAD -- <file>` on an UNTRACKED file is a no-op (verify before panicking)

A Lane-B writer ran `git checkout HEAD -- tests/test_object_extraction.py`. Because the whole A02
worktree is intentionally uncommitted (`??` in git status), the path is not known to HEAD →
`error: pathspec ... did not match`, NOTHING destroyed. RULE: when a writer logs a forbidden
`git checkout`/`reset` command, (1) confirm whether the target is tracked at HEAD
(`git ls-files --error-unmatch <file>`), (2) confirm the file still has its full content + expected
test count + expected hash, (3) treat as an incident-in-scope note (writer went out of allowed
commands) but do NOT kill the writer on the basis of a no-op. Also record the writer's
post-hoc state check (it runs `wc -l`/`head` again — that is benign verification, not damage).

## Evidence hygiene for correction cycles

- NEW evidence dir per lane (`output/s08-a02-t01-c5/<ts>/`, `output/s08-a02-t02-c1/<ts>/`), never
  reuse prior logs. Writer evidence: per-suite logs + combined ×2 + flaky ×20 + cross-seed +
  ruff/mypy/alembic/openapi. Manager integration gate under `output/integration-gate/<ts>/`.
- Post-correction hashes for every allowlisted file; compare pre/post.
- Manager never reads test counts as proof — reads the actual code paths (grep FAIL-list:
  `hash(` digit, `literal_column`, `union_all`, unbounded `.in_(full_list)`, production synthetic
  branches, bbox fabrication, confidence clamp/default, `except Exception` swallow, same-process
  "independent" test).
