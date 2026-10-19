# Auditing generated-media claims before a gate (video/image, GPU workers)

Measured on a MotionForge delivery (2026-09-27/28): three GPU-generated clips + an assembly, each with a
JSON gate that said PASS, still contained content defects. This is the Manager's pixel-and-measurement
cookbook: the defect classes that survive every *technical* gate, and the cheap checks that catch them.

## 0. Rule: look at real pixels yourself, at checkpoints

Read the actual PNG/MP4 with native vision — never accept a worker's prose description of an image. The
checkpoints that each caught a real defect: anchor vs source frame · A/B of two profiles at the same frame ·
per-segment first/mid/last frames · assembly boundary frames.

Extract frames for viewing without a player:

```
ffmpeg -hide_banner -loglevel error -i clip.mp4 \
  -vf "select='eq(n\,0)+eq(n\,150)+eq(n\,300)'" -vsync 0 -frames:v 3 out_%d.png
```

## 1. Defect classes that pass every technical gate

| Class | How it hides | Cheap check |
|---|---|---|
| **Geometry vs source** | dims gate compares output to the *declared* target, not the source window (portrait 480×848 shipped for a 640×360 source) | compare against the SOURCE dims; grep the built graph for hardcoded `width/height/crop` inputs on resize/get-size nodes |
| **Prompt carried across units** | every per-unit graph has the same prompt → each clip renders unit #1's scene; frames/fps/pts all pass | hash/compare prompt strings across the per-unit graphs BEFORE paying for runs (identical prompt sha across 3 graphs was the tell) |
| **Window contains a cut** | a "unit" spans two scenes; the generator anchors on the first and drifts from the source's later content | cut scan with thresholds declared before looking — worked rule: `changed_pixel_delta 32 AND changed_fraction ≥0.50 AND mean_abs_diff ≥12`; split the unit at the cut, each segment gets its own anchor + prompt |
| **Overlay copied from control** | a control/reference-conditioned model reproduced the source's watermark (play button + channel text) while the primary profile did not | corner crops of first/last frames; treat as a delivery blocker, profile-scoped |
| **Event-state mismatch** | object stays in its opening state through the window while the source event map has open/close/swap at frame N | compare the state AT the event frame, not just coverage breadth |
| **Prefix inheritance** | rebuilt graph kept an inherited SaveVideo prefix → outputs landed in the OLD run dir | re-hash the old dir's files against their recorded shas FIRST, then reconcile with a mapping file — no re-run needed when the prefix doesn't enter the computation |

Node-semantics trap: `crop=disabled` on a resize node STRETCHES (check the node source/tooltip before
"just disabling crop"). Preserve content with aspect-preserving pad (`scale=min()` + centered pad), then
trim the pad rows at assembly. Pad used for conditioning only does not appear as bars in the output — say
so explicitly, or a reviewer will hunt for phantom bars.

## 2. Cost-attribution trap: cold vs warm is up to ~15×

Same graph, same 4 s clip on one host: **2,394 s cold** (first run after a server start) vs **155 s warm**
= 38.7 s/output-s warm vs ~597 cold. A big speed delta after a config change (aspect fix, cache toggle) is
*not* evidence the config caused it. Isolate cold/warm before crediting or blaming any change; every fresh
server start pays one cold run. Put warm numbers in ETA math and add one cold-run cost per restart.

Determinism toggles are also evidence: cache on/off and overlap 8↔16 produced **pixel-identical** outputs
(`max_abs 0`, containers differed) — that lets you pick the cheaper setting without re-judging content.

## 3. Claim hygiene for media gates

* Demand **per-segment pins** for assemblies: `{unit, file, sha256, frames, span}` per segment. A segment
  list without spans can hide wrong order/length; expected total frames = sum of spans.
* A `coverage PASS` string is a worker opinion. Pair every PASS with your own look at first/mid/last frames
  vs that segment's OWN source.
* Verify audio with your own ffprobe (stream present, codec, duration). Segment clips may legitimately have
  no audio when audio is muxed at assembly — check the assembly, not the segments.

## 4. Pitfall: preview sheets can disagree with the assembled file

Measured: a lane's per-clip preview sheet showed one content state while the segment inside the assembled
file showed another. When a preview sheet and the shipped artifact disagree, treat both as suspect and
re-extract frames from the exact file+sha you intend to ship. (This is what per-segment pins are for.)

## 5. Smallest-variable repair loop

One variable per round (prompt → split-at-cut → per-segment prompt), each round re-gated. Keep every
superseded assembly on disk with its own pin JSON (v1/v1.1/v1.2/v1.3) so the verify target is explicit and
the supersede trail is auditable. Dispatch the fix to the SAME owner session with the new evidence; never
batch several content fixes into one run — when it fails you won't know which variable did it.
