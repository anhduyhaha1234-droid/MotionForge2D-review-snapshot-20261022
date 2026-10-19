# Cap-ended rounds: verify the claim, snapshot the uncommitted bytes, order the continuation

Session: 2026-09-22, MotionForge MF-RESKIN-MODEL-UPGRADE wave 1 (3 disjoint CPU workers).
Manager session `20260922_104152_8d11d1`; evidence root
`.../outputs/mf-reskin-model-upgrade-20260922/20260922T0345Z/`.

Two of the three Wave-1 lanes stopped on the tool-call cap rather than on a technical blocker.
Both had landed real work; neither was gateable. This is the handling that worked.

## 1. Receipts: exit 0 with two very different meanings

| lane | duration | exit | self-reported | on disk |
|---|---|---|---|---|
| MF-V1-BENCH R1 | 1,532 s | 0 | `TASK_SUBMITTED`, own commit | committed `36c912e`, parent `2594de06` (wave base), porcelain clean |
| MF-V1-COMFY R6 | 2,304 s | 0 | **`RUNNING`** (honest) | **no commit**, 8 modified + 1 untracked |
| MF-V1-VIDEO14B R1 | 2,469 s | 0 | `RUNNING` (honest) | untracked `experiments/`, no commit |

The COMFY lane's own closing text was the most valuable artifact of the round:

```
RUNNING — iteration budget exhausted mid-gate. Not TASK_SUBMITTED: evidence set
incomplete and nothing committed. Honest state below.
…
- No HANDOFF.md, no REPORT.md, no raw/gate_matrix.json, no raw/micro_tests.txt, no
  raw/guard_after.json, no before/after hash table, no MODEL_CAPABILITIES.diff.md — F06
  is untouched.
- No local commit; the worktree is DIRTY with all of the above.
- The very last edit (a new real-server test …) was written but NEVER RUN — the server is
  already stopped, so it is currently unverified/uncommitted test code. That is the first
  thing to run or revert.
```

## 2. Manager verification of the cap-ended COMFY round

The claim being tested was: F01 (queued-timeout releases the GPU gate while the server still
executes the prompt) is fixed by a durable `PromptReservations` ledger plus a typed
`UnresolvedReservation` refusal in the gate.

- **Re-ran the lane's own suite in its worktree** (`python -m pytest tests/ -q
  -p no:cacheprovider`) → **114 passed, 10 skipped in 4.19 s**. The 10th skip is the
  real-server case while the engine is down (the lane reported 9 skips with the engine up).
  The claim is verified; the task is not delivered.
- **Byte-attributed every touched file against the write-set preimage**: all 8 modified files
  **grew** — `adapter.py` 442→739 lines, `lease.py` 208→442, `gpugate.py` 140→263,
  `errors.py` 196→222, `contract.py` 132→136, `__init__.py` 23→36, `tests/fake_transport.py`
  236→267, `tests/test_real_server.py` 231→299. Nothing shrank ⇒ no destructive-shrink red.
- **Real-server gate (6 steps, ComfyUI 0.28.2 / 808 nodes on 127.0.0.1:8199)**, reported by the
  lane and consistent with the reproduction probe: step1 `unresolved` + marker on disk;
  step2 caller-2 bare gate `acquired=false` / `MF_COMFY_UNRESOLVED_RESERVATION`; step3 caller-2
  with reconcile callback refused, outcome `queued`; step4 restarted adapter **adopted the same
  `prompt_id`, `submit_count 0`**; step5 real `/interrupt` → `interrupt_count 1`,
  `terminal_proven true`, `release_count 1`, marker gone; step6 gate takeable again. VRAM
  ~8.7 GiB during, 1,905 / 12,227 MiB after.
- **Two self-disclosed incidents kept as evidence** — (a) the first gate run aborted in step 4
  (`LeaseConflict`) *after* the POST, leaving a genuinely running prompt plus one unresolved
  marker; recovered through the new mechanism itself (`tools/f01_orphan_recovery.py` waited for
  terminal history, reconciled → `completed`, `release_count 1`, raw kept); (b) the first full
  run's step1 returned `validated` in 1.2 s — a ComfyUI cache hit on an identical graph made the
  probe blind; fixed with a fresh seed per run and re-run (`unresolved` after 1.0 s).

```json
{"label": "COMFY-writeset", "count": 21, "present": 21, "tracked": 21,
 "dirty": 0, "bytes_total": 176647}
```

## 3. Snapshot the dirty worktree before resuming the same owner

No commit existed, so the bytes lived only on disk. Walk `git status --porcelain` (both `M` and
`??`), copy each file into a manager-owned snapshot dir, re-hash the copy, assert equality
*before* dispatch:

```python
por = subprocess.run(["git","status","--porcelain"], cwd=wt,
                     capture_output=True, text=True).stdout
for ln in por.splitlines():
    rel = ln[3:].strip(); p = wt / rel
    d = p.read_bytes(); h = sha256(d)
    dest = snap / rel; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(d)
    assert sha256(dest.read_bytes()) == h          # snapshot_match
```

Result: **9 files, 9/9 hash-match**, 8 `M` + 1 `??`
(`__init__.py` 36L, `adapter.py` 739L, `contract.py` 136L, `errors.py` 222L, `gpugate.py` 263L,
`lease.py` 442L, `tests/fake_transport.py` 267L, `tests/test_real_server.py` 299L,
`?? tests/test_reservation.py` 339L). Manifest at
`manager/guard/wave2/comfy-r6-dirty-snapshot.json`. The same treatment was applied to the
VIDEO14B lane (`manager/snapshots/video14b-untracked/`, 5 files, 5/5 match).

The untracked test file is the one that exists nowhere else — it is the file a crash would have
cost, and it was also the file that had never executed.

## 4. The continuation packet order that prevents a second stranding

`MF-V1-COMFY-continuation-06.md` (7.0 KB) was written with an explicit four-part order:

- **A** (highest priority) start the engine with the committed tool, verify the epoch
  `instance_id` actually changed, run the never-executed case
  `test_real_unresolved_reservation_blocks_caller2_then_releases_once` plus the rest of
  `tests/test_real_server.py`, keep the exact command + output in `raw/micro_tests.txt`, re-run
  the offline suite on the final state.
- **B** write the missing evidence set: `REPORT.md` (F01 result first: `original_gate_held
  false→true`, `lease_still_exists false→true`, `reservation_on_disk false→true`,
  `second_stage_gate_acquired true→false`), `raw/gate_matrix.json` with 100 % of rows
  dispositioned, `raw/guard_after.json` with before/after sha256+lines, `HANDOFF.md` for the
  downstream video lane (module paths, entry points, required arguments, how a second caller
  uses gate/lease/reservation), and `MODEL_CAPABILITIES.diff.md` splitting four categories:
  *missing artifact* / *missing node* / *measured OOM* / *vendor claim*.
- **C** commit locally on `codex/mf-reskin-v1-comfy`, allowlist
  `experiments/mf_reskin_v1/comfy/**`, parent `9e57f3e` intact, no push.
- **D** stop the server and prove it: port 8199 closed, VRAM back to ~1.9 GiB, no listener, and
  no collateral `python.exe` killed.

The packet also fixed the language drift at the boundary: worker output may be English, but the
manager's report to the user follows §21 (all-Vietnamese, status-first, anchored ETA).

## 5. Measured cap ≠ documented cap

| lane | `tool_call_count` at stop | packet assumed |
|---|---|---|
| MF-V1-COMFY R6 | **110** | ~90 |
| MF-V1-VIDEO14B R1 | **122** | ~90 |

Both stopped mid-gate. Continuation sizing therefore comes from the observed count
(`SELECT tool_call_count … FROM sessions`), not from the number written in the packet header,
and every packet for a multi-stage task carries the A→D ordering so a cap landing anywhere still
leaves the work captured.

## 6. Download manifest discipline from the VIDEO14B round

The lane fetched **~71 GB across 11 model files** (`diffusion_models` 52 GB: `wan_animate_2_int8_convrot`,
`wan2.1_vace_14B_fp16`, `wan2.1_vace_1.3B_fp16`; `text_encoders` 17 GB: `umt5_xxl_fp16` +
`umt5_xxl_fp8_e4m3fn_scaled`; `clip_vision` 1.2 GB; `loras` 704 MB × 3; `vae` 485 MB × 2) —
and its own honest gap list was the right starting point for the continuation:

```
1. DOWNLOAD_MANIFEST.json — chưa chạy sha256 thật; 2 LoRA CausVid còn dở và repo không license.
…
5. Runtime chưa GPU-ready: đang là torch CPU-only ⇒ cần cài wheel CUDA (có sm_120)
```

Manager rules encoded in `MF-V1-VIDEO14B-continuation-01.md`:

- every file gets URL + revision/commit + license + bytes + **actual on-disk sha256**; a file
  without a hash is `UNVALIDATED`, never "downloaded";
- the license-unclear / incomplete LoRAs are **excluded from the run configuration**, recorded
  as `license_unclear` + `excluded_from_run` in the manifest *and* in the workflow delta, and
  must not be referenced by the run graph — evidence is kept, nothing is deleted;
- CUDA wheel install is authorised **into the task-local venv only**, with the wheel
  source/version verified first, the capability proved by `torch.__version__`,
  `torch.version.cuda`, `torch.cuda.get_arch_list()` containing **sm_120**, and
  `torch.cuda.is_available()` true — and with model load / inference still forbidden;
- disk accounting by `df -h /c` deltas (476 GB → 399 GB free ⇒ ~77 GB fetched) because `du -sh`
  over the model tree hung past the foreground tool timeout (see §22 of the umbrella).

Artifacts the lane had already produced and that the Manager credited as accepted, so the
continuation would not redo them: `VERIFY_UPSTREAM.json` (20,645 B), `RUNTIME_PIN.json`
(9,035 B), `BOOK_WINDOW.json` (14,083 B), `MEMORY_PLAN.json` (13,656 B),
`REFERENCE_PLAN.json` (12,290 B), three verbatim official workflows, node inventories
(`ComfyUI 306af3a` and pinned `v0.37.0`), and `mf_animate2_book4s.json`.

## 7. Reusable recipe

```bash
# 1. liveness + real tool budget (read-only DB)
python scripts/worker_liveness.py --recent-minutes 120
# 2. the lane's dirty bytes, snapshotted and hash-verified before any resume
python scripts/capture_writeset.py <label> <listing.txt> <out.json> \
  --cwd <worktree> --snapshot-root <evidence>/manager/snapshots/<lane>
# 3. the lane's own decisive suite, in its own worktree
cd <worktree> && python -m pytest tests/ -q -p no:cacheprovider
# 4. write the continuation with the fixed order A(run unrun tests) → B(evidence) →
#    C(commit, parent intact) → D(stop the server and prove it)
```

`scripts/capture_writeset.py` covers the listing-driven form; for the cap case the listing is
simply `git status --porcelain | cut -c4-` (both `M` and `??` entries), and the assertion that
matters is `snapshot_sha256 == source_sha256` per file before dispatch.
