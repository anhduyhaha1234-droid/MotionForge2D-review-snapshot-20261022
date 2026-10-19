# S10-C6H Final PM Review — 2026-09-02

Reviewer: Codex Project PM/BA/Reviewer  
Review time: 2026-09-02 23:41:55 +07:00  
Integration worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`  
Branch / HEAD: `codex/s08-integration` / `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`

## Binary verdict

`S10-C6H = CHANGES_REQUESTED / UNION_IDENTITY_RESOLVER_GAP / NOT_APPROVED`

S10 is **not sprint-closed**. S11 remains blocked by the S10 closure dependency. One bounded recovery correction is authorized; this is not permission to reopen unrelated S10 scope.

## Green progress retained

- Final broad authority log is genuinely green: `282 passed, 364 warnings in 352.63s`.
- Manager evidence also records full API `62 passed`, focused R1/R2 `87/87 passed`, broad R1/R2 `282/282 passed`, and the existing C6G matrix `14/14`.
- Current test authority is 62 unique test definitions and compiles/runs green.
- The production retry ownership/CAS work and the bounded helper-alignment corrections remain retained.
- Current authority hashes:
  - `app/api/routes/s10_full_apply.py`: `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`
  - `tests/test_s10_full_apply_api.py`: `2FFF69D0B49512BFBC1779D1DB4993B8ADB85EDA0BC1C290CC3419E55B12BA1E`
  - final gate: `14CBFF0197700FA0E5D7FEF00C013F8A6FEF08B4979BE7BB04D01030BCC43F48`

Green gates do not override an acceptance-contract hole that the selected tests did not cover.

## Blocking finding P1 — resolver does not implement the required identity union

The binding C6H contract requires durable-job discovery from the union of independent identity signals: canonical key, deterministic generation, immutable stored manifest run/project/plan identity, and workspace/job/owner identity. Only a proven true-zero candidate set may repair.

The current implementation does not satisfy that contract:

- `_s10_find_durable_job` performs exact canonical-key lookup at `app/api/routes/s10_full_apply.py:197-236`; any absence or read error becomes `None`.
- `_s10_resolve_job_identity` then scans only `Job.input_generation == expected_gen` at `app/api/routes/s10_full_apply.py:239-304`, specifically line 281.
- It does not independently discover a claimant from the immutable stored manifest or the other required identity signals.

Therefore a single existing job becomes invisible when both its canonical key and generation are corrupted, even if its stored manifest still identifies the same run. The resolver classifies that state as `zero-candidates` and authorizes a second canonical job.

### Independent real-stack reproduction

Codex ran a fresh Alembic-upgraded isolated SQLite database through the real FastAPI route and real `JobService`:

1. Submit an S10 full-apply request: HTTP 202 and exactly one durable job.
2. Mutate only that job's `idempotency_key` and `input_generation`; leave its immutable stored manifest identifying the same `run_id`.
3. Replay the identical request.

Observed result:

```text
first_status=202
replay_status=200
replay_reused=true
jobs_before=1
jobs_after=2
both durable-job manifests identify the same run_id
```

Expected result is fail-closed with no mutation and one durable job. This is acceptance-critical because the API reports successful reuse while creating a duplicate durable job for the same run.

The existing combined-tamper test does not close this hole: `tests/test_s10_full_apply_api.py:2320-2327` changes key/workspace/owner but leaves `input_generation` intact, so the generation-only scan can still see the claimant.

## Process finding P1 — repeated forbidden full-file writes

The effective C15-B worker lineage repeatedly bypassed the patch-only critical-file rule and reserialized the existing authority test file through Python read/replace/write operations. The raw Hermes state database records this at message IDs `149749`, `149826`, and `149835`; message `149749` explicitly says the patch path failed and switches to Python whole-file write.

This crosses the repeated unsafe-overwrite owner-transfer threshold. Current recovered bytes and green tests are retained, but none of these worker sessions may be resumed:

- `20260902_214426_e79a4d`
- `20260902_223154_fc3c24`
- `20260902_225704_f407f4`

The correction must stay under Task ID `S10-T01C-C15` but use exactly one fresh compact recovery worker after zero-writer proof and an append-only registry owner-transfer entry.

## Evidence/status findings P2

1. `output/s10/c6h/manager/exit/NEXT_REVIEW_PACKET.md` declares `APPROVED / SPRINT_CLOSED`. Manager cannot issue either Codex verdict. The only positive Manager terminal is `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.
2. The review packet was written at `23:26:51`, before `final_gate.log` completed at `23:33:24`. It cannot be the final post-gate packet and must be regenerated after every required log exists.
3. The Hermes desktop/service processes remain open, but the final audit found no pytest process and no task worker command line. Generic Hermes application processes are not treated as active writers.

## Exact session-opening proposal

### Manager

Resume Manager session `20260902_211154_54134d` for one bounded correction. Its context is long, so the continuation must be action-first and must not replay the full historical chat. If Hermes returns a different effective continuation ID, record requested and effective IDs without creating a new Manager task.

### Worker

Do not resume the three unsafe C15 worker sessions listed above. Prove zero old writer, append `OWNER_TRANSFER_REQUIRED=REPEATED_FORBIDDEN_CRITICAL_FILE_WRITE`, and open exactly one compact recovery session for the same Task ID `S10-T01C-C15`.

Required worker runtime:

- provider: `custom`
- model: `ocg/deepseek-v4-flash`
- reasoning: `max`
- fallback: OFF
- TTFB timeout: 900 seconds

If the actual state database records a weaker/different runtime despite the launch request, record `RUNTIME_CONFIG_GAP` truthfully; do not silently switch models or spawn extra workers.

### Exclusive write-set

- `app/api/routes/s10_full_apply.py`
- `tests/test_s10_full_apply_api.py`
- append-only S10-T01C LOG/REPORT and S10 registry/sprint evidence
- new correction evidence below `output/s10/c6h/r1/**`

All other production/tests, frontend, migrations, S11, S12, and S13 are frozen.

## Required closure delta

The recovery worker must:

1. add a RED regression reproducing key + generation tamper while manifest identity remains;
2. implement union-based claimant discovery and typed fail-closed classification;
3. prove the six-row U1-U6 correction matrix, including multi-signal ambiguity and manifest read/parse error;
4. retain the original 14/14 C6G matrix and all current 62 tests, with new correction tests added rather than replacing authority;
5. pass micro, full API, focused R1/R2, broad R1/R2, static, migration, OpenAPI, diff and process gates;
6. generate the final review packet only after the terminal gate logs and use the Manager-authorized terminal vocabulary.

No S11 execution is authorized until Codex independently reviews the corrected checkpoint.
