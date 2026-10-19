# Post-export verification of a delivered clip (measured 2026-09-22, RTX 5070 12 GB)

Phase: **after** the render succeeded and the export exists. This is the pass the manager runs
itself before the clip is offered to a human reviewer, and the values below are what a CORRECT
deliverable actually looks like on this class of job (Wan2.1-VACE 14B fp16, source-conditioned
4 s window, 30 fps, 640×360 source).

## 1. Identify the three artifacts before measuring anything

| Artifact | Role | sha256 | Shape |
|---|---|---|---|
| `raw_…_121f.mp4` | engine output, padding included | `0630c87d75b9afd7a9d762949ddd68987ec010dc88be90610e33219e93cb1725` | 121 f, 4.033333 s |
| `final_…_4s.mp4` | export = deliverable | `ca42806b6ec5647f2ac1bf8a555c25fce819a44a27fbb30058a56b39a5471a88` (163,391 B) | 120 f, 4.000000 s |
| `media/superseded_r3/final_….r3.mp4` | earlier WRONG export, kept as evidence | `06e6145979abb889568c78d4113707a365caa61a1ffc93be63e90a549d638e05` | 120 f, but audio 9.241542 s |

Never overwrite a superseded export: the old bytes are how a reviewer sees what changed.
`ffprobe -show_format -show_streams` and read the fields out with a `grep -E "^(index|codec_name|
codec_type|start_time|duration|nb_frames|time_base|sample_rate|channels)="` filter, per stream.

## 2. The five measurements that decide the clip

1. **Video stream:** `h264`, 120 frames, `r_frame_rate=30/1`, `time_base=1/15360`,
   `duration=4.000000`, **`start_time=0.000000`** (the export normalised only the container),
   640×368, `nb_read_packets == nb_frames == 120`.
2. **Presentation vs packet order.** `ffprobe -select_streams v:0 -show_entries
   packet=pts_time` returns decode order (`0.000000, 0.133333, 0.066667, …`), i.e. non-monotonic
   on a B-frame stream. Presentation pts are `0, 512, 1024, … 60928` with a single delta
   `{512}`. Assert CFR on the presentation list — the packet list yields a false failure (this
   is exactly what the evaluator's `A_pts_audit` block had to separate).
3. **Audio window:** `aac`, 44100, 2 ch, `start_time=0`, `nb_read_packets=216`,
   `duration=4.001995`. Verify the *content*, not just the length: decode both streams to raw
   PCM and compare byte-for-byte.
   ```
   ffmpeg -v error -y -i <final>.mp4        -map 0:a:0 -f s16le -acodec pcm_s16le cand.pcm
   ffmpeg -v error -y -ss 55.000 -t 4.001995 -i <film>.mp4 -map 0:a:0 -f s16le -acodec pcm_s16le src.pcm
   ```
   then compare sample-by-sample in Python (`array('h')`). Correct result measured:
   **352,968 samples compared, 0 mismatches, MAE 0.0, max abs diff 0, sha256 identical**
   (`af876599…`) on both sides. Any non-zero MAE means the window (or the offset) is wrong.
   Decode the source with the SAME duration as the candidate, not the nominal 4.000 s, or the
   trailing block reads as a mismatch.
4. **Geometry against the SOURCE, in the same command.** Source window 640×360, candidate
   640×368 → **+8 px, 2.2222 % vertical**. This must be a FAIL row. The owner's own gate had
   marked it PASS because 368 was its declared expectation — the expectation came from the
   candidate, so the check could not fail.
5. **Frame map vs pixels.** The map (`out frame i ↔ film frame 1650+i`) was scored by per-frame
   MAE argmin over offsets −3…+3: histogram `{-3:56, -2:33, -1:7, 0:8, 1:6, 2:4, 3:6}`, only
   **8/120** at offset 0, `min_advantage_of_offset0 = −0.0537`, `median_advantage = −0.0006`,
   median MAE at offset 0 ≈ 75.29. Conclusion recorded: **supports but does not prove** — the
   derivation (driving-clip order + padding removal) is the authority, not the metric.

## 3. Gate table shape to demand

30 rows, every row dispositioned: **20 PASS / 3 FAIL / 7 `NOT_REVIEWED`**. The three FAILs are
the raw render's `pts.contract` / `pts.cfr` / `pts.last_frame` (kept, not relabelled); the seven
`NOT_REVIEWED` are the semantic rows (character, hands, grip, props+background, second person,
identity, blur/flicker) that only a human can answer. Overall label
`TECHNICAL_PARTIAL_WITH_DISCLOSED_PTS_LIMITATION` — never `TECHNICAL_PASS`, and no
`QUALITY_ACCEPTED` on a route without vision.

## 4. Resource numbers to keep next to the clip

20 sampler steps @ ~56.5 s/it, wall **1,170.705 s for 4 s** (≈293 s render per 1 s of video);
peak ~9,176–9,264 / 12,227 MiB; model `33,068 MB Staged` via dynamic VRAM loading with the
server process holding ~30 GB RSS; GPU 100 %. The 4B image anchor earlier peaked **11,590 /
12,227 MiB (94.8 %)** — a warning that the card is at its ceiling, so unload it before any video
run. Quote throughput only as seconds-of-render per second-of-ACCEPTED-video; at this rate 12 s
≈ 1 h and 28 s ≈ 2.3 h of GPU before retries.
