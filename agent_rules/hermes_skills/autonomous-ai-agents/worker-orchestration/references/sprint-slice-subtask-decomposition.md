# Sprint-Slice Subtask Decomposition — multi-session task slicing

Pattern source: S11-T01 "Original Audio Remux" correction (2026-08-21), full cycle
A→D MANAGER_VERIFIED 2026-08-22. The parent prompt mandated exactly ONE owning
production writer session for the whole task; mid-run the user corrected: decompose
into four formal subtask IDs, each with its own owning session, dispatched in DAG
waves. Reuse this shape whenever a task is too large for one session.

## When to decompose

- Task spans ≥3 distinct concerns (e.g. policy/contract → engine → wiring → integration).
- One allowlist would mix unrelated production files, weakening scope discipline.
- Reviewers need read-only lanes whose view of "done" is per-concern, not monolithic.
- Parent authority grants only part of a roadmap (sibling tasks blocked on an epic).

## Canonical structure (S11-T01 example)

| Subtask | Concern | Exclusive writes (disjoint across siblings) |
|---|---|---|
| T01A | Import policy + contract freeze | import service (narrow behavior), contract docs, policy tests |
| T01B | Pure/bounded engine | NEW engine module + its unit tests only |
| T01C | Durable job wiring | job_service registration (additive only) + thin adapter module + job tests |
| T01D | Real integration/acceptance | integration + acceptance test files ONLY (production read-only) |

Each subtask packet defines: outcome, exclusive write allowlist, forbidden files
(INCLUDING sibling test files), required tests, end state (`SUBMITTED`),
correction protocol. Read-only dependencies are listed explicitly so a writer
reads-but-never-writes shared modules.

## Session ownership rules (hard)

- NEW task ⇒ NEW session. CORRECTION ⇒ RESUME the same owning session until
  MANAGER_VERIFIED. Never open a second session while the owner is alive.
- Recovery session ONLY when the owner is confirmed dead/unresumable; before
  recovery record: inactive proof, reason, last confirmed file/hash/test, full
  correction history. Recovery keeps the SAME Task ID and pinned model.
- Never: two sessions owning one Task ID; one session owning two Task IDs;
  a reviewer session used as production writer; an old BA session used as writer;
  correction expressed as a new Task ID (`T01A-C1` is forbidden).

## DAG + wave dispatch

```
A ──────────────┐
                ├─→ D      Waves: W1 = A ∥ B (parallel, disjoint write-sets)
B ─→ C ─────────┘          W2 = C after B MANAGER_VERIFIED (may overlap A)
                           W3 = D only after A+B+C all MANAGER_VERIFIED
```

- Capacity-slot reuse: when B finishes, launch C in B's slot.
- Parallel lanes only when write-sets are PROVABLY disjoint; verify ownership by
  mtime window after exit (see pitfall 20).
- If an upstream defect surfaces downstream (e.g. T01D finds an engine bug), the
  DOWNSTREAM session stops; manager resumes the OWNING upstream session, then
  resumes the downstream session to rerun acceptance. Downstream never patches
  upstream code.

## Session registry (mandatory, maintained by manager)

`| Task ID | Role | Session ID | Model | State | Exclusive files | Dependency | Last heartbeat |`

Write the session ID immediately at creation. States:
`PLANNED → READY → RUNNING → SUBMITTED → (CORRECTION_REQUIRED ↔ RUNNING) →
MANAGER_VERIFIED`, plus terminal blockers `BLOCKED_SCOPE` / `BLOCKED_MODEL_ROUTE`.

## Model-pinned lanes

When the lane exists to quality-check a specific model: EVERY new session
(writers, reviewers, recovery) uses exactly the pinned model + reasoning level +
fallback disabled. If the provider rejects the route ⇒ state `BLOCKED_MODEL_ROUTE`,
report to user, NEVER substitute another model. Pre-existing sessions/lanes keep
their own models — never retarget them. Record per session: exact model ID,
actual provider, display alias, reasoning level, fallback state, start local+UTC
time, read/write allowlist.

## Read-only reviewer lanes

Separate Task IDs (e.g. RO1 runtime-safety, RO2 test-strength/report-accuracy),
one session each, read-only, findings written ONLY to
`output/<lane>-readonly-review/<run-id>/`; findings get routed back into the
owning task's session context. Reviewer follow-ups continue the SAME reviewer
session. Safe to run parallel to writers when the provider endpoint is healthy
(pitfall 16 caveat); snapshot reviews taken before code lands need explicit
re-review after landing.

## Global-gate mutex

Focused subtask work may run parallel to other lanes' writers, but global quality
baselines are exclusive: pause all lane writers at coherent checkpoints, verify
no writer is mid-write, verify the OTHER lane (e.g. S07) is not running its own
global gate, then run exactly one baseline. If you cannot verify the other lane's
gate state, do NOT run your global gate — park at
`SUBMITTED_PENDING_GLOBAL_GATE` / `MANAGER_VERIFIED_PENDING_CODEX_REVIEW` and
stop the writers instead of letting them idle.

## Close-out vocabulary (do not overclaim)

Per-subtask: `MANAGER_VERIFIED`. Parent task: `<PARENT>=MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.
Sprint stays `IN_PROGRESS / <parent>_PENDING_CODEX_REVIEW / <siblings>_BLOCKED_ON_<epic>`.
Never self-record APPROVED / CLOSED / CODEX_APPROVED / SPRINT_SUBMITTED — the
external reviewer (Codex) owns those transitions.

## Full-cycle results (verified 2026-08-22, S11-T01A→D complete)

- Corrections were all narrow and first-try when the resume `-q` enumerated exact
  errors + gate commands (pitfall 32): T01A 2 corrections (F401; mypy annotation),
  T01B 1 (UP035/F841/2×unused-ignore), T01C 1 (10 lint findings), T01D 0.
- Final acceptance: ONE frozen command running all five S11 test files
  (`--ignore=tests/test_integration.py`, Windows-native basetemp,
  `-p no:cacheprovider`, `env -u MOTIONFORGE_DATABASE_URL`) → 52 passed, 0
  failed, no ffmpeg/ffprobe leaks (psutil scan), stable across ≥3 runs.
- Manager independent re-verification per subtask: rerun the subtask's own tests
  + regressions of every touched neighborhood (worker, job persistence, import)
  on separate basetemps; grep REPORT=SUBMITTED; hash-compare engine/protected
  files against dispatch-time snapshots.
- Close-out artifact: `docs/pm/sprints/<SPRINT>-CODEX_HANDOFF.md` (see pitfall 34)
  + registry heartbeat line marking every lane MANAGER_VERIFIED; workers stopped;
  terminal state `MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.
- Parallel-lane attribution: a sibling sprint sharing the worktree CAN move
  tracked-modified counts mid-run (S07 moved project_cast.py 4380846c→66dbb946
  while S11 ran). Before blaming your writer: grep writer logs for writes to the
  file, check mtimes against the writer's window, compare against the writer's
  own logged baseline (pitfall 29).
