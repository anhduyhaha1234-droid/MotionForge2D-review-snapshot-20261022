# MotionForge full-delivery takeover (contract active from 2026-09-27/28)

Authority packet root:
`C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-takeover-20260927/`

Read order: `NEXT_HERMES_PROMPT.md` → `EXECUTION_CONTRACT.md` (scope, gates, final deliverable list §9) →
`SESSION_OPENING_PROPOSAL.md` (owner map) → `PRODUCT_AND_COMFY_PLAN.md` (requirements U01–U28 + acceptance) →
`COMFY_UNITS_RESEARCH.md` (scene-unit schema §3, node semantics §5, proof plan P0–P7 §7) →
`TASK_BOARD.md` + `TASKS.json` + one packet per task `tasks/MF-END-xx.md`.

**This contract REPLACES the earlier CPU-only/GPU=0/no-QA/no-INT/no-DEMO limits** for the listed tasks:
GPU is allowed sequentially (1 job at a time), workers may local-commit (no push), QA/INT/DEMO/UI tasks open
after the PROOF_GATE. It does NOT reopen accepted NR05/NR06, nor authorize push or S13 wholesale.

## Delivery shape (3 phases, one contract — do NOT ask the user per job)

* **Phase A (dispatch immediately after preflight):** finish the real corrections owned by the existing
  owner sessions, then prove scene-unit Comfy workflows **P0–P7** in an isolated `RUN/proof` tree.
  PROOF_GATE = ≥1 valid graph/profile per real shot type in the demo + real assembly via Comfy.
* **Phase B (only after PROOF_GATE):** wire the PROVEN graph into the public app via MF-END-01…28
  (28 task IDs / 112 micro-jobs, 14 dependency layers, one NEW session per task). Internal dependency
  authority — the Manager opens waves without asking the user.
* **Phase C:** app vertical slice → stress demo (BOOK/TURN/OCC ≥3 shots ~12 s) → full selected MP4 source →
  second video same cast → batch/reopen → package/S12 gates. Missing clean-Windows/human target does not
  block producing MP4+package; it marks those release gates NOT_RUN honestly.
* Terminal: `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW — NOT_APPROVED / NOT_CLOSED`,
  `QUALITY_ACCEPTED=0` until independent Codex review. Manager never self-approves/closes.

## Resource caps + workspaces

* ≤3 upstream model streams **including the Manager** ⇒ while the Manager is active, ≤2 workers stream;
  stagger 45 s at launch. GPU lease = 1 job at a time; read-only verifiers never run on a tree with a live
  writer; global gates only after all writers are terminal.
* RUN root: `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20260927/<UTC-run-id>` — never overwrite;
  feature-task checkouts under `mf-delivery-20260927/<TaskID>` from the immutable wave base.
* Proof workspace: `RUN/proof/{graphs,tools,inputs,output,evidence}` only; Comfy runtime source + model
  dirs + old inputs are READ-ONLY; launch isolated Comfy servers with RUN-scoped input/output/temp/user/
  cache dirs + a dedicated port, and always capture epoch/pid receipt + shutdown proof.
* Ledger (old manager ledger) stays append-only; snapshot the WHOLE current prefix (not just the historical
  36 rows) before appending dispatch rows.

## P0/P1 measured facts (2026-09-27, runtime video14b HEAD 73c9bad4, ComfyUI 0.37.0)

* Isolated CPU server on port 8321: `/object_info` = 960 nodes (sha 80850af2…); clean shutdown verified.
* **NOT registered in this runtime:** `Flux2KleinEditModel`, `Flux2KleinEditApply`, `TrackToMask`,
  `Sam2Segmentation`. **Weights present:** WanAnimate2/WanVace/WanImageToVideo/WanFirstLastFrame; video +
  image compositing nodes. **Weights MISSING:** sam3, sam2, checkpoints (SCAIL nodes exist, no weights).
* Anchor image path that already RAN (R27-I1, reuse it): `UNETLoader` + `CLIPLoader` + `VAELoader` +
  `EmptyFlux2LatentImage` + `ReferenceLatent`×N + `ImageScaleToTotalPixels` + `ResizeImageMaskNode` +
  `SamplerCustomAdvanced`/`KSamplerSelect`/`Flux2Scheduler`/`RandomNoise`/`CFGGuider` + `VAEDecode` + `SaveImage`.
* WanAnimate2ToVideo consumes `reference_image[:1]` only (no per-role mask input) ⇒ primary reference must be
  a composed full-scene anchor; SCAIL is the correspondence candidate but its palette auto-sorts (needs
  explicit role→palette mapping + `sort_by=none`); continuation = 1 frame (Wan) vs 5 frames (SCAIL).

## Owner map at contract start (proven via RO state.db)

Manager `20260927_121424_09f32c` (chat bridge; canonical 7a53d1 evidence-only) ·
COMFY `20260927_165642_819e25` (R28 commit `70f7180`, Manager re-ran: 23 passed) ·
QC `20260927_165735_03675b` · VIDEO `20260927_165838_1cbd42` (R28 commit `cbd0216`; owns proof P0–P7) ·
CONTRACT `20260927_135600_94d1d5` · BENCH `20260926_173425_c114dd` · QA `20260926_173510_fae464` ·
INT `20260926_180042_1990da` · DEMO `20260926_181543_020847`.

Launch shape used for this delivery: `hermes chat -q <packet> --provider custom -m ocg/deepseek-v4.1-flash
--pass-session-id --no-restore-cwd --max-turns 160` (keeps the same session id on resume — see
`independent-evidence-verification/references/packet-path-drift-and-relaunch.md`).
