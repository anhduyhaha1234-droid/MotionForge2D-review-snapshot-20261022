# Continuation-id monitoring & vacuous-guard traps

Measured 2026-09-24 during a 3-lane correction round (Hermes-CLI workers resumed with
`--resume <parent>`). Every item below cost real time or nearly produced a false green.

## 1. The monitor must target the ACTUAL continuation id, never the requested parent

`hermes -z … --resume <parent_id>` **mints a new session id**. If your heartbeat/watchdog
queries `<parent_id>`, it reports the parent's last message from the previous day
(age ≈ 1400 min) with a flat row count — which is byte-for-byte the signature of a
**stalled lane**, while in reality the worker was writing dozens of turns per minute.

False-stall signature to recognise:
- rows flat + age huge
- BUT the process pair is alive AND tool children (`bash.exe` etc.) were spawned in the
  last few minutes
- AND `state.db` grows

Rules:
1. Resolve actual ids **first**, then build the monitor from those ids.
2. Resolution method (one packet per lane per round is what makes it provable): read the
   session's FIRST user message from the read-only DB and match it against the head of
   *that lane's own* packet file. Record the method in the ledger/registry row.
3. Write it down as a correction when you get it wrong: "monitor targeted the requested
   parent" is a *bookkeeping* error, not a worker fault. Never let it be read as a stall,
   and never resume a worker because of it.
4. Keep the requested→actual pair in the same row as the proof, e.g.
   `parent 20260923_164859_a5fcbd -> actual 20260924_175709_40429c [PROVEN]`.

## 2. A capture that returns 0 files is a FAILED capture, not a clean baseline

`Path.glob("dir/**")` in CPython does **not** recurse into subdirectories; `"dir/**/*"`
does. A write-set capture built on the former reported

```
[COMFY] NO FILES IN WRITE-SET — check globs
```

for a lane that actually had 42 files in scope. Had that empty manifest been accepted as
a baseline, the post-worker guard would have had **nothing to guard** and would have
returned `VERIFIED` forever — the most dangerous kind of green (compare pitfall #27:
vacuous proof after a failed command).

Rules:
1. Treat `files == 0` as a hard failure of the capture step, not a result. Print the count
   in the summary line for every lane.
2. Cross-check the capture against an artifact whose hash an independent reviewer already
   published (in this round: `media_engine.py 55a423df…`, `compose.py 1e9e7bc7…`,
   `adapter.py f0237554…` all matched the review's own measurements) **before** dispatch.
   Agreement with a third-party hash is proof the manifest covers the right bytes.
3. Never cite a guard result whose manifest you have not seen populated.

## 3. "Waiting on upstream" vs "hung" — probe before you escalate

Cheap probe, ~45 s:

```
# CPU delta over 45 s on the hermes/python worker pair
$a = @{}; foreach($p in $pids){ $x=Get-Process -Id $p; $a[$p]=$x.CPU }
Start-Sleep 45
foreach($p in $pids){ (Get-Process -Id $p).CPU - $a[$p] }
```

- ≈0.1 s CPU over 45 s + ESTABLISHED socket to the router = **waiting for the model**
  (normal; the model TTFB dominates).
- High CPU with no new tool children = actual spin/hang; escalate.
- A tool child (`bash.exe`, `ffmpeg`) created in the last few minutes is stronger proof of
  progress than the launcher log, which in `-z` mode can stay **0 bytes** for the first
  several minutes of a healthy run.

## 4. DB rows are the heartbeat; the launcher log is not

Per-lane progress = message-row count + newest `tool_name` + age in minutes, read from
`state.db` with `mode=ro`. Materialise rows before any inner query (a cursor reused inside
its own iteration silently truncates the loop). See `scripts/lane_heartbeat_ro.py`.

## 5. Guard-after-worker false-positives while sibling lanes write

A post-worker check that asserts "every other pinned tree is unchanged" flags the other
concurrent lanes, which are *legitimately* dirty. Pass the currently-active lanes as
`known_active` and skip them; run the all-tree/quiescence check only when every writer is
terminal. Otherwise a correct run reports `FAILED` and trains you to ignore the guard.

## 6. Lane-scope containment is the cheapest high-value guard

Per lane: `git status --porcelain` in that lane's tree, assert **every** changed path
starts with the lane's allowlist prefix (or equals an allowed file). It catches scope
violations the moment they happen and needs no manifest. In the round above, all three
concurrent lanes were provably in-scope within minutes of dispatch:

```
COMFY     M experiments/mf_reskin_v1/comfy/mf_comfy/{adapter,errors,lease}.py + 2 new tests
P1QC      M app/services/qc_evidence/{compose,errors,sources}.py + new observe.py
CONTRACT  M app/schemas/media_engine.py
```

## 7. Freeze the micro matrix BEFORE dispatch

Write each row with its exact expected counts (POST / artifact / marker / receipt), file:line,
and the exact test node. A worker's report then becomes checkable rather than narrative, and
a "green broad run" cannot be used to waive a row that is still binary-open. Freeze it before
the first dispatch and hash it.

## 8. Packet hygiene that keeps provenance provable

- **One packet file per lane per round** — that is exactly what makes
  "first user message == packet head" a valid mapping proof. Merged/shared packets destroy it.
- Write the evidence destination **literally** in the packet (full absolute path + a worked
  example file path) and add one line: "write here, do NOT create a nested `NEW` folder
  inside it". Two spellings of a path alias split one round's evidence across two trees.
