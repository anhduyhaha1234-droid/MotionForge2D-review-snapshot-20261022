# MF-V1-COMFY — read-only proof, orphan release, per-hash pinning (2026-09-17)

Worked example behind SKILL.md §16. Lane: `MF-V1-COMFY` (isolated ComfyUI stage
adapter + real engine proof on a task-local runtime, RTX 5070 12,227 MiB).
The lane submitted a strong round-1 packet; two defects survived it and both were
found only by looking at disk truth.

## What the lane got right (verified, not taken on trust)

| Worker claim | Manager verification | Result |
|---|---|---|
| commit `9cde2cea…b3d8d6e0` on its own branch | `git rev-parse HEAD` | MATCH |
| commit touches only its allowlist | `git show --stat` = 17 files, all under `experiments/mf_reskin_v1/comfy/**` | PASS |
| not pushed | `git log origin/<branch>` → `ambiguous argument … unknown revision` | PASS |
| no cache committed | `git show --name-only \| grep -c 'pyc\|pycache'` = 0 | PASS |
| 68 tests pass, 0 skipped | **re-ran with the lane's own venv** | `68 passed, 1 warning in 9.06s` |
| real SDXL render, artifact sha `9e885a9e…cb61` | recomputed sha256 of the PNG on disk | MATCH |
| guard `total_drift = 0` | read its verify report | ACCEPTED |

Cheap allowlist proof worth reusing:

```bash
git show --name-only --pretty=format:"" HEAD | grep -vc '^experiments/mf_reskin_v1/<task>/'
# 0 == every committed path is inside the allowlist
```

## Defect 1 — a "pinned" registry that pinned only SOME hashes

`ENGINE_HANDOFF.json` and `MODEL_CAPABILITIES.json` were submitted as the pinning
evidence, and both *look* pinned. Field-by-field they were not:

```
pins.workflow_sha256        = 36d08f5b…4a91   ✅
pins.node_inventory_sha256  = 52674207…f745   ✅
pins.model_hashes           = null            ❌
checkpoint_sha256 (all 7 registry rows) = None ❌
```

The checkpoint was present and identifiable on disk
(`Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`, 7,105,348,188 B). The
Manager hashed it independently (`c9e3e68f…8bca`) so the correction packet could
state the expected value rather than just the requirement. The lane recomputed it
with its own command and landed **the same hex** — that agreement is the actual
verification, not the field being non-null.

Why it mattered: this hash is the model component of the per-shot cache key in the
wave's streaming plan (source SHA + shot/PTS + masks/tracks + stylepack +
workflow/node/model versions + params/seed). A silently swappable checkpoint
invalidates cache correctness later.

Lesson: grep the individual hash fields. `model_hashes = None` next to two filled
siblings is invisible to any "has it got hashes?" check.

## Defect 2 — the lane's server outlived the lane and held the GPU

After the process exited (receipt `exit_code: 0`, duration 2682 s):

- `curl -s -m 4 http://127.0.0.1:8199/system_stats` → still answering
- `nvidia-smi --query-gpu=memory.used --format=csv,noheader` → **7,452 MiB of
  12,227 MiB at 0 % utilisation**, no worker alive

On a single-GPU wave with an explicit "one heavy GPU stage at a time" rule, that is
a blocker for the next lane, so it went into the correction packet as a defect with
a required fix (clean shutdown + before/after `nvidia-smi` + port no longer
answering + shutdown step added to the runtime runbook).

Fix verified: port down, **7,458 MiB → 628 MiB**.

**Cleanup rule:** kill only the exact PID tree the lane owns. Never
`killall`/`pkill python` — the orchestrating agent is itself a Python process
(a Hermes host), so a broad pattern kill takes down the manager.

## Read-only claim over a USER-OWNED install — the decisive checks

The lane was authorized to use the user's own ComfyUI at
`C:\Users\Admin\.gemini\antigravity\scratch\ComfyUI` (71 GB of models) **read-only**.
Verification, all four checks measured:

1. `git rev-parse HEAD` in that tree → unchanged `306af3a8771a8232d26bd20acbfc6b07f862ad2b`
2. `git status --porcelain` → only `?? my_workflows/` and `?? run_comfyui.bat`
3. `find <tree> -type f -newermt "-60 minutes"` → exactly **one** hit: `.git/index`
4. `find <tree> -type f -not -path "*/.git/*" -newermt "-3 hours"` → **0 files**;
   `find <tree>/models -type f -newermt "-3 hours"` → **0 files**

Two traps this closes:

- **`.git/index` is a false positive.** A worker (or the Manager) running
  `git status` refreshes the index stat-cache and moves its mtime. It shows up in
  every `-newermt` sweep. Exclude it, and state explicitly that it was excluded —
  otherwise the reviewer sees a touched path and assumes a write.
- **Dirty entries must be dated before they are blamed.** `?? my_workflows/` and
  `?? run_comfyui.bat` carry **July 2026** mtimes — months before a September
  dispatch — so they are pre-existing user content, not lane artifacts. A name-only
  read of `git status` would have produced a false scope-breach finding.

Report the outcome as counts: "0 tracked files modified, 0 files written in 3 h
(excluding `.git`), 0 model files written" — not as "looks read-only".

## How the two defects were closed

The lane's round 1 was **accepted** (its work was real and its safety behaviour
correct), and a single bounded continuation was dispatched on the **same** session
id, scoped to exactly: (a) fill the model hash in both files with a self-computed
value, (b) shut down its own server with before/after GPU evidence, (c) re-run the
write-set guard, (d) refresh docs/ledger so they do not contradict the artifacts,
(e) local commit, no push. Explicitly out of scope: re-downloading, new inference
runs, new engine proofs, licence acceptance, and the HunyuanCustom/Van-VACE route
(weights absent — that is a user decision, not the worker's).

The same continuation also carried the Manager-verified verdict on round 1 with an
explicit "these claims HELD" table, so the lane spent its budget on the two
remaining items instead of re-proving its prior work. Budget note: the run is
bounded (see `background-worker-orchestration` § the iteration cap), so a
continuation must fit the *remainder* only.
