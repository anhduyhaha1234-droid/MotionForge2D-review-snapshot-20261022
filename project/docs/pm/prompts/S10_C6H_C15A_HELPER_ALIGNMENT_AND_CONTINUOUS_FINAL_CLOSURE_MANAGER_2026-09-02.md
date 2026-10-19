# HERMES MANAGER PROMPT — S10-C6H C15-A helper alignment + continuous final closure

You are the Hermes Task Manager for MotionForge2D S10-C6H. This is an authorized continuation of the existing C15 Task, not a new sprint and not a new Task.

## 0. Mandatory source-of-truth read

Before any mutation, read the following files in full:

1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
   - canonical SHA-256 at Codex review: `9328C8C0672EA0040D278B2A00C81C1DBD24B4C72FF87C68FDA3A357A44B61BC`
2. every applicable `AGENTS.md` from repo root to the target paths;
3. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`;
4. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6H_TEST_AUTHORITY_REBASELINE_AND_FINAL_CLOSURE_MANAGER_2026-09-02.md`
   - canonical SHA-256 at Codex review: `625F1FDB0A326A2FE550ED8E0E67524835A9B7DAA7F54043BEA83A4A356A4426`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6H_C15A_STALL_ROOT_CAUSE_PM_REVIEW_2026-09-02.md`.

If any canonical hash differs, stop before mutation and report the exact path, expected hash, actual hash, and whether the change is authorized. Otherwise continue without asking the user.

## 1. Binding Codex verdict

`S10-C6H = CHANGES_REQUESTED / C15_A_HARNESS_ALIGNMENT_REQUIRED / NOT_APPROVED`

C15-A has real structural progress but is not closed. One bounded combined C15-A helper-alignment correction is authorized. C15-B may begin only after Manager R-GATE passes. S11/S12/S13 are forbidden.

Do not rebuild the test module. Do not replace it from memory. Do not use whole-file `write_file`, generated overwrite, copy-over, or delete/recreate. Use narrow patch hunks only and verify the diff immediately.

## 2. Known ground truth at dispatch

Worktree:

`C:\Users\Admin\MotionForge2D-worktrees\s08-integration`

Expected branch/HEAD:

- branch `codex/s08-integration`
- HEAD `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`

Candidate test file:

- `tests/test_s10_full_apply_api.py`
- expected pre-correction SHA-256 `9B96B12FFE40F7A95E4CB96F78C9F68B8788092D99FE2BC2581289D031F9F313`
- expected 62 textual test definitions, 62 unique, zero duplicate names

Frozen production route:

- `app/api/routes/s10_full_apply.py`
- frozen SHA-256 `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`

Existing Manager session:

`20260902_100134_89bbc9`

Actual latest effective C15 worker lineage to resume:

`20260902_171240_ce07c1`

The earlier ID `20260902_164500_6e24fe` hit the 90-iteration ceiling. Do not resume that stale state as if it were latest.

## 3. Action-first, no false continuation

This prompt must be executed, not summarized.

In this Manager turn:

1. perform read-only preflight;
2. dispatch/resume the worker;
3. prove the child process/session is active;
4. monitor it;
5. review its evidence;
6. dispatch any already-authorized next phase before emitting an interim final response;
7. continue until a truthful terminal state.

Never emit a final response saying “I will dispatch/continue next” if the process has not already been dispatched. A final response ends the desktop turn.

Do not spend time debugging heartbeat, cron, Telegram, desktop delivery, or notification plumbing. The active worker process plus normal completion notification is the liveness mechanism for this bounded closure. Maintain required heartbeat files only as lightweight task evidence; do not treat them as a delivery system.

## 4. Runtime/model contract

The user's latest explicit override applies to every remaining C15 worker
dispatch/resume/continuation in this prompt and supersedes only the old
`comboBAI` model clauses in the original C6H binding prompt and prior review.
All ownership, scope, safety, test and exit requirements remain unchanged.

Use this exact route:

- exact model ID: `ocg/deepseek-v4-flash`
- provider: `custom` (local 9Router route)
- fallback: OFF; never route through `comboBAI`, BAI, GLM, bare
  `deepseek-v4-flash`, OpenRouter/CMC, Meta/Muse or another model
- worker reasoning target: `max`
- `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`

Probe the full model ID before dispatch and preserve raw non-secret evidence.
The probe/worker log must show effective model `ocg/deepseek-v4-flash` and
provider `custom`. A bare `deepseek-v4-flash` is not equivalent. Resume with
the exact full model override, for example:

```powershell
$env:HERMES_CODEX_TTFB_TIMEOUT_SECONDS = "900"
hermes --resume 20260902_171240_ce07c1 --provider custom -m ocg/deepseek-v4-flash --yolo --no-restore-cwd -z "<the bounded C15 correction packet from this prompt>"
```

If that exact route is unavailable or resolves to a different effective model,
stop `BLOCKED_MODEL_ROUTE` with the probe command/status and do not fallback.

Before the worker's first write, inspect the effective worker state/config. Prior worker state rows recorded `reasoning_config = null` and `max_iterations = 90` even though local config requested max/300. Use a supported Hermes invocation/config path that actually records the intended setting if available.

Do not claim `reasoning max` unless the effective state row proves it. If Hermes still records null/90, log `RUNTIME_CONFIG_GAP` with the exact command and state-row values, then continue this deterministic bounded correction on the same exact `ocg/deepseek-v4-flash` route with extra Manager verification; do not switch models and do not stop solely for that runtime limitation.

If `hermes --resume 20260902_171240_ce07c1 ...` creates another effective state-db session ID, immediately record:

- requested resume ID;
- actual effective/returned session ID;
- timestamp;
- same Task identity `S10-T01C-C15`;
- same single-writer ownership.

## 5. Preflight and ownership

Confirm before mutation:

- exact worktree, branch, HEAD, dirty inventory;
- `MOTIONFORGE_DB_PATH` is unset and no MAIN DB is in scope;
- no live competing writer owns C15;
- candidate test hash/structure matches Section 2;
- frozen route hash matches Section 2;
- pre-edit byte snapshot of the test file exists in the C15 evidence directory;
- append-only session LOG/REPORT/registry paths exist.

If the test candidate hash differs because another writer has changed it, do not overwrite. Identify that process/session, inspect the diff, and either adopt its verified result or stop with an exact ownership conflict.

## 6. Authorized C15-A correction packet

The defect is a deterministic helper-generation mismatch, not a reason to reconstruct the module and not yet a production defect.

Authoritative pre-destruction evidence:

- `output/s10/c6g/t01c-c14/recovery-t3/authoritative_lines.json`
- `output/s10/c6g/t01c-c14/recovery-t3/read_pages_content.txt`

Patch only the relevant `_make_client` and `_payload` blocks in `tests/test_s10_full_apply_api.py`. Preserve all 62 test functions and all unrelated helpers byte-for-byte where practical.

### 6.1 `_make_client` required result

Restore the signature:

```python
def _make_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    route: str = "sprite_affine",
) -> tuple[TestClient, dict[str, str]]:
```

Equivalent one-line formatting is acceptable; semantics are not negotiable.

In its seed transaction:

- create workspace/project/video/scene/character/pack/role/reskin rows;
- persist canonical valid reskin parameters, not `{}`:

```python
valid_params = {
    "anchor": {"x": 0.5, "y": 0.5},
    "scale": 1.0,
    "fit_mode": "contain",
    "clip_mode": "asset_alpha",
    "offset": {"x": 0.0, "y": 0.0},
    "rotation_offset_deg": 0.0,
    "opacity": 1.0,
}
```

- serialize with deterministic `json.dumps(valid_params, sort_keys=True, separators=(",", ":"))`;
- do not fabricate the obsolete pre-v2 `apply_checkpoint` row;
- seed initially contains `workspace_id`, `project_id`, `video_item_id`, `pack_version_id`, and `reskin_config_id`;
- after commit call exactly, in order:

```python
_seed_persisted_authority(factory, artifacts_root, seed)
_seed_v2_authority(factory, artifacts_root, seed, route=route)
```

- return `TestClient(app), seed` as before.

The real `_seed_v2_authority` result owns `checkpoint_id`, `checkpoint_hash`, checkpoint revision, manifest ID/hash, and frozen full-apply authority. Do not preserve or blend the fabricated legacy checkpoint.

### 6.2 `_payload` required result

Default public submit must be the minimal v2 body:

```python
def _payload(seed: dict[str, str], **overrides) -> dict:
    base = {
        "video_item_id": seed["video_item_id"],
        "apply_checkpoint_id": seed["checkpoint_id"],
        "expected_checkpoint_hash": seed["checkpoint_hash"],
        "expected_checkpoint_revision": int(seed.get("checkpoint_revision", 1)),
        "chunk_config": {"chunk_frames": 25, "overlap_frames": 4},
    }
    base.update(overrides)
    return base
```

Keep the recovered explanatory docstring if present. Do not include `approved_checkpoint`, `structural_lock_manifest`, `scene_manifest`, or `mapping` in the default body. Tamper tests may pass those legacy copies explicitly through `overrides`.

### 6.3 Immediate diff guard

Immediately after patching, prove:

- only the two intended helper regions changed;
- test count remains 62/62 unique;
- `_C10BoomService` remains defined;
- no production file changed;
- route hash remains frozen;
- no skip/xfail/fake pass was introduced.

If any guard fails, revert only the worker's narrow hunk from the pre-edit byte snapshot and correct it. Never replace the whole test file.

## 7. Required focused verification

Use the project interpreter/environment already established by the original C6H prompt. Run and capture exact commands, exits, stdout/stderr, elapsed times, and post-command hashes.

First compile and lint:

```powershell
python -m py_compile tests/test_s10_full_apply_api.py
python -m ruff check tests/test_s10_full_apply_api.py --select F
```

Then collect:

```powershell
python -m pytest tests/test_s10_full_apply_api.py --collect-only -q
```

Expected: 62 collected, no collection errors, no skip/xfail.

Then run this focused helper/authority packet:

```powershell
python -m pytest tests/test_s10_full_apply_api.py -q -k "test_submit_202_and_status or test_minimal_submit_omits_legacy_authority_succeeds or test_client_legacy_authority_tamper_fails_closed_zero_run_job or test_unsupported_route_never_coerced or test_openapi_submit_required_minimal"
```

All five selected tests must pass. `test_unsupported_route_never_coerced` must actually exercise `_make_client(..., route=bad_route)` rather than being edited around.

Then run the entire module:

```powershell
python -m pytest tests/test_s10_full_apply_api.py -q
```

Expected C15-A outcome: 62 passed. If failures remain, classify each against the original/recovered authority evidence. Do not change production during C15-A.

Only one additional narrow correction inside the already-authorized helper packet is permitted. Any unrelated failure requires truthful escalation with exact failing tests and stack traces.

## 8. Manager R-GATE

When C15-A verification completes, the worker exits and releases ownership. The Manager must immediately run R-GATE before production is unfrozen.

R-GATE must independently verify:

- candidate post-correction SHA and line-count method;
- 62/62 unique tests;
- compile/Ruff/collect/full-module evidence;
- focused helper packet evidence;
- exact diff is limited to authorized helper regions plus append-only task evidence;
- route still equals SHA `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`;
- no MAIN DB, no competing writer, ports/processes clean;
- no stale or contradictory evidence is being cited.

R-GATE verdict is binary:

- `C15_A_REBASELINE_APPROVED`: test authority is trustworthy; continue immediately to C15-B under the original C6H prompt; or
- `C15_A_REBASELINE_REJECTED`: state exact unmet predicates and stop without production mutation.

Do not call a clean 62-pass result “blocked test authority.”

## 9. Continuous C15-B and final S10-C6H closure

If R-GATE is `C15_A_REBASELINE_APPROVED`, dispatch/resume the same effective C15 lineage for C15-B in the same Manager turn before any final response. Do not ask the user to say “continue.”

C15-B must follow every requirement and exit gate in:

`S10_C6H_TEST_AUTHORITY_REBASELINE_AND_FINAL_CLOSURE_MANAGER_2026-09-02.md`

In particular:

- use the rebaselined 62-test module as authority;
- execute the original C6G 14-row closure matrix;
- distinguish harness GREEN from genuine production RED;
- make the smallest production correction only for independently reproduced production defects;
- preserve durable identity, concurrency, fail-closed, zero-side-effect, and evidence-integrity requirements;
- run focused, module, broad, and final-broad gates exactly as specified;
- no S11/S12/S13 work;
- no fallback model;
- no overclaim from stale evidence.

If the worker reaches its iteration ceiling, resume the latest effective session immediately, record the new effective session ID, and continue. Iteration exhaustion is not a sprint verdict.

## 10. Evidence/registry reconciliation

Before exit:

1. correct the registry wording that called the continuation “same session”; retain lineage continuity but record effective session `20260902_171240_ce07c1` and any subsequent effective ID;
2. amend/regenerate chain evidence that still reports stale test SHA `499438...` and 2771 lines;
3. report the final SHA and state the line-count convention used (`Get-Content`, raw newline count, or tool output);
4. record actual runtime state values for `reasoning_config` and `max_iterations`;
5. include all commands, exit codes, timestamps, process/port cleanup, and writer release;
6. preserve append-only LOG/REPORT/registry history; corrections must identify superseded statements rather than silently rewriting history.

## 11. Stop conditions and required terminal response

Valid terminal outcomes only:

- `S10-C6H = APPROVED / SPRINT_CLOSED` after all original C6H/C6G exit gates pass; or
- `S10-C6H = CHANGES_REQUESTED / <exact bounded unmet predicate> / NOT_APPROVED`; or
- a truthful environmental/authority block with exact evidence and no safe authorized continuation.

Do not stop because:

- a worker turn ended;
- a worker hit 90 iterations;
- C15-A ended as instructed;
- heartbeat delivery is unavailable;
- the Manager already sent an update;
- the task is taking a long time.

Before any terminal response, prove:

- zero live writer;
- heartbeat removed or marked terminal;
- owned ports free;
- registry/LOG/REPORT/exit evidence updated;
- no promised future dispatch remains undone.

Your terminal response must begin with the exact final verdict, list the effective worker session lineage, summarize test/route hashes and gates, and link the exit evidence. Never say “I will continue” in a terminal response.

Execute now.
