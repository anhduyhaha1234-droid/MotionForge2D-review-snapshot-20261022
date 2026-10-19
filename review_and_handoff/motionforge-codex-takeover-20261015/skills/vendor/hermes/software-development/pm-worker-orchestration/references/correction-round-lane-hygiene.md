# Correction-round lane hygiene (resume dispatch, guards, monitoring)

Measured 2026-09-24 on the MotionForge2D correction round (`mf-core-tool-delivery-20260924/20260924T1055Z`):
3 lanes dispatched by `--resume`, 1 lane finished mid-round. Every trap below cost real time or
nearly produced a false verdict.

## 1. Per-lane write-set manifest BEFORE dispatch — and prove the capture is non-empty

The canonical guard is `MAIN/docs/pm/tools/write_set_guard.py` (`capture` / `verify`). Two rules:

* **Capture the lane's own write-set files with byte snapshots** (`--snapshot-dir`), so a
  destructive shrink or a vanished file is detectable after the worker stops.
* **Make the capturing tool PRINT the enumerated count** and compare it against what you expect.

The trap: `Path.glob('app/services/qc_evidence/**')` returns **2** entries (directories), not the
26 files under it, and the tool cheerfully printed `NO FILES IN WRITE-SET`. `dir/**/*` (or
`rglob`) is required for "everything under here". A manifest that enumerates 0 files is not a
completed prerequisite — it is zero protection with a green checkmark.

**Cross-check the manifest against the reviewer's independently measured hashes** before dispatch.
If `media_engine.py` hashes to the same sha the review published, any later diff is meaningful;
if it does not, you are guarding different bytes than the reviewer reviewed.

## 2. Reviewer repro runs in YOUR scratch — never in the reviewer's output path

Many review probes write their results next to themselves (`OUT = Path(__file__).parent`) and
overwrite the published evidence on re-run. Copy the probe into your own scratch and rewrite
**only** the scratch/output constants:

```python
text = SRC_SCRIPT.read_text(encoding="utf-8")
text = re.sub(r"SCRATCH=Path\('.../review1535core'\)", "SCRATCH=Path('C:/Users/<u>/AppData/Local/Temp/<short>')", text)
text = text.replace("(OUT/'adapter_probe_results.json')", "(OUT/'manager_after_probe_results.json')")
text = text.replace("OUT=Path(__file__).resolve().parent", "OUT=Path('.../manager/scratch')")
assert "manager" in text and "manager_after_probe_results.json" in text   # fail loudly, not silently
```

Then assert the probe really ran against the lane's current bytes: the probe usually records
`adapter_sha256` — compare it to a sha you recompute from disk in the same breath. A probe that
ran against stale bytes proves nothing and looks identical in the pass/fail table.

### MAX_PATH: keep the scratch root SHORT

A scratch root under a deep evidence tree
(`…/outputs/mf-core-tool-delivery-20260924/20260924T1055Z/manager/scratch/repro/probe-<ns>/…`)
plus the lane's `reservations/<32hex>__<attempt>.reservation.json.tmp<pid>` filename crossed 260
chars and the OS refused the create — surfacing as `FileNotFoundError` inside the **project's own
atomic-write helper**, i.e. it looked like a product bug. Use
`C:/Users/<user>/AppData/Local/Temp/<short-tag>` for the scratch root. When a helper raises
`FileNotFoundError` on a file it just tried to create, measure `len(str(path))` first.

## 3. Post-worker guard, then verify — in this order

`guard_after_worker.py <LANE> [other-active-lanes...]` does four things and must run **before**
any gate:

1. verify the write-set manifest (allow-change = every captured path, so only disappearance /
   destructive shrink / snapshot damage fails);
2. `git status --porcelain` in the lane tree — every changed path must sit inside the lane's own
   allowlist prefixes;
3. re-check **every other pinned tree** for HEAD/porcelain drift vs the preflight snapshot;
4. re-check MAIN (HEAD + dirty count preserved).

Pass the lanes that currently have a live writer as `known-active`, otherwise the others-check
reports their in-flight edits as protected drift (a false alarm that trains you to ignore the
guard).

Then do the Manager's own verification: independent probe (above) + **your own run of the
affected-module suite** at the worker's HEAD. On 2026-09-24 the manager run reproduced
`131 passed, 10 skipped in 7.41 s` and the probe matched the worker's `probe_after.json` **9/9**
on `status/error/submit_calls/receipts/staged`. Cross-agreement between two independent runs is
the deliverable; a worker's own log line is not.

## 4. Monitoring a resumed lane: repoint, rotate, and kill by handle

* **`--resume` mints a NEW session id.** A monitor still querying the requested parent id shows
  `0 new rows / age 24 h` for every lane while all of them are working hard. Resolve the actual
  ids first (first user message == that lane's own packet head — one packet per lane per round),
  then point the heartbeat/watchdog at them. **When every lane reads frozen at once, suspect the
  wiring, not a mass stall.**
* **Rotate the watchdog's lane set when a lane goes terminal.** The stall rule ("row count
  unchanged for >8 min") is guaranteed to fire on a closed session: it never grows again. Rotate
  the set in the same operation that dispatches the replacement lane.
* **Stop a watchdog by its tracked background-process handle**, not by filtering the command line
  for its script name — that filter also matches the probing `powershell` and its own `bash`
  wrappers (8 pids) and would kill whatever it matched. Never `killall`-style sweep interpreters
  the agent itself runs on (the Hermes desktop/serve processes are the same `python.exe`).
* Keep a heartbeat line that records per lane: `rows / age_minutes / last_tool / log_bytes`.
  Log bytes alone are misleading — a worker can stream a 9.7 KB report at exit after showing 0 B
  for 48 minutes (stdout is block-buffered until flush).

## 5. Non-English (Vietnamese) deliverables: scan the bytes

Coordination docs in this project are Vietnamese, and stray CJK/English fragments have leaked in
(a table cell shipped as `I 未 proven`). Before delivering, scan the file for out-of-range scripts
(CJK `\u4e00-\u9fff`, `\u3040-\u30ff`, `\uac00-\ud7af`) and fix in place, then re-scan to prove
zero remain. A manual skim is not a check. Deliver to the user in Vietnamese, tables and evidence
summaries included.
