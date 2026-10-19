# S11-C3 — Codex Independent PM/BA/Code Rereview

**Review date:** 2026-09-05 +07  
**Reviewed tree:** `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`  
**Branch / local HEAD:** `codex/s11-integration` @ `28a22072c27a9cd5d1e5eacca82bf9740ce3558c`  
**Remote HEAD:** `origin/codex/s11-integration` @ `28a22072c27a9cd5d1e5eacca82bf9740ce3558c`  
**Submission claim:** `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`  
**Codex verdict:** `CHANGES_REQUESTED / NOT_APPROVED / S11_NOT_CLOSED`

## 1. Decision

C3 closes the five explicit C2 identity-tamper examples and materially
strengthens the targeted correction/recompute restart proof. The canonical
tree is clean, pushed and green for the covered tests.

S11 still cannot close. A fresh production process has no registered QC
detectors, so a real full check-run cannot execute. Independently, the new
read-authority implementation catches loss of server revision authority and
substitutes a guessed `1.0.0`; a forged ten-detector completion is therefore
accepted as `completed` when only two detector revisions are known. The test
suite hides both defects by importing/registering detectors in test fixtures.

The C3 terminal packet is also non-authoritative: it admits the exact CMC route
returned 403, then continued on inherited sessions without `-m`; it ran only
7 of the required 15 final gates, omitted `manager/REGISTRY.md`, and copied the
live Hermes DB despite the prompt's read-only/no-copy rule.

## 2. Positive evidence retained

- Canonical porcelain is empty and local equals GitHub at `28a2207`.
- `git diff --check 7751598..28a2207` exits 0.
- Codex independently reran current bytes:
  - T03G job module: `127 passed, 254 warnings in 149.45s`;
  - T03G API module: `16 passed, 33 warnings in 21.36s`;
  - T06C targeted correction/recompute restart twice on isolated roots:
    `1 passed` in 4.48s and `1 passed` in 4.41s;
  - both T05A modules: `9 + 5 = 14 passed`;
  - required `ruff --select F`: green;
  - retained mypy scope: `Success: no issues found in 2 source files`.
- The strengthened T12 test now snapshots affected and unaffected rows/bytes,
  positively binds new outputs to the affected role and re-reads QC/readiness.
  It passes current production, so no T04B product correction is justified.
- The previous schema/policy/evidence/source/generation tamper rows now fail
  closed, and valid no-source/real-source controls remain accepted.

## 3. Findings

### [P1] Clean production bootstrap registers zero of the binding detectors

**Locations:**

- `app/workflow/job_service.py:226-233`
- `app/workflow/qc_checks_handler.py:93-108`
- `app/services/qc_checks/orchestrator.py:557-568`
- `tests/test_s11_t03g_qc_check_job.py:57-98`
- `tests/test_s11_t02_t06_acceptance.py:1089-1134`

`JobService` registers the `RUN_QC_CHECKS` handler but does not register its
detector band. Seven detector modules self-register only when imported; three
require an explicit `register()` call. Normal app/JobService startup imports
neither the full set nor those explicit registrations. The orchestrator
correctly rejects an unregistered requested detector, so the missing bootstrap
prevents the feature from running.

Codex ran two clean-subprocess probes on the reviewed tree:

```text
from app.main import app
registry.names() -> []

JobService(real Alembic-head DB, real owned worker)
registry.names() -> []

run_full_check_set(... full binding band ...)
QcRunnerError code=QC_ORCHESTRATOR_MISSING_ARGS
unregistered detectors requested: all 10 binding names
```

Existing green tests import seven detector modules and explicitly register the
remaining three before exercising the product. They therefore prove behavior
only in a polluted test process, not production bootstrap.

**Expected:** constructing the real production `JobService` deterministically
registers exactly the server-owned binding band before a full job can run.  
**Actual:** registry remains empty and the job fails before execution.  
**Impact:** the central S11 full-QC workflow is unusable after a clean process
start.  
**Owner:** S11-T03G durable-handler composition. The old owner session
`20260903_170546_0d42f6` requires recovery transfer under the context-health
decision below.

### [P1] Revision authority fails open through a hard-coded fallback

**Location:** `app/persistence/qc_check_runs.py:554-579`

C3 calls the correct server resolver, but catches every exception and replaces
the result with `{}`. Each missing detector then gets a guessed expected
revision of `1.0.0`:

```python
try:
    expected_revisions = _server_detector_revisions(list(band))
except Exception:
    expected_revisions = {}

expected_revisions.get(name, "1.0.0")
```

Codex used a fresh Alembic-head DB and the current T03G helpers. The process had
only the two audio detectors registered, while the seeded completion claimed
all ten revisions as `1.0.0`. Expected was `failed`/readiness `not_run` because
8/10 server authorities were unavailable. Actual was:

```text
REGISTERED ['audio_missing', 'av_sync_drift']
ACTUAL_STATE completed
ACTUAL_DETAIL completed current FULL-scope run ... proving ... 10-detector coverage
```

This directly violates C3's requirement that completion equal exact
`detector_revisions(full_coverage_detectors())`, with no fallback. Registry
error, missing member, incomplete keyset or empty server revision must all fail
closed. A valid control with all ten exact server revisions must remain green.

**Owner:** same S11-T03G recovery owner as finding 1.

### [P1] C3 terminal evidence violates the binding route and closure contract

`NEXT_REVIEW_PACKET.md` explicitly says the exact
`cmc/muse-spark-1.3-contributor` custom route returned 403, then the Manager
continued with inherited sessions “không pin -m”. Read-only Hermes
`session_model_usage` records later implementation/integration calls as
`meta`, while the durable sessions still carry older DeepSeek/Muse routes.
Fallback was OFF; route failure authorized `BLOCKED_MODEL_ROUTE`, not silent
continuation.

The Manager then reported a 7-gate M3 subset instead of the binding 15-gate
ladder. It omitted the fresh five-row standalone matrix, combined focused gate,
fresh Alembic upgrade, direct OpenAPI scan, outer/inner thresholds, T01 64,
S10 71, protected hashes and final process/timestamp proof. Required
`manager/REGISTRY.md` does not exist. The packet also lists a
`state-main-ro-copy.db`, contrary to the no-copy rule for live Hermes state.

This finding independently rejects the submission even if implementation tests
were all correct. A future packet may not summarize a subset as full closure.

**Owners:** new compact C4 Manager for evidence/gates; exact INT01 session
`20260903_112116_35051c` only for verified Git transport.

### [P2] Code hygiene is below the repository's configured lint baseline

The narrow contractual `ruff --select F` gate is green, but normal configured
Ruff on the affected source/tests reports 19 issues. C3-affected examples
include unsorted imports and missing final newlines in
`qc_check_runs.py`/`test_s11_t03g_qc_check_job.py`; the handler also lacks a
final newline. These do not cause the P1 behavior, but they are consistent with
fast whole-file style output and should be fixed only in the bounded T03G
write-set while the production defects are corrected.

## 4. Code-quality assessment

The C3 code is stronger than C2 in breadth and mechanical regression coverage:
the 143 T03G tests, exact source identity checks and T12 restart assertions are
useful. The weak point is production-boundary reasoning. To make a partial
test registry pass, the implementation encoded the test convention
`1.0.0` as production authority and then caught all resolver failures. This is
a classic test-shaped fix: broad green counts, but a clean process fails.

Assessment: test construction is good; exact fail-closed logic and production
composition are not yet release quality. Keep the speed advantage of Muse, but
require clean-process probes and mutation/adversarial rows before broad suites.
Do not infer quality from duration or pass count alone.

## 5. Context-health and session-opening decision

`AUTHORIZED_TO_DISPATCH` only for bounded `S11-C4`; S12/S13 remain blocked.

- Open one **new compact C4 Manager session**. Do not resume the C3 Manager,
  which violated both route and closure evidence contracts.
- Freeze the old T03G owner `20260903_170546_0d42f6` and transfer the same
  S11-T03G correction lineage to exactly one fresh recovery session. Evidence:
  575 messages, 507 API calls, multiple compression/model records, and the
  same exact-authority miss repeated from C2 into C3 while comments retain the
  stale pre-integration assumption that other lanes own missing registration.
  No T03G writer is currently active. Record the transfer before dispatch and
  never resume the old owner after transfer.
- Reuse the existing clean T03G branch/worktree, fast-forward it to canonical
  `28a2207`, then allow one recovery writer only. Do not create a second branch
  or concurrent implementation owner.
- Use exact custom 9Router model `cmc/muse-spark-1.3-contributor`, requested
  reasoning `max`, fallback OFF. Because this route returned 403 in C3, C4 must
  probe it before opening the writer; persistent route failure is
  `BLOCKED_MODEL_ROUTE`, never permission to inherit `meta` or another model.
- After the one writer exits, run isolated read-only verification lanes in
  parallel, then resume exact Git-only INT01 for conflict-free integration,
  one complete fail-fast ladder and one non-force push.

Binding prompt:
`docs/pm/prompts/S11_C4_PRODUCTION_REGISTRY_FAIL_CLOSED_FINAL_EXIT_MANAGER_2026-09-05.md`.
