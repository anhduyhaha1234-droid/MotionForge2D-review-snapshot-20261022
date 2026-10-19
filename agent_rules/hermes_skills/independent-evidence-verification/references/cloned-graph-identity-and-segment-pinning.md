# Cloned graphs & assemblies: per-unit identity, per-segment pinning

## One proven graph cloned for N units must swap EVERY per-unit field

A pipeline proven on unit A (BOOK) was cloned to units B/C (TURN/OCC). The positive-prompt text
was silently carried over — all three graphs had the SAME prompt sha (`540d16b7…`) — so B/C
rendered unit A's scene (a person reading a book instead of the certificate sheet) while every
technical gate stayed green: dims 640×368, 120 frames, 30/1 fps, pts monotonic, motion present.

* **Cheap detector:** hash the input text (and other key inputs) of the cloned graphs and ASSERT
  they differ per unit. Add it to the per-unit gate — technical gates cannot see content carry-over.
* **Decisive detector:** view the src-vs-gen preview at frames 0/60/119 with native vision.
  Content defects survive numeric gates; only eyes catch "wrong scene, right resolution".
* Fix cost stays small when the server is warm (~2.6 min/clip) and the delta is ONE variable
  (prompt per-unit; model/LoRA/steps/seed untouched).

## Assemblies must pin per-segment file + sha

When a boundary frame of the final assembly disagreed with the clip preview referenced in the gate
JSON, the assembly could not be attributed to any specific source file — the receipts did not pin
per-segment inputs. The disagreement itself is the finding.

* Rebuild with an explicit `segments[{unit, file, sha256, frames, audio_file, audio_sha}]` table in
  the assembly receipt, and re-run boundary-frame checks (e.g. frames 119/120 and 239/240).
* General rule: any artifact built from multiple pieces should be traceable piece-by-piece by
  hash; "the concat used the right inputs" is a claim, not evidence.

## Manager-side verification pattern that caught this

Worker gate JSON claimed per-shot PASS on technical fields; the Manager's own pass (extract frames
from the final assembly + view the src-vs-gen previews with native image input) caught the content
defect and the segment-attribution gap before the defect reached the demo gate. Budget one visual
check per shot of any delivered video: frame 0 / middle / last, source beside generated.

## See also

- `references/output-geometry-and-source-cut-integrity.md` — before trusting any per-shot gate:
  assert output dims against the SOURCE window (an inherited template's hardcoded resize node
  rendered portrait and center-cropped half the scene); scan each source window for editorial
  cuts with a declared rule and split units at them; prove A/B inertness via decoded-frame diffs,
  never file hashes.
