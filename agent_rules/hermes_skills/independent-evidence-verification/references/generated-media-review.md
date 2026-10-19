# Reviewing generated media artefacts before authorising the next generation

Measured 2026-09-26 (MotionForge2D round: a GPU lane produced still "anchors" for three shots under a budget of
"≤3 initial + ≤1 diagnosed correction", then asked the Manager to decide the next step). The Manager review below is
what turned a plausible-looking deliverable into a ruled outcome.

## 1. Load the pixels — a path is not a review

* Load every contact sheet / frame with **native image input**; record each file's sha256 and **how many panels/frames
  you covered**.
* State coverage explicitly ("2 sheets / 13 panels; no video exists yet") so a still-image review is never read as a
  clip review, and a partial look is never reported as the whole.

## 2. Ask the second question: can the INPUTS even carry the property?

Output-vs-source comparison is only half the job. Ask whether the supplied references can *encode* what is being demanded.

Measured: three anchor references were **flat silhouettes** (no face, no clothing, no texture). Identity transfer is
impossible from such inputs — no amount of re-rendering or re-prompting can add a property the references do not contain.
The honest deliverable there was a **typed failure**, not another generation.

If the inputs cannot carry the property, write that in the review and treat "generate more attempts" as waste.

## 3. Rule from documents already agreed; route definition questions upward

* Use the definitions already in force — e.g. *shot ids are not character ids*; prop/document shots are judged on prop
  state, layout and occlusion; identity/appearance stability is judged **only where people appear**.
* Apply them; **do not invent policy**. A genuine acceptance-definition question (here: how to source identity references
  for shots containing people when the library holds none) is **routed to the reviewer** with the pixel paths, the SHAs and
  the typed codes — the Manager records it, it does not decide the product definition unilaterally.
* Never accept a substitute artefact, a relabelled input, or a lowered bar in the meantime.

## 4. Audit the generation budget as a count, not a claim

* Require the lane to print the **actual generation count** with per-attempt output sha256 + seed + model identity, so a
  budget like "≤3 + ≤1" is checkable rather than asserted.
* A defect that persists **after the one allowed correction** is a **typed failure** (record the code verbatim) — not
  permission to keep sampling. Restate the prohibition explicitly in the closeout packet: no seed sweep, no silent extra
  attempts, no "one more try".

## 5. Propagate typed failures into the dependent gate as a RULE outcome

When the gate text says *"anchor bad / role missing ⇒ skip with typed failure"*, then the dependent run **and anything
conditional on it** become `NOT_RUN` **by rule**. Record the exact reason and say plainly that the `NOT_RUN` is
rule-mandated — otherwise it surfaces in the next review as an "avoidable NOT_RUN" and invites a second, pointless grant.

## 6. Close the GPU/lease side in the same packet

The closeout that follows such a ruling must also prove the resource is clean: engine stopped, port closed, no listener,
VRAM back to baseline, pids gone — plus the generation census from §4. A typed failure is still a resource event.
