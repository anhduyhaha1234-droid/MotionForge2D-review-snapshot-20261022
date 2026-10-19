# Verifying media fidelity and container-metadata claims

Measured 2026-09-24, correction round where a reviewer found that an export **dropped the source's
colour metadata** while the lane was publishing a broad "zero pixel loss" claim. The lane's fix was
correct and the Manager closed the row **from its own measurements**, not from the lane's report.
That is the point of this file: a fidelity claim is verified by probing the container and by a
two-sided tag test, not by comparing decoded planes alone.

## 1. Pixel equality is NOT fidelity — the tags are a separate claim

The reviewer's measurement, which the Manager later reproduced in kind:

| layer | result |
|---|---|
| native YUV after crop, frame selection 0..119 | **equal** → a pixel-compare PASS |
| RGB decoded with the candidate's own (missing) tags vs the raw | **differed** — MAE mean **2.1182**, max **18** |
| RGB decoded with the raw's tags forced onto the candidate | **identical to raw** |

So a decode-compare can pass while the delivered artifact is visually wrong for any consumer that
honours tags. Two consequences for verification:

* A fidelity row needs **both** a pixel/plane comparison **and** a container-metadata comparison.
* When the two disagree, the *metadata* is the finding, and "zero pixel loss" must be narrowed to the
  layer that was actually measured (here: planes, not rendered colour).

## 2. The 4-file tag matrix (the check that closes the row)

Probe every side of the claim — fixed artifact, the artifact it replaces, the reference, and a
deliberately stripped control:

```bash
probe() { ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,color_range,color_space,color_primaries,color_transfer,pix_fmt \
  -of default=noprint_wrappers=1 "$1" | tr '\n' ' '; echo "  <= $(basename "$1")"; }
```

| file | W×H | range | matrix | primaries | transfer |
|---|---|---|---|---|---|
| raw render (reference) | 640×368 | `tv` | `bt709` | `bt709` | `iec61966-2-1` |
| **fixed candidate** | 640×360 | `tv` ✔ | `bt709` ✔ | `bt709` ✔ | `iec61966-2-1` ✔ |
| tag-stripped sibling (control) | 640×360 | `unknown` | `unknown` | `unknown` | `unknown` |
| superseded pre-fix candidate | 640×360 | `unknown` | `unknown` | `unknown` | `unknown` |

Rules:

1. **Carry the geometry in the same table.** The reference and the candidates here genuinely differed
   (`640×368` raw vs `640×360` cropped/exported). Publishing tags without dimensions is what lets a
   later reader conflate the raw's +8-row stretch defect with a different (correct, cropped) artifact.
2. **The control is what makes it evidence.** A tag-preservation gate whose negative control cannot be
   produced proves nothing; a sibling exported WITH the tags omitted, showing `unknown` on all four
   fields, proves the check can fail. Keep it in the lane's evidence (a `*notags*` sibling is fine —
   it is not a deliverable).
3. Compare the **tuple**, not one field: a file can carry `bt709` primaries and still lose `transfer`.
4. Report "carried N/4 like the reference" rather than "metadata is preserved".

## 3. Pin by digest, never by mtime — a deterministic re-export touches mtime only

A closing run re-ran the export that produces the frozen candidate. The bytes were identical
(`sha256 ee66fe96…`, `1,071,360 B`) but the file's **mtime jumped** (19:22:10 → 20:18:34), and the
freeze **record** beside it was rewritten too (its own sha changed, one field renamed) while still
pinning the same path/sha/bytes.

Rules:

* An evaluator/freeze must key on the **digest**; an mtime-based invalidation would have discarded a
  still-valid evaluation and forced a pointless re-measure.
* When you see a moved mtime, **re-hash before reacting**, then report the precise shape:
  *"record changed, candidate did not — bytes identical, only mtime touched."*
* The same distinction decides "is the freeze still the newest?": check for sibling round
  directories and for artifact classes that merely *look* like freezes (a test-only reference table
  is not a candidate freeze and does not supersede one).
* Ask the evaluator directly which side of the line it falls on (`fresh evaluation needed` vs
  `evaluation stands`) and let it answer from the artifacts — measured here: it answered
  *"stands"* with the sha/bytes/mtime evidence, and did not open new scope.

## 4. Reporting shape

One table (file → dimensions → the tag tuple → match), the control beside it, and a coverage sentence
naming what was **not** judged (no playback, no audio, N frames of M). Then the verdict, in the
reviewer's language: the row is *corrected* only when both the pixel layer and the metadata layer were
measured — otherwise it is evidence-submitted.
