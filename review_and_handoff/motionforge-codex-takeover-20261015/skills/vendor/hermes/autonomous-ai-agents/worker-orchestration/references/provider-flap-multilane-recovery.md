# Recovering a multi-lane worker wave from repeated provider flaps

Session of record: 2026-09-23, one Manager session, 7 authorized lanes, 2 flaps in ~50 min.
Backs pitfall 84. Complements pitfall 15 (single-writer 502 resume) and 16 (don't fan out
read-only lanes over a flaky endpoint).

## 1. Recognise the failure (do not trust the exit code)

```
exit=0 duration=1215.1s log=...\manager\logs\MF-V1-BENCH-c3r.log
```
while the log itself is **125 bytes** and contains only:

```
API call failed after 3 retries: HTTP 503: [<provider>/<model>] [502]: fetch connect timeout (reset after 17s)
```

Three separate times in this run the launcher returned `exit 0` for lanes that did nothing.
**Gate on log content**: `for f in logs/*.log; do [ $(stat -c%s "$f") -lt 200 ] && echo DEAD "$f"; done`.
The same size test also catches the "did real work then died" case — those logs are kilobytes.

## 2. Measure the blast radius BEFORE re-dispatching

Per lane, in one script (bash `path:label` splitting breaks on Windows drive colons — use Python):

- `git -C <tree> status --porcelain | wc -l` and `git rev-parse --short HEAD`
- evidence-file count under the lane's own `NEW/<LANE>/`
- whether the lane left WIP files (dirty tracked files) or nothing at all

This decides the resume prompt's shape: "**nothing was written, start now**" versus
"**your work is on disk — verify it, do not redo it**". Observed split: 2 lanes with real WIP
(COMFY 3 dirty + 51 evidence files, BENCH 4 dirty + 110 evidence files), 4 lanes with zero bytes,
1 lane with a single new untracked file.

## 3. Snapshot the WIP with the standard capture tool

```
python manager/tools/capture_writeset.py <LABEL>-flap<N> writeset-<LANE>.txt \
    guard/writeset-<LANE>.flap<N>.json --cwd <tree> --snapshot-root manager/snapshots/<lane>-flap<N>
```
Expect `snapshot_hash_mismatch: 0`. This is what makes a later resume's "keep vs amend" auditable.

## 4. Wait, probe, then resume the SAME owner

- Wait the mandated 5 min. Do not retry sooner.
- Probe with BOTH signals: `GET /v1/models` → 200 **and** a real 5-token chat completion
  returning the expected literal. `/models` 200 alone is NOT proof (see pitfall 81).
- Re-dispatch each lane to its **same actual session id** with the same model/provider/scope.
  Record `parent → actual` in the ledger with the proof method (pitfall 36/26).

## 5. The load response (the actual fix)

Two flaps with 7 long streams open is a load signal:

- **Cut concurrent long streams to 3** (the core lanes that gate everything else) and run the
  remaining CPU lanes as a second batch after the first reports.
- **Stagger starts by ~45 s** (`sleep 45` / `sleep 90` prefixes on the launch commands) so the
  lanes are not all mid-request at the same instant.
- Keep one heavy GPU job at a time regardless — CPU lanes may run beside it.

Measured result: 3 staggered lanes ran 24–87 tool calls with zero further flaps.

## 6. Never merge resume packets across lanes

A single `RESUME2-WAVE-A.md` with per-Task-ID sections destroyed provability:

| Attempted proof | Result |
|---|---|
| first user message == packet head | all 3 sessions byte-identical → cannot discriminate |
| `state.db.parent_session_id` == `--resume` parent | column exists but **NULL** for worker rows |
| keyword count over tool RESULTS | packet text is echoed in results → poisoned counts |
| `[terminal] ran \`<cmd>\`` echo | UI rendering only, not stored in the DB |
| assistant-message action text | too short early on (workers still reading) |

Outcome: the mapping had to be labelled **`INFERRED`** (dispatch order + the 45 s stagger matched
session starts exactly) in the ledger, with a `actual_session_proven_by` field, and re-confirmed
later from each worker's self-reported id. **Write one packet file per lane per round even when the
content is 95 % identical** — that is the only thing that keeps the mapping provable.

A helper worth keeping: `manager/tools/reconcile_ledger.py` derives each row's `actual_session`
by matching the session's first user message against the packet text, preferring the DB lineage
column when the packet is unique, and supports an explicit `INFERRED` override table. Note the
two bugs that made its first run useless — see pitfalls 37 (sqlite cursor reuse) and 38/84.

## 7. Verify the lane's fix with a sentinel, not the report

When a lane's task is "stop writing into protected evidence", the manager's acceptance is a
**sentinel run**, not the worker's summary:

1. record bytes + row count + sha256 of the protected artifact
2. run the previously-leaking suite/module yourself, twice
3. re-record and diff — the protected artifact must be byte-identical and the new run must have
   appended **0 bytes**

Observed: 184,680 B / 422 rows / sha `21d5b178…` identical across a full-suite run ⇒ PASS.
Also read the FIX in code before accepting it: the leak was `_ledger_path()` computed at import
time, so `MF_BENCH_WORK` moved scratch but not the ledger; the fix resolves the path at CALL time,
falls back into the scratch root, and **fails closed** when the target is inside an evidence root.

## 8. Worker claims vs disk truth (same wave)

Three claims turned out wrong when the manager checked them, and every check was cheap:

1. **"3 rows PASS" with RED tests at the new HEAD.** A writer declared `F05/F06/F07 PASS` from a
   suite run made BEFORE its own final commit; at the commit it had just created, **2 of its
   registered tests failed** (`2 failed, 24 passed, 1 skipped` vs `26 passed` at the previous
   HEAD) and 6 new `ruff --select F` findings sat in the files that commit added. Rule: after any
   writer that edits code AND commits, re-run the suite **at the new HEAD** and diff the tier
   counts against the previous round — account for every delta either way (extends #35).
   When correcting, forbid "fix it by relaxing the assertion": diagnose first. One assertion was
   merely stale (`select_filter(keep)` became `select_filter(keep, crop)` once the crop was folded
   into the same step); the other asserted the wrong engine history key (`videos`, where a real
   server publishes `images`). Demand the assertion keeps its teeth + a pre-fix RED capture, and
   **re-hash the artifact afterwards** to prove the test fix moved no bytes.
2. **"the chosen candidate file is missing."** It existed — copied into the wrong directory because
   the picker tool takes `media_dir` as `argv[3]` and the caller passed `raw/media` instead of
   `media`. Before accepting a missing-artifact claim, `find` it yourself.
3. **"no evidence was written."** True for six lanes but not for the two that mattered — those had
   dozens of evidence files. Never generalise one lane's footprint to the whole wave.

## 9. Housekeeping

- Stale completion notices keep arriving AFTER terminal state and after you killed a monitor —
  triage in one command by reading the log (125 B ⇒ it is the already-analysed flap) and reply
  "already processed, no action". Do not re-open a closed lane.
- A killed monitor's `exit 1` is the normal force-terminate code, not a failure. Diff the
  `python.exe` pid set before/after to prove zero collateral (pitfall 22 in
  `terminal-engineering-discipline`).
