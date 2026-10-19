# S12-C2 finding loop: source-locked validation vs re-encode pipeline

Real transcript from 2026-09-09 S12-C2 W7 closing waves. The full loop:
verifier discovers a positive-path blocker → route producer → interface-delta
to the validator owner → producer wires the new mode. Model used:
`ocg/deepseek-v4-flash` @ custom (user override; CMC 429 until 09-11T17:23Z).

## 1. Verifier finds the positive path never closes (F11-T06B-01, P1)

T06B (read-only acceptance lane, base = FULL product merged) reported:
- C26 scenario F render GREEN (real 1080p→3840x2160 scale+pad, native 4K
  control, 4:3 letterbox, dims/frames/timing exact) — but POSITIVE PUBLISH
  BLOCKED: `publication._expectation_for` never supplied authority reference
  (sha/digests/audio) → T04A source-locked validator rejects every real job
  (`provenance FAIL, frame_order NOT_MEASURED`) → run lands `failed` retryable.
- C28-F01 (P2): `_expectation_for` never attached an AudioReference.
- C29: hardware MEASURED, clean-VM/human NOT_RUN → beta blocked, never waive.

Discipline: verifier does NOT patch production; it routes back to the exact
owner with a minimal repro and keeps rows honest (`failed`, not waived).

## 2. Producer findfix (T03C owner, publication.py)

`_build_source_reference(manifest, fps_num, fps_den)`:
- probes the CURRENT approved Full Apply artifact (server-derived source_path)
  using T04A helpers: `probe_frame_digests` (per-frame content digests at the
  approved raster), `probe_audio_digest` (→ `AudioReference(mode="transcode")`
  when the artifact has audio; `absent` when silent), fps rational + frame
  count + artifact sha256.
- NEVER reads from the candidate; artifact missing → degrade to fps/sha only
  (NOT_MEASURED/FAIL, no fake PASS).
- New unmocked tests: real 4K source + byte-identical candidate → REAL PASS
  across all probes (publication completes); source-with-audio → av_policy PASS.

## 3. The design conflict: exact digest vs re-encode

After the findfix, the positive path was STILL blocked — and this is the
class-level lesson: **a validator that demands byte-identical frame digests
can never pass a pipeline that re-encodes**. 4K upscale from 320×180 or any
lossy re-render is never byte-identical to the approved artifact, so
`frame_order`/`provenance` FAIL by design on every legitimate job.

The fix is NOT weakening assertions: it is an explicit, measured, fail-closed
tolerance mode added by the VALIDATOR owner:

- `ValidationExpectation.frame_match_mode`: `"exact"` (DEFAULT, fail-closed —
  re-encoded candidates still FAIL unless a consumer opts in) | `"psnr"` with
  `frame_psnr_min_db` set by the consumer per profile (threshold missing →
  FAIL closed). `SourceReference.reference_path` = immutable approved-artifact
  path, used only for psnr (missing → FAIL).
- New helper `probe_frame_psnr(candidate, reference, w, h)` — per-frame PSNR dB
  at the approved raster, presentation order.
- Tamper cases MUST still FAIL under the tolerance (proven with real tests,
  assertions unchanged): reorder B+A FAIL; changed audio FAIL (video PASS but
  remux digest FAIL); timing drift FAIL; wrong reference FAIL; combined FAIL.
  Only legitimate lossy re-encode of the SAME content → PASS.
- `AudioReference` transcode policy: compare presence/mapping/A-V drift only,
  never the digest.

Route shape: the PRODUCER (T03C) proposes the delta but does NOT touch the
validator's file; the VALIDATOR owner (T04A) implements it; then the producer
wires `frame_match_mode` + `frame_psnr_min_db` per profile (psnr for re-encode
profiles, exact for identity-copy) plus optional `expected_sha256`.

## 4. Pitfalls seen on this loop

- **ffmpeg `-shortest` drops the last frame** in remap video+audio fixtures
  (19/20 frames) — remove `-shortest` in changed-audio fixtures so the test
  targets audio content, not trim behavior.
- Regression counts shift after an addendum merge: the producer's lane count
  grows (T03C 30 → 35 → 37) because its branch now carries the validator's
  base tests too; re-state the count per tree in REPORT/evidence.
- The verifier's second-round assert that pinned the OLD fail now PASSES on
  canonical (base includes the producer fix) — expected; the remaining blocker
  moves to the next link in the chain (the unwired mode), keep routing it.

## 5. Next link in the chain: cross-raster PSNR (F11-T06B-02, P1)

The chain did NOT end at wire-psnr. After T03C `04a5036` (wire `frame_match_mode`
psnr + per-profile threshold + expected_sha256) merged and T06B REVERIFY-2 ran:

- **C26 POSITIVE CLOSURE for native-4K SAME-raster**: publish COMPLETED
  (PSNR measured 59–71 dB vs threshold 30), GET result 200 (server-owned
  media_url) + GET media playable. C27 kill/restart → publish completed PASS.
- **New verifier finding F11-T06B-02 (P1)**: upscale 1080p→4K + 4:3 letterbox
  render is real 3840×2160 but publish FAILS `frame_order` because
  `probe_frame_psnr` decoded the REFERENCE at its ORIGINAL raster — a
  cross-raster candidate can never PSNR-match. Verifier keeps the row failed,
  writes an exact repro, does NOT patch production.
- Route to VALIDATOR owner (T04A, `bd5837e`): `probe_frame_psnr(…,
  reference_width, reference_height)` now fits+pads the reference TO THE
  CANDIDATE RASTER before computing dB, using the product letterbox policy
  (`_fit_filter` = `scale force_original_aspect_ratio=decrease` + centered
  black pad, never stretch). Same-raster path unchanged (native 4K PSNR
  59–71 dB preserved). `SourceReference.reference_width/height` are new
  immutable server-owned fields; raster missing or claims wrong → fail-closed
  (no fake PASS). Tamper guards re-proven: reorder cross-raster FAIL,
  audio/drift FAIL, legit upscale 4K + letterbox PASS. 5 new tests
  (upscale letterbox PASS, same-raster PASS no-fit, reorder FAIL,
  wrong-raster-dims FAIL, missing raster FAIL) → 78 passed T04A.

Class-level lesson: **same-raster PSNR is not proof for cross-raster work —
the reference must be normalized (fit+pad per the product's own letterbox
policy) to the candidate raster before frame comparison; never decode the
reference bare and compare.** And each closure round exposes the next link
(reference → psnr mode → producer wiring → cross-raster normalization) —
keep routing verifier findings to the exact owner with minimal repros until
the FULL positive chain closes; a render-green + publish-failed split stays
an open row.

## 6. Pipe-frame-drop on Windows: moving ONE side to a file is not enough

Cross-raster fit+pad (`bd5837e`) was still not closure. T06B REVERIFY-3/4 on
merged canonical (`68f40b3`, later `dfd4fe0`) read **7/30 frames at ~7.6 dB**
for upscale/letterbox — root cause: the pipe-fix (`b6d174c`) only moved the
REFERENCE to a temp raw file; the CANDIDATE still streamed through
`_open_raw_pipe`, and a large scale filter graph on Windows drops rawvideo
stdout-pipe frames (native same-raster 30/30 via pipe is fine; cross-raster
scale is not). This is a media-pipeline failure, NOT a content mismatch —
judging it as "still frame_order" without reading the frame count would have
sent the loop in the wrong direction.

Fix (`probe_frame_psnr`, T04A `83e7714`, 81 passed):
- On the CROSS-RASTER path (reference has a vf filter), decode BOTH candidate
  and reference to mkstemp raw files in %TEMP%
  (`_decode_raw_to_file`, validate `size % frame_size == 0` → fail-closed
  None, delete in finally), read frame-by-frame from disk. No rawvideo pipe
  survives on the scale path.
- Same-raster path keeps the proven pipe (no filter → no drop).
- Tests assert the FULL count (`"30 frames PSNR"`) — a truncated pipe fails
  as frame_count mismatch, never passes as low-PSNR noise.
- Guards unchanged: reorder FAIL, missing-raster FAIL, same-raster 30/30 PASS.

Verifier re-verify-4 (`70cb392`) confirmed the exact next link BEFORE the fix
landed (candidate still piped) — the loop discipline is: re-verify on merged
canonical, read the failing count + root cause, route back with the precise
delta. Validator-branch unit-green is not product-path closure.

## 7. Where the loop stood at session end

Chain merged to canonical `dfd4fe0` (cross-raster `bd5837e` + reference-pipe
`b6d174c`); T04A candidate-pipe `83e7714` committed locally (81 passed);
INT01 merge `83e7714` → prep T06B branch → T06B REVERIFY-5 dispatched (expect
upscale 1080p→4K + 4:3 letterbox publish COMPLETED). Remaining after that:
INT01 final merge → Manager frozen per-dir gate → packet C2 → zero-watcher
state.

Class-level lesson complete: same-raster PSNR ≠ cross-raster proof
(reference must be normalized fit+pad); and on Windows, a scale-heavy
rawvideo PIPE drops frames — decode both sides to temp raw files for any
cross-raster comparison and assert the full frame count, not dB alone.