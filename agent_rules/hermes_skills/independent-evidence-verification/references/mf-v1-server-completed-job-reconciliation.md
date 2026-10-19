# A CLI worker died mid-job; the SERVER had already finished it (2026-09-22)

Session context: correction wave `mf-reskin-correction-20260922/20260922T0955Z`, lane MF-V1-VIDEO14B.
This file records the reconciliation that saved a completed GPU run, the wrong-parent resume slip, the
candidate-collapse proof, and the two independent checks that closed the round.

---

## 1. The cap-ended GPU round, reconciled against the engine

The lane's b1 round exited `RUNNING` at its tool-call cap. Its own report said (correctly) that it had
**not** killed the GPU job, and that an `a4` attempt was "still running". Manager-side reads, taken
~1 minute apart:

```
netstat -ano | grep LISTENING | grep :8310
  TCP 127.0.0.1:8310  LISTENING  20756                     ← engine still up
curl -s http://127.0.0.1:8310/queue   → {"queue_running": [], "queue_pending": []}
curl -s http://127.0.0.1:8310/history → 4 entries, all success, last = 632bbf19-… with 3 outputs
engine log                           → "Prompt executed in 150.04 seconds"
nvidia-smi                           → 4,410 MiB used (model still resident)
```

So the submitted job had **completed server-side** after the wrapper stopped. The engine output dir
already held `animate2_book4s_00003_.mp4` (157,300 B, sha `ebf49f80…`) and `…00004_.mp4` (187,464 B).
The continuation packet was therefore written as **reconcile → export → audio → bundle → shutdown →
commit**, with "do not re-run Animate-2" and "do not start a second engine" as hard rules.

**The run record fields that made reconciliation possible** (`raw/run_b3_book4s_a4/run_record.json`):

| Field | Value | Why it matters |
|---|---|---|
| `attempt_id` | `waveB-b3-book4s-1A-a4` | binds the attempt to the packet's identity |
| `allowed_types` | `["output"]` | proves the F05 output-contract boundary on a REAL run |
| `graph_sha256` | `f246221a…` | needed to argue "identical re-render" vs "new candidate" |
| `node_inventory_sha256` | `d9e8e25a…` | engine build identity |
| `model_pins` | 5 hashes incl. `wan_animate_2_int8_convrot…0580ecdd…` | matched-set provenance |
| `service_epoch` | `instance_id 96ab17eb…`, `pid 20756`, `port 8310` | lets the next round reuse instead of restart |

---

## 2. Wrong-parent `--resume` — one parallel writer, killed pre-write

Dispatching the b3 closeout, the Manager resumed `20260922_174854_0606cc` (the **c2** session) while the
actual latest member of the lineage was `20260922_183517_69741c` (the **b2** session). The launcher
minted `20260922_190023_1dca48`, whose first `user` message was the correct packet — so the packet text
alone would not have caught it. The state store did:

```
20260922_190023_1dca48  msgs=10  tools=6   started 12:00:25Z  ended NULL   ← wrong parent
```

Killed immediately; verified `tool_call_count 6` and that no artifact was written; recorded the id as
`DEAD_KILLED_BEFORE_WRITES` in `manager/SESSION_REGISTRY.md`; re-dispatched on `…183517_69741c`
(`20260922_190127_662ec3`, 51/90 tools inside 9 minutes).

**Rule:** before every `--resume`, list the lineage from `state.db` and take the **newest** member. Match
the minted id to its packet text (§20) — that proves *which* task it belongs to but **not** that it
inherits the right history; the parent must be checked separately.

---

## 3. Two attempts, one candidate

| Attempt | Artifact | Bytes | sha256 | Why it ended that way |
|---|---|---|---|---|
| a3 | `…00001_.mp4` | 157,300 | `ebf49f80…` | refused at publish: declared kind `videos`, server publishes under `images` at node 246 |
| a4 | `…00003_.mp4` | 157,300 | `ebf49f80…` | same bytes after the declaration was fixed |

Same `graph_sha256` (`7ea87b66`), same seed node value `582699151003550`, same driving-video sha
(`7082a1ba…`), same reference sha (`1311699b…`), same five model hashes ⇒ a **deterministic re-render**,
i.e. ONE candidate and one rejected sibling (`…00004_.mp4`, 1280×368 stitch). The report states this
explicitly rather than advertising two candidates.

---

## 4. Independent checks that closed the round

**Claimed-but-absent path.** The lane reported copying the chosen raw render to
`NEW/VIDEO14B/waveB/media/chosen_animate2_book4s_00003_.mp4`; the directory held only
`reference_chosen_640x368.png`. A named path is a claim — the closeout round was sent to write it and
report the sha, and the report marks that path unproven until the sha lands.

**PCM bit-exactness (Manager-run, not lane-reported).**

```
ffmpeg -v error -y -i  <clip 640x360>            -t 4           -f s16le -acodec pcm_s16le -ar 44100 clip.pcm
ffmpeg -v error -y -ss 55 -i <film>              -t 4           -f s16le -acodec pcm_s16le -ar 44100 film.pcm
sha256sum clip.pcm film.pcm   → both 2387eded24366afefdcf16cea122f4cc85366d0…
cmp -s clip.pcm film.pcm      → PCM_IDENTICAL=true   (705,600 B each = 176,400 samples × 2ch × 2B)
```

Two deltas kept as separate labels: container **+1.995 ms** (AAC tail) vs decoded **+84 samples =
+1.904762 ms**. Collapsing them into "audio off by ~2 ms" would have hidden which layer was responsible.

**Delivery probe on the exported clip** (geometry must be the SOURCE's, not the generation canvas):

```
ffprobe -select_streams v:0 -count_frames:
  width=640 height=360 r_frame_rate=30/1 time_base=1/15360 nb_read_frames=120
  format duration = 4.001995
```

**Shutdown proof, read as fields not as a verdict:** `8310/8210/8199/8301` all
`ConnectionRefusedError 10061`; VRAM 1,216 MiB idle; `hermes` PIDs 14872/29648 alive; `collateral []`;
`uses_taskkill_T = false`; the stop tool's survivor list derived from the live process table (no
hardcoded pid list).
