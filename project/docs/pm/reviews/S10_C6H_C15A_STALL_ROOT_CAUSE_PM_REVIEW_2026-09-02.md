# S10-C6H C15-A stall/root-cause PM review — 2026-09-02

## Verdict

`S10-C6H = CHANGES_REQUESTED / C15_A_HARNESS_ALIGNMENT_REQUIRED / NOT_APPROVED`

`S10-T01C-C15` has made real recovery progress, but C15-A is not closed and C15-B is not yet authorized to write production. One bounded C15-A helper-alignment correction is authorized under the existing combined-correction allowance. S11/S12/S13 remain out of scope.

## Independent state audit

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch: `codex/s08-integration`
- HEAD: `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`
- Current test authority candidate:
  - `tests/test_s10_full_apply_api.py`
  - SHA-256 `9B96B12FFE40F7A95E4CB96F78C9F68B8788092D99FE2BC2581289D031F9F313`
  - 62 textual test definitions, 62 unique, zero duplicate names
- Frozen production route:
  - `app/api/routes/s10_full_apply.py`
  - SHA-256 `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`
- No C15 worker is currently active. The Hermes processes observed at review time are only `hermes desktop` and its local `serve` process.

## What is complete

C15-A repaired the destructive-loss structure materially:

- 62/62 unique tests collect;
- `_C10BoomService` exists;
- the test module compiles;
- Ruff F checks pass;
- no skip/xfail was introduced;
- the production route stayed frozen.

This is valid progress and must not be discarded or rebuilt again.

## Blocking defect

The current helper generation is internally inconsistent with the recovered C8+ v2 authority contract:

1. `_make_client` lacks the keyword-only `route` parameter.
2. It persists `reskin_config.params_json='{}'`, although the v2 authority builder requires the full canonical reskin parameter contract.
3. It fabricates an obsolete `apply_checkpoint` row before the real v2 authority seed.
4. Its seed omits `reskin_config_id`.
5. It calls `_seed_persisted_authority` but not `_seed_v2_authority`.
6. `_payload` still sends stale client-owned authority copies by default instead of the minimal v2 submit body.

The recovered pre-destruction evidence in `output/s10/c6g/t01c-c14/recovery-t3/authoritative_lines.json` and `read_pages_content.txt` establishes the intended helper generation.

Independent probes proved the causal chain:

- current file: `test_submit_202_and_status` returns 422 because the stored checkpoint hash does not match recomputed content;
- adding only `_seed_v2_authority()` is insufficient: the empty reskin params fail validation;
- adding valid params and v2 authority while retaining the legacy `_payload` is still insufficient: `structural_lock_manifest.manifest_hash` mismatches;
- restoring valid params, real v2 authority seeding, and the minimal v2 payload returns HTTP 202.

Therefore the Manager's proposed one-line/one-call correction is incomplete. The authorized correction must align both `_make_client` and `_payload` as one bounded helper packet.

## Why Hermes keeps stopping

The new MotionForge rules are not the primary cause.

- The rules explicitly require continuous monitoring/correction until a terminal state; they do not authorize stopping after saying “I will continue.”
- The rules' safety requirements were beneficial here: they prevented another overwrite and require route freeze/evidence discipline.
- The heartbeat requirement adds overhead and does not map cleanly to Hermes Desktop delivery, but it is not what stopped C15-A.

The primary cause is orchestration behavior:

- the Manager emitted a final response before dispatching the promised next action; a desktop turn ends after the final response, so no later action can run without another user turn;
- it spent time investigating heartbeat/cron delivery even though cron has no active Hermes Desktop delivery adapter;
- it accepted the worker's “authority gap” classification without immediately testing the recovered authoritative helper evidence;
- after finding a likely correction, it reported the future action instead of dispatching it.

Hermes runtime/config behavior is a secondary cause:

- worker `20260902_164500_6e24fe` stopped at the default 90 tool-iteration ceiling;
- its continuation was effectively recorded as session `20260902_171240_ce07c1`, also with a 90-iteration ceiling;
- both worker state rows have `reasoning_config = null`, despite the requested `reasoning max` and local config values `agent.reasoning_effort=max`, `agent.max_turns=300`;
- the oneshot/resume path therefore did not honor the intended runtime settings.

Model quality is contributory but not the sole cause. `comboBAI` was fast and recovered much of the test file, but it misclassified a deterministic helper mismatch and stopped at the requested C15-A boundary. Better orchestration and exact evidence are more important than switching models again for this bounded correction.

## Session decision

- Resume the same Manager session: `20260902_100134_89bbc9`.
- Resume the actual latest C15 worker lineage: `20260902_171240_ce07c1`.
- If Hermes creates a new effective state-db session when `--resume` is used, record both the requested resume ID and returned/effective ID in the registry. It remains the same C15 Task, not a new Task.
- One writer only.
- Dispatch first and prove the worker process is active before any interim user-facing response.
- Do not investigate heartbeat/cron delivery during this closure.
- If the Manager final-stops once more before dispatching the authorized action, treat its context as unhealthy and open one compact replacement Manager session at the next review.

## Evidence corrections required

- Reconcile the registry's “same session” statement with effective continuation session `20260902_171240_ce07c1`.
- Regenerate or amend stale chain evidence that still reports test SHA `499438...`/2771 lines. The final repaired candidate is SHA `9B96...`; line counts must name the counting method.
- Record the actual worker `reasoning_config` and iteration ceiling from the Hermes state database. Do not claim `max` unless the runtime row proves it.

## Exit policy

After the bounded C15-A correction:

1. pass compile, Ruff F, collect=62, focused helper tests, and full `tests/test_s10_full_apply_api.py`;
2. run Manager R-GATE with the route still frozen;
3. only if R-GATE establishes trustworthy C6G RED production gaps, continue the same C15 lineage into C15-B;
4. complete the original 14-row closure matrix and all original exit gates;
5. stop only on a truthful terminal verdict.

