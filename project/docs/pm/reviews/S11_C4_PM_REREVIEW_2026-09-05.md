# S11-C4 Independent PM/Code Review — 2026-09-05

## Verdict

`S11-C4 = CHANGES_REQUESTED / NOT_APPROVED`  
`S11 = NOT_CLOSED`  
`S12/S13 = BLOCKED`

The implementation improved materially over C3, but a binding model-route breach,
two production bootstrap defects, and non-closure-grade evidence remain. No
production or test implementation bytes were changed by this review.

## AUTHORITY_LOADED

Rules/authority were read in this review. The required rules and governance
files were hashed before the decision:

| Authority | SHA-256 | Lines |
|---|---|---:|
| `docs/pm/HERMES_AUTOPILOT_RULES.md` | `c9b068b2195461b1f867a5ec95714cea3ab09881757f5607094574d15dda428f` | 216 |
| `AGENTS.md` | `9208e0dea247b32f54ae24ed9fda8b85de79fcd0b4b3f54a2ae8b7d81218c4e6` | 4 |
| `frontend/AGENTS.md` | `e3447d84251880fb34cfae09131cb4c57471529bbfe60976a3245793cf621627` | 4 |
| `docs/pm/SESSION_PROTOCOL.md` | `e100656c8b2a8959c595234dfe51ebb832fbb5f8763f2243ad0423a62955eda6` | 142 |
| `docs/pm/CODEX_PM_HANDOFF.md` | `a8b89ef2584eb35e5d2b439947b463c53d1fa5e62e7c5a3e229a805f685130e3` | 1032 |
| `docs/pm/ROADMAP.md` | `ca294f7151d651ac2ff10f4bb88c416c7a4c4c65207bc61bac05ae0b198402bc` | 630 |
| `docs/pm/reviews/S11_C3_PM_REREVIEW_2026-09-05.md` | `49e49c2efad39fdef18866002ebc012ceafd866001f9b4e10e8ea692d93e4170` | 158 |
| C4 binding prompt | `d0f588fabc6c2023d04f19bf77d605ff5594e14a33199228860ad51334d52cb8` | 246 |
| C4 `manager/REGISTRY.md` | `2f553c4a8dc87c6a880aad1815de51f01835a0da5d44253fcc2da10e6ddc631d` | 23 |

The requested `docs/pm/sessions/S11-T03G/LOG.md` and `REPORT.md` do not exist
in the MAIN worktree at the literal requested paths. They do exist and were
read in the reviewed canonical worktree:
`C:\Users\Admin\MotionForge2D-worktrees\s11-integration\docs\pm\sessions\S11-T03G\`.
That path discrepancy is recorded, not silently normalized.

Reviewed tree/time: canonical `codex/s11-integration`, HEAD
`8f5af068978265a0dc347db97099f897e1eb5a49`, local==remote, porcelain empty;
review boundary 2026-09-05 09:10 UTC. Evidence root:
`C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-034450`.

## Git, ownership, runtime and route reconciliation

- `28a22072c27a9cd5d1e5eacca82bf9740ce3558c` is an ancestor of the reviewed
  HEAD. The actual diff is 9 paths: 3 production files, 2 T03G test files and
  4 T03G/INT01 PM documents. Canonical worktree is clean; MAIN is independently
  dirty with unrelated user work and was not cleaned.
- Recovery commit chain is `5663484` then `5449d13`; INT01 merge/docs are
  `80bd36a` and `8f5af06`. The old owner
  `20260903_170546_0d42f6` is frozen; no project writer, pytest, ffmpeg,
  watchdog, cron or heartbeat process was active at the review boundary.
- Read-only SQLite URI `file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro&immutable=1`
  shows exact probe session `20260905_034616_e72a18` with model
  `cmc/muse-spark-1.3-contributor`; its durable raw output is HTTP 403
  “Model/provider not recognized” and `PROBE_EXIT=1`. `/v1/models` currently
  lists `cmc/meta/muse-spark-1.3-contributor`, not the exact required ID.
  Recovery session `20260905_043139_01a91f` has durable model
  `cmc/meta/muse-spark-1.3-contributor` and was therefore an alias route.
- This is a contract-blocking route violation, not an evidence-only defect.
  The current explicit instruction pins the exact ID and fallback OFF; no newer
  user instruction authorizes alias substitution. C4 therefore cannot be
  approved or dispatched further under the required route.

## Positive evidence

- Fresh independent run on current bytes: both complete T03G modules, `143
  passed`, exit 0.
- Fresh T05A consumer run: `14 passed`, exit 0.
- Fresh targeted T12 runs on two separate basetemp roots: `1 passed` + `1
  passed`, exit 0. The retained C4 full T06/outer/inner and S10 evidence is
  consistent with `12`, `12`, `425`, and `71` passes, but its packet arithmetic
  is not sufficient to close the evidence findings below.
- Ruff configured scope: exit 0. Mypy binding scope
  `qc_check_runs.py` + `readiness.py`: exit 0. `git diff --check` against both
  `28a2207` and `7751598`: exit 0. Alembic has exactly one head
  `f9a0b1c2d3e4`; a fresh isolated upgrade to head exited 0. Direct OpenAPI
  scan: 274 paths, 340 operations, 0 duplicate operation IDs.
- A fresh process probe with no detector/test imports before `JobService()` saw
  registry `[]` and then the exact 10-name ordered band after construction.
  This confirms the intended current path works in this snapshot; it does not
  repair the missing durable regression test or the failure-atomicity defects.

## Findings

### P1 — binding model route breach

Evidence: `manager/raw/route-models.json`, `route-probe-exact.log`,
`route-probe-meta.log`, and read-only `sessions`/`session_model_usage` rows.
Expected: exact `cmc/muse-spark-1.3-contributor`, custom 9Router,
`http://127.0.0.1:20128/v1`, reasoning `max`, fallback OFF. Actual: exact probe
returned 403 and the worker used `cmc/meta/muse-spark-1.3-contributor`.
Impact: C4 worker/model evidence cannot be attributed to the requested exact
route; the substitution violates the explicit route contract. Required action:
stop at `BLOCKED_MODEL_ROUTE`; do not retry with alias, inherited session or
another model. Owner routing is the exact S11-T03G recovery lineage only after
an exact route becomes valid.

### P1 — bootstrap retains ghost registrations and is not failure-atomic

Location: `app/workflow/qc_checks_handler.py:251-412`, with the production hook
at `app/workflow/job_service.py:231-243`.

Fresh isolated probes on the reviewed HEAD:

- Pre-registering `ghost_detector` returns success and leaves 11 registry
  entries after bootstrap, even though the binding full band is exactly 10.
- Pre-registering `trajectory_drift` with `wrong:entry@9.9.9` raises
  `QC_RUN_BOOTSTRAP_CONFLICT`, but leaves the wrong entry plus six imported
  detector entries in the registry. A second call still fails because the
  partial state was not rolled back.

Expected: the full-band contract must reject or otherwise fail closed on a
non-authoritative extra, and every import/explicit-registration/conflict error
must restore the complete pre-call registry snapshot. Required tests must
assert full registry equality after each failure, same-entry/different-version,
same-name/different-entry, import failure, explicit registration failure and
concurrent constructor cases.

### P1 — clean-process regression proof is not durable

Both T03G modules call `ensure_full_band_registered()` in autouse fixtures
(`tests/test_s11_t03g_qc_check_job.py:57-61` and the API module equivalent).
The submitted green probe imports `test_s11_t03g_qc_check_job` before constructing
`JobService` (`lanes/c4-recovery/green_probe_c4.py:22`), and that test module
imports detector modules. Therefore it is not a valid proof that the production
hook alone bootstraps a clean process, and removing the hook would not be caught
by the current T03G suite. Required action: add a durable subprocess regression
test that starts with an empty registry, imports normal app code only, constructs
the real owned `JobService`, and fails if the production hook is removed.

### P1 — closure packet overclaims gate/evidence status

The raw guard artifact is literally `{"status":"FAILED","failures":5}` in
`manager/raw/guard-verify.json`, while EXIT_VERDICT labels the guard green. A
fresh rerun with the five explicit allow-change paths verifies `0/5`, showing
the bytes are not shrinking and the original command likely omitted its
allowlist; it does not make the submitted failed artifact green retroactively.
The packet also places `int01-c4-gate.txt` outside the exact C4 run-root and
does not provide raw individual proof for every required hash, process/port
cleanup, Alembic, direct OpenAPI and final local==remote row.

The T12 map has one dedicated `lane-V2a.log` run and one T12 invocation embedded
in `lane-V2full.log`; it does not prove the exact required sequence of two
dedicated targeted T12 runs on separate roots followed by full T06. The V1 row
also labels combined `157` tests as T05A although T05A itself is `14`.
These are binding closure/evidence defects even though the product consumers
are green. The earlier parallel T01 run failed `63/64` on process-leak
visibility while the serial rerun passed `64/64`; this is an orchestration
mistake, not a demonstrated C4 product defect, but the final packet must retain
both raw facts and not rewrite the failed run.

## Code/model/process assessment

C4 is better than C3 on production composition and revision fail-closed intent:
the `JobService` hook is on the real owned-worker path, the current revision
resolver no longer guesses an expected map on resolver failure, and the 143-row
T03G matrix plus static gates are useful. The remaining bootstrap is too large
and globally mutating for its contract without rollback/serialization, and test
fixtures still mask the critical startup boundary. No quality claim can be
attributed to the requested exact model because the exact route never ran; the
green implementation came through an unauthorized alias session.

## Finite correction matrix and routing

No implementation worker is authorized while the exact route is unavailable.
When and only when the exact route is valid, resume the existing recovery
lineage `20260905_043139_01a91f` for the same S11-T03G correction; do not resume
the frozen `20260903_170546_0d42f6` owner and do not create recovery session 2.

| Task | Owner | Required outcome | Evidence |
|---|---|---|---|
| C4-R1-A | exact S11-T03G recovery lineage | exact-ten/no-ghost bootstrap, full snapshot rollback on all failures, safe concurrent construction, durable clean-process regression | fresh subprocess + adversarial registry matrix + full T03G modules |
| C4-R1-B | exact S11-T03G recovery lineage | resolver-raise, missing/extra/empty/wrong/current-changed revisions and no-source/real-source controls; no guessed authority | fresh Alembic-head matrix and API/readiness propagation |
| C4-R1-C | new compact Manager only after route gate | correct the C4 run-root packet: registry identity, guard allowlist result, two dedicated T12 runs then full T06, every raw gate, final quiescence/local==remote | new run-root with command/exit/duration/timestamp/hash index |

## Session Opening Proposal

`PROPOSED_ONLY` is not safe; the current state is
`BLOCKED_DEPENDENCY/MODEL_ROUTE`. Start with one new compact Manager only for
preflight/route validation, exact model `cmc/muse-spark-1.3-contributor`, custom
9Router, base URL `http://127.0.0.1:20128/v1`, reasoning `max`, fallback OFF.
Maximum safe implementation wave is zero; unused slots are deliberate because
there is no valid route and the correction write-set must not be touched.
After exact route validity is proven, the correction is a resume of the exact
recovery lineage, with no second writer and no parallel implementation. INT01
remains Git-only and cannot edit implementation/test bytes.

## Decision

`CHANGES_REQUESTED`. Do not authorize S12/S13. The complete next Hermes prompt
is saved at `docs/pm/prompts/S11_C4_R1_BOOTSTRAP_ATOMICITY_ROUTE_BLOCKED_2026-09-05.md`
and is pasted verbatim in the Codex response.
