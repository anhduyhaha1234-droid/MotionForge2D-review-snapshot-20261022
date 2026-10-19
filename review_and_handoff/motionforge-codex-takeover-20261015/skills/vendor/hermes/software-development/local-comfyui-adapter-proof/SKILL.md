---
name: local-comfyui-adapter-proof
description: "Prove a local ComfyUI adapter on Windows + real inference."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [comfyui, adapter, windows, gpu, verification]
    related_skills: [terminal-engineering-discipline, claude-code]
---

# Local ComfyUI adapter + real capability proof (Windows)

Use when a task says "prove ComfyUI capability", "isolated engine adapter", "run a real
light workflow", or asks whether a video model fits a small GPU.

Proven end-to-end on RTX 5070 (12,227 MiB, sm_120), ComfyUI 0.28.2 pinned at
`306af3a8771a8232d26bd20acbfc6b07f862ad2b`, torch 2.11.0+cu128. 68 tests, real SDXL
inference verified from artifact bytes.

## 1. Discover first, assume never

Search more than the obvious places: `~/.gemini/antigravity/scratch/ComfyUI` was the real
install on this machine while `~/ComfyUI`, `C:\ComfyUI`, `~/Documents/ComfyUI`,
`~/Desktop/ComfyUI` and PATH were all empty. Read-only facts worth collecting:
`git rev-parse HEAD`, `comfyui_version.py`, `venv/Scripts/python.exe -V`, and
`python -c "import torch;print(torch.__version__,torch.version.cuda,torch.cuda.get_device_capability(0))"`.
**Never run the user's install in place** — it writes `output/ temp/ user/ __pycache__`.
Build your own copy instead.

## 2. Task-local env (pin everything)

```bash
git clone --no-hardlinks "C:/path/to/user/ComfyUI" "$RT/ComfyUI"
cd "$RT/ComfyUI" && git switch -c pinned 306af3a8771a8232d26bd20acbfc6b07f862ad2b
python -m venv "C:/abs/rt/venv"        # WINDOWS-NATIVE path for the native python!
venv/Scripts/python.exe -m pip install "torch==2.11.0" torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu128
venv/Scripts/python.exe -m pip install -r ComfyUI/requirements.txt
```

Mount the user's model store **read-only** in `ComfyUI/extra_model_paths.yaml` (a second
section) and copy (not download) the one checkpoint the light proof needs.

## 3. Launch on loopback with an instance epoch

Wrapper script that writes `instance_epoch.json` from *inside* the server process
(`instance_id`, `pid`, `launched_at`, `base_url`) then `runpy.run_path(main.py)`. Pass
`--listen 127.0.0.1 --port <p>` plus `--output-directory/--temp-directory/--input-directory/
--user-directory` so every write stays inside your runtime. The epoch + live pid is what
makes restart detection and lease ownership provable.

## 4. Observed real semantics (do not trust docs)

| Situation | Real response |
|---|---|
| unknown node class | 400 `{"error":{"type":"missing_node_type","message":"Node 'X' not found…"}}` |
| missing checkpoint | 400 `node_errors.<id>.errors[0].type == "value_not_in_list"` |
| missing required input | 400 `prompt_outputs_failed_validation` + `required_input_missing` |
| empty graph | 400 `error.type == "prompt_no_outputs"` |
| unknown prompt | `/history/<uuid>` → `{}` (**no proof**, never a success) |
| cancelled prompt | history `status_str:"error"` + an `execution_interrupted` marker → its own typed code |
| `/interrupt` | accepts JSON `{"prompt_id": …}`, 200 `{}` |
| `.partial` files | **do not exist** here: `SaveImage` writes via PIL directly, so a crash leaves a truncated/zero-byte PNG → detect by size + full decode, not by name |

Match both the underscored `error.type` and the spaced human `message` when classifying.

## 5. Adapter invariants reviewers actually check

- one submission per attempt; a second raises typed `BLIND_RESUBMIT_REFUSED`; count it.
- timeout after submit = ambiguous: reconcile via `/queue` + `/history` + epoch; still
  queued ⇒ `unresolved`; epoch gone ⇒ `SERVER_EPOCH_CHANGED`; else `AMBIGUOUS_AFTER_SUBMIT`.
- websocket = progress only; reconnect internally, never resubmit; history is authority.
- re-materialise artifacts inside the stage root, hash + full decode there; reject
  `.partial`, zero-byte, undecodable, wrong server `type`, hash mismatch, path escape
  (absolute / drive / UNC / `..` / symlink).
- `/interrupt` only with an exclusive lease bound to that prompt_id + live pid; a refusal
  must make **zero HTTP calls**.
- one heavy GPU stage at a time via a cross-process byte lock; keep holder info in a
  **sibling file** — a byte-locked file cannot be read by the contender.
- never mutate the submitted graph (FPS/duration/resolution are caller-owned).

## 6. Prove the artifact without vision

The active model may have no vision, so verify the image from bytes:
- `SaveImage` embeds a `prompt` text chunk → proves the file came from this server for
  *your* graph (seed, ckpt, node classes) — the strongest provenance signal.
- compare `std` and mean gradient energy against uniform-noise and blank baselines
  (real render ≈ std 47 vs noise 74, gradient 3.5 vs noise 38).

## 7. Pitfalls that cost real time

1. **MSYS path translation**: passing `/c/Users/...` to a native `.exe` (python, pip,
   pytest) can silently create `C:\c\Users\...`. Pass `C:/Users/...` to native binaries;
   keep `/c/...` for bash builtins only. Same trap inside Python `subprocess.run` — a
   `/c/...` argv[0] fails with `WinError 2`.
2. Wrap every evidence command in a ledger recording argv/cwd/start/end/exit/duration; it
   also catches launch failures that would otherwise look like empty output.
3. `git -C /c/abs` fails in git-bash → `cd` first and use relative paths.
4. `du -sh venv` on Windows can hang for minutes (many small files) — don't run it.
5. Guard scripts must **fail closed**: if a check cannot run (e.g. `git ls-tree` rejects the
   `exclude` pathspec magic), treat it as drift, not clean. Prove sensitivity with a control
   that must differ (an unfiltered digest).
6. An allowlist commit legitimately moves HEAD: compare the content digest of tracked files
   outside the allowlist at base vs head, not just `git status`.
7. **Two fake-transport rigs sharing one transport break the fake clock.** `make_rig`
   re-points `transport.time_advancer` to *its own* clock, so a second rig built on
   `transport=rig.transport` silently steals caller-1's advancer: caller-1's `clock()` never
   moves and its wait loop spins forever (thread never finishes; a `join(20)` burns 20 s and
   the assertion fails for the wrong reason). Save the advancer and restore it
   (`rig.transport.time_advancer = rig.clock.advance`) before releasing a barrier.
8. **A CPU-only real server**: run the FROZEN venv + code read-only with
   `PYTHONDONTWRITEBYTECODE=1`, `CUDA_VISIBLE_DEVICES=` (empty), `--cpu`,
   `--base-directory/--user-directory` into your own dir, port `8300+`, and `cwd` = the
   ComfyUI dir (`main.py` imports `comfy.options` relative to cwd). Prove the frozen tree was
   untouched with a before/after digest over all files except `models/ logs/ output/ temp/`.
   A second process can own the LISTENING socket — verify "listener pid set empty + port
   closed", not just "the pid I spawned is gone".
9. **A model-free workflow must be timed, not assumed slow.** `EmptyImage → 3×ImageScale →
   SaveImage` executed in 0.62 s, so the prompt finished inside a 1 s stage timeout and the
   "unresolved" scenario never formed. Calibrate (24 resamples ≈ 5 s here) and confirm in the
   server log: `grep "Prompt executed in"`.
10. **Required-input drift**: in 0.28.2 `ImageScale` requires `crop` (it is NOT optional), and
   `EmptyImage` requires `color`. Read `/object_info` for the exact required keys before
   submitting; a missing key is a typed 400, not a default.

## 8. Acceptance shape

Keep two clearly separated proof levels: fake-transport tests = adapter contract only; one
real run on the real server with real model inference = engine proof. Report
`unavailable`/`unmeasured` plus the reason for anything not executed — never a pass.
