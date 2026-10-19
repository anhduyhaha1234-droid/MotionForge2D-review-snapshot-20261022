# S11-C4 Production Registry + Fail-Closed Recovery (2026-09-05)

Class: production-bootstrap defects that green suites hide. Two P1s survived
C3's 143-test gate because every test imported/registered detectors before
exercising the product. Symptom signature: broad counts green, clean process
dead.

## The two defects

**P1-A — clean-process bootstrap registers zero detectors.**
`JobService` registered the `RUN_QC_CHECKS` handler but not its detector band.
Seven detector modules self-register only on import; three need explicit
`register()`. Normal startup imports neither. Orchestrator correctly rejects
unregistered detectors → full QC unusable after clean start.
Clean-subprocess probes that prove it (no test imports before bootstrap):
`from app.main import app; registry.names() -> []`, real `JobService` on a
fresh Alembic-head DB → `[]`, `run_full_check_set(full band)` →
`QC_ORCHESTRATOR_MISSING_ARGS`, all 10 binding names unregistered.

**P1-B — revision authority fails open through a guessed fallback.**
`qc_check_runs.py` wrapped the server resolver in try/except → `{}` and
defaulted each missing detector to `"1.0.0"`. Probe: only 2/10 detectors
registered + completion claiming ten `1.0.0` revisions → actual `completed`,
expected `failed` + readiness `not_run`.

## Recovery shape (one writer, T03G lineage, bounded write-set)

Allowed: `app/persistence/qc_check_runs.py`,
`app/workflow/qc_checks_handler.py`, `app/workflow/job_service.py`, the two
T03G test modules (+1 narrow clean-process test file iff subprocess isolation
cannot live in them), `docs/pm/sessions/S11-T03G/**`, new C4 evidence.
Forbidden: migrations, schemas, detector algorithms, T03F orchestrator,
other lanes' tests/code, frontend, broad refactor, deps/config, MAIN docs,
old-cycle evidence.

- **C4-A bootstrap:** one explicit server-owned composition path —
  `ensure_full_band_registered()` constructing the real `JobService` with its
  owned worker deterministically registers exactly the ten names from
  `scope_detectors(SCOPE_FULL)` (real entry points/revisions, incl. the three
  explicit-register ones) before any RUN_QC_CHECKS executes. Idempotent on
  repeat construction; conflicting name/entry/version fails closed. No
  duplicate detector, no dynamic client choice, no test-only bootstrap. Keep
  the orchestrator's unknown-detector rejection — never weaken it to pass.
- **C4-B authority:** delete every guessed fallback. Completion keyset+values
  must equal exact current server revisions for all ten names. Exception,
  unregistered member, incomplete/extra map, empty revision, conflicting
  registration → `failed` + `not_run` + truthful authority detail. Never
  `1.0.0` / `{}` / manifest values as substitutes. Valid full completion with
  all ten exact revisions stays `completed/ready`; no-source and real-source
  controls stay green. All C2/C3 invariants preserved.
- **C4-C hygiene:** normal repo-configured Ruff on CHANGED files only (not
  just `--select F`); fix own import-order + EOF-newline issues; no
  historical lint cleanup.

## Executable proofs (clean subprocess, no test/fixture imports first)

1. Importing normal app code alone recorded (diagnostic baseline).
2. Real `JobService` on fresh Alembic-head DB → exact registry
   set/order/revision map equals binding full band.
3. Second construction → idempotent.
4. Deliberate conflicting pre-registration → fails closed.
5. Real full RUN_QC_CHECKS submit/execute → no longer dies with
   `QC_ORCHESTRATOR_MISSING_ARGS`.

## Minimum revision matrix (fresh Alembic-head DB each row)

Only-2-audio registered + claimed ten → failed. Exactly one full-band
member unregistered → failed. Resolver raises → failed, no laundering.
One server revision rotated, completion stale → failed. Wrong / empty /
extra / missing completion revision → failed. All ten exact → completed.
Prior five identity-tamper rows still fail closed. No-source + real-source
controls accepted. API/project readiness propagates unavailable authority
as `not_run`.

## Worker exit-gate order (mandatory)

RED captured pre-fix on current bytes → micro C4-A/B matrix green → both
complete T03G modules green → configured Ruff on changed files → retained
mypy scope → own diff-check + write-set guard → self-review every
catch/default and every production import/registration → commit exact
allowlist, report SHA/raw, `TASK_SUBMITTED`, exit. No push/merge/rebase.

## Manager adversarial review (inspect code, not counts)

Allowlist containment + no shrink beyond guard threshold. Independent
clean-subprocess bootstrap rerun without importing tests. Mutation probes:
registry empty / member missing / resolver raise / wrong revision. Scan for
broad-except, guessed defaults, hidden test imports, global registry
pollution. Verify exact usage row for the recovery session. Reject
overclaim, masked exit, post-gate commit. Any red → same recovery session;
never the frozen old owner, never a second recovery session.

## Session transfer + transport notes (S11-C4 instance)

- Old owner frozen `FROZEN_CONTEXT_UNHEALTHY` with evidence (575 msgs / 507
  API calls, repeated exact-authority miss C2→C3, stale other-lanes-register
  assumption); zero active process confirmed; recorded in REGISTRY before
  dispatch; never resumed after.
- T03G branch FF to canonical via LOCAL objects when fetch is blocked:
  `git fetch` died on stray `refs/codex/turn-diffs/*` ("did not send all
  necessary objects") but `merge-base --is-ancestor T03G-tip canonical`
  was true, so `git merge --ff-only <canonical-SHA>` succeeded with no
  rebase/reset/force. Always ancestor-check first.
- Route divergence: exact prompt ID `cmc/muse-spark-1.3-contributor` absent
  from `/v1/models` (137 ids; only `cmc/meta/...` present) + zero-write
  probe 403 verbatim. Standing user mandate (100% muse-spark-1.3 via muse)
  outranks the prompt → run the mandated route, record divergence for the
  reviewer, never silent-swap, never block on it unilaterally.
- Machine-wide gates run SERIAL: T01's `test_12_no_process_leak` scans
  machine-wide ffmpeg PIDs → 63/64 when parallel with the inner suite,
  64/64 serial (269s). Parallel=false-positive is proven by the serial
  rerun, not by reasoning. Same applies to any port/lock/global-runtime
  gate sharing the box with heavy suites.
- Guard `FAILED` needs attribution, not panic: 5/5 drift with bytes/lines
  GROWING on allowlisted files = expected intentional change; shrink, lost
  definitions, or protected-file drift = red. Record which side before
  judging the ladder.

Result: recovery `5663484` + NUDGE5 `5449d13`, INT01 no-ff merge, 15/15
ladder green, one non-force push `28a2207..8f5af06`, terminal
`SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`.
