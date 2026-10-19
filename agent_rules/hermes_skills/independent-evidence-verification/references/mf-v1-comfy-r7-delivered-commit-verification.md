# Worked example — verifying a round that landed a commit (MF-V1-COMFY R7, 2026-09-22)

Companion to SKILL.md §24. The lane was a resumed continuation (§23) that had been ordered to
close an evidence set, run a never-executed test, correct a capability registry, commit, and prove
shutdown. It reported `TASK_SUBMITTED`. Everything below is the manager-side verification that
turned that report into verified facts — or into named residue.

## 0. The delivery claim

| field | value |
|---|---|
| task | MF-V1-COMFY continuation-06 (round 7) |
| session lineage | `20260917_212227_80336a` (R5, 52-byte connection-error log) → `20260922_104627_73f18d` (R6, cap) → `20260922_112639_f9bd0a` (R7) |
| receipt | exit **0**, duration **1616.68 s**, packet sha256 `AFE63165…`, model `ocg/deepseek-v4.1-flash` |
| commit | `cc3222b1bed6680480ab6d63fb869b02d749259b` |
| parent | `9e57f3ee11f2f299c0fc221cbc6c944dfd860185` (intact) |
| diffstat | 9 files, **+1173 / −35**, all under `experiments/mf_reskin_v1/comfy/**` |
| evidence | `COMFY/` 66 files — REPORT.md 11,980 B, HANDOFF.md 9,790 B, MODEL_CAPABILITIES.diff.md 11,966 B, raw/gate_matrix.json 19,020 B (40 rows), raw/guard_after.json 13,467 B, raw/micro_tests.txt 10,958 B, raw/comfy_shutdown.json 11,604 B |

## 1. The five checks, in the order they were run

### 1.1 Commit trio + allowlist

```
git log --oneline -4 | cat        → cc3222b … / 9e57f3e … / 449de4d … / f61a3bf …
git rev-parse HEAD^               → 9e57f3ee11f2f299c0fc221cbc6c944dfd860185   (declared parent, intact)
git status --porcelain | wc -l    → 0
git show --stat --oneline HEAD    → 9 paths, every one inside the task write-set
git rev-parse --abbrev-ref --symbolic-full-name @{u}
                                  → fatal: no upstream configured for branch 'codex/mf-reskin-v1-comfy'
```

The `+1173/−35` matters as much as the paths: every changed file **grew** (adapter 442→739 lines,
lease 208→442, gpugate 140→263, `__init__` 23→36, contract 132→136, errors 196→222,
`fake_transport` 236→267, `test_real_server` 231→302, plus new `test_reservation.py` 339) — no
destructive shrink anywhere, which is the §8 red this check exists to catch.

### 1.2 Scoped lint, and the residue by name

```
python -m ruff check --select F mf_comfy/ tests/            → Found 4 errors
python -m ruff check --select F --output-format concise <the 9 committed files>
                                                            → All checks passed!
```

The 4 residual findings, each named with its file and proved outside the diff:

| finding | file | in the commit? |
|---|---|---|
| F401 `pathlib.Path` imported but unused | `mf_comfy/pinning.py:11:21` | no |
| F841 local `sel` assigned but never used | `mf_comfy/reskin.py:752:5` | no |
| F401 `fake_transport.CKPT` imported but unused | `tests/test_adapter_failures.py:12:28` | no |
| F401 `pathlib.Path` imported but unused | `tests/test_units.py:7:21` | no |

Lesson: a package-wide `ruff` count on a live worktree is NOT the round's lint verdict. Pass the
committed file list; attribute anything left by file name.

### 1.3 The claim matrix (40 rows, 0 undispositioned)

```
{python -c json.load(): Counter over rows[].disposition}
→ Counter({'pass': 35, 'not-applicable': 4, 'fail': 1})
completeness: {"rows_total": 40, "pass": 35, "fail": 1, "not-applicable": 4,
               "rows_undispositioned": 0, "counts_verified_by": "…recounted after writing…"}
```

The four `not-applicable` rows all carry a reason that makes them auditable:

- `E5` engine-stop-requested-twice — "Not exercised in round 7: the second invocation would have
  overwritten the round-7 record with an ALREADY_STOPPED report… The idempotent path exists in
  tools/stop_comfy.py (lines 221-233) but is **UNPROVEN** this round — carried as an open item, not
  claimed."
- `S7` / `S8` adapter state machine — "the adapter can only ever reach `validated`; authority is
  MotionForge / S12 publication, outside this task."
- `V1` ComfyUI boot — an OBSERVED defect, deliberately not a gate: `Failed to initialize database …
  unable to open database file` at boot, while `/prompt`, `/history`, `/queue`, `/object_info`,
  `/interrupt` all worked. Recorded with the honest scope limit: "user/asset persistence is NOT
  available on this engine."

The single `fail` row is the disclosed self-inflicted incident:

> `V3` round-6 shutdown record / expected "preserved" / **fail** — "I invoked tools/stop_comfy.py
> with `--help` expecting a usage message, but the tool has no argparse and executed the shutdown
> immediately, overwriting the round-6 shutdown record (raw/comfy_shutdown.json +
> raw/161_shutdown_*.txt). The round-7 record it wrote is complete and identity-verified, but the
> round-6 bytes are not recoverable byte-exactly. Recorded here as fail rather than papered over."

Manager-side confirmation: the surviving `raw/comfy_shutdown.json` was read field by field and is
internally consistent; no reconstructed prior-round bytes were written. The generalisable trap for
the human/in-house tooling layer: **a script with no `argparse` runs on any argv, including
`--help`** — read the source (`grep -n 'argparse\|sys.argv' <file>`) before probing an unfamiliar
helper with a flag.

### 1.4 Suite re-run in both modes

```
python -m pytest tests/ -q -p no:cacheprovider     (engine down)  → 114 passed, 10 skipped in 4.33s
```

(Lane, engine up: `124 passed, 0 skips`.) Skips are named per node, so the engine-down run is
evidence for 114 only. Also verified from the lane's own raw: `test_real_server.py` 10 passed
(11.12 s), real inference timing 0.156 / 0.016 / 2.078 / 0.016 s (total 2.297 s), peak VRAM
**8,954 MiB**, artifact sha256 `99d25eaa…`, 284,723 B. The never-executed test from the prior round
(`test_real_unresolved_reservation_blocks_caller2_then_releases_once`) now passes in 2.39 s.

### 1.5 Shutdown receipt, field by field

| field | value |
|---|---|
| verdict | `SHUTDOWN_CONFIRMED` (a label — not the evidence) |
| `listener_pids_after` | `[]` |
| `tree_kill_used` | `false` |
| `no_collateral_python_killed` | true (pids removed exactly `[14340, 32060]`) |
| port 8199 | closed (`connect_ex 10061`) |
| VRAM | 8,823 → 2,208 (`/free` HTTP 200) → 2,004 → 1,931 MiB idle of 12,227 |
| orchestrator process check | `hermes desktop` (14872) and `hermes serve` (29648) still alive |
| unresolved reservations on disk | zero (only `closed/` receipts) |

## 2. F06 — the capability-registry re-classification (reusable shape)

Every previously merged engine row split into four categories, each carrying only held evidence:

| row (as merged) | missing artifact | missing node | measured OOM | vendor/stock claim | label after |
|---|---|---|---|---|---|
| `comfyui-local-sdxl-t2i` | no (7,105,348,188 B, sha `c9e3e68f…`) | no | no | n/a | **`RUNNABLE_LOCAL`** (measured; not `QUALITY_ACCEPTED`) |
| `hunyuanvideo15-t2v-i2v` | **yes** | no (7 Hunyuan-1.5 classes present) | no | yes — 31.02 GiB T2V / 4.70 GiB VAE upstream | `unavailable` |
| `hunyuan-custom-video-editing` | **yes** | **yes** (no editing class; the 3 video+mask nodes are Wan-family) | no | yes — 22.83 GiB editing fp8 | `unavailable` |
| `wan-vace-masked-video-edit` | **yes** | no (`WanVaceToVideo` present) | no | yes — 1.3B named as fallback, never fetched | `unavailable` |
| `omniweaving-editing` | **yes** | **yes** | no | yes — upstream example is an 8-GPU config | `unavailable` |
| `native-source-propagation` | no (loads no checkpoint by design) | no (not a Comfy node route) | no | n/a | `not_a_comfy_engine` |
| `reference-store-14b-video-models` | no (UNets present, read-only) | no | no | yes — stage cost quoted, never run | `unmeasured` |

The file states outright: "*No row in this file qualifies*" as measured OOM. That sentence is the
standard to demand — a capability table that cannot distinguish "we don't have it" from "the card
can't fit it" will mislead the next lane exactly where it matters.

Pinned environment for the rows above: ComfyUI **0.28.2**, build
`306af3a8771a8232d26bd20acbfc6b07f862ad2b`, **808** node classes, inventory sha
`52674207e277a8ba881ac39f38df21511a22d2129cbab4c2ef636fc890eef745`, RTX 5070 / 12,227 MiB.

## 3. What the round still left open (passed forward verbatim)

- no video engine on this machine (no Hunyuan/VACE/OmniWeaving weights; no Hunyuan editing node
  class in the pinned build) ⇒ the downstream lane must not read this as a video capability;
- **zero `QUALITY_ACCEPTED`** — no visual review was possible on a text-only route;
- `stop_comfy.py`'s idempotent path unproven this round (matrix row `E5`);
- a pre-existing broken git ref fails auto-repack (the commit itself landed fine);
- prior-round calibration blockers and the un-run 56-anchor batch unchanged.

## 4. The handoff (why you read the file, not the chat)

`COMFY/HANDOFF.md` is the frozen interface for the next task and warns in bold that
`stop_comfy.py` takes no arguments and runs immediately — the same trap that produced the `fail`
row above, now encoded where the next lane will actually hit it. It pins the commit, the sys.path
entry point (no installed wheel), the runtime paths (epoch, `leases/gpu_stage.lock`,
`reservations/` + `closed/` + `quarantine/`), the only checkpoint on disk, and the engine
lifecycle with its version pins.
