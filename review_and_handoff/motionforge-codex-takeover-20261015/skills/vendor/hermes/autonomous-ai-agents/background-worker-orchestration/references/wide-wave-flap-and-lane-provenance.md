# Wide-wave upstream flaps: concurrency response, damage measurement, lane↔session provenance

Verified 2026-09-23 on a 7-lane `hermes -z` wave (MF core-correction + tool-delivery wave A).
Companion to the `background-worker-orchestration` section "A WIDE parallel wave vs SUSTAINED
upstream flaps".

## 1. The failure signature

Every lane, both flaps, identical shape and a **~125-byte log**:

```
API call failed after 3 retries: HTTP 503: [<provider>/<model>] [502]: fetch connect timeout (reset after 11–29s)
```

Launcher receipt in every case: `exit_code: 0`. Twelve receipts across two flaps were
indistinguishable from success unless you read the log payload. The route answered
`GET /v1/models` → HTTP 200 **and** a live `hermes -q "Reply exactly: PROBE_OK"` returned the literal
token with `reasoning_tokens=21` after each flap ⇒ transient provider flap (§7), not
`BLOCKED_MODEL_ROUTE`, not auth/quota.

Flap cadence observed: deaths at ~16:00 and ~16:45, i.e. **two flaps inside ~50 minutes** while seven
long streams were open. That correlation is what justified changing the dispatch shape rather than
re-rolling the same seven.

## 2. Per-lane damage table (measure BEFORE writing any resume packet)

| Lane | Ran | Tools | WIP left on disk |
|---|---|---|---|
| core lane A | 3,933.6 s (~65 min) | 64 | **3 files dirty** + 51 evidence files |
| core lane B | 1,215.1 s | 19 | **4 files dirty** + 110 evidence files (102 under `work/`) |
| core lane C | 1,049.0 s | 24 | none (tree clean at pinned HEAD) |
| CPU lane D | 1,219.5 s | 16 | none |
| CPU lane E | 1,194.3 s | 19 | 1 evidence file |
| CPU lane F | 1,027.6 s | 18 | **1 new untracked source file** |
| CPU lane G | 1,267.5 s | 23 | none |

How it was measured (all cheap, all from disk, none from worker prose):

- evidence-file count per lane: `find <NEW>/<LANE> -type f | wc -l`
- tree state: `git -C <tree> status --porcelain | wc -l` plus `git -C <tree> rev-parse --short HEAD`
- dirty attribution: the porcelain lines themselves
- WIP byte snapshot: the wave's `capture_writeset.py <label> <list> <out.json> --cwd <tree> --snapshot-root <dir>`

Write this table into the incident file. It is the evidence that a resume packet's wording
("finish your 3-file WIP" vs "you wrote nothing, start from the top") is fact-based. Without it you
either redo finished work or tell a lane its tree is empty when it is dirty.

## 3. The concurrency change (and how to present it)

- **7 → 3 concurrent streams.** Batch 1 = the lanes every downstream step gates on. Batch 2 = the
  independent CPU lanes, dispatched only after batch 1 reports.
- **Stagger starts ~45 s.** Confirmed from session start timestamps:
  `16:48:59 / 16:49:44 / 16:50:29` (three lanes), and the earlier batch `16:48:59 / 16:49:44 / 16:50:29`.
- Present it as a **measured load response** with the failure correlation, explicitly *not* as an
  arbitrary worker cap — and note that the critical-path lane is why batch 1 is those three.

## 4. Lane↔session provenance: what the DB can and cannot prove

This is the part that cost the most time. After a merged-packet dispatch the mapping
lane → session id could not be proven. In order of attempt:

| Method | Result |
|---|---|
| `first-user-message == packet head` (content match) | **FAILS** for a merged packet — every lane's first user message is the whole identical packet |
| `sessions.parent_session_id == the id passed to --resume` | **FAILS** — the column is `NULL` for every worker row; so are `cwd`, `title`, `session_key`, `display_name`, `handoff_state` |
| keyword count over `role='tool'` results | **FAILS** — tool results echo the packet text, which names every lane's tree |
| `[terminal] ran \`<cmd>\`` echo to recover the worker's own command line | **FAILS** — that prefix is a UI rendering; it is **not** stored in `messages.content` (0 matches) |

Consequences and the workable rules:

1. **One packet file per lane per round** — that keeps method 1 valid, which is the cheapest proof.
2. When a merged packet was unavoidable: capture launch-order → session-start timestamps at dispatch
   time and grade the row **INFERRED**, with the basis written into the ledger. Never present INFERRED
   as proven.
3. **A worker that reads its own `HERMES_SESSION_ID` and reports it upgrades its row to CONFIRMED.**
   Observed: one lane reported `20260923_165029_286f96` from its process env, matching the value
   inferred at dispatch time — that row's provenance label was then rewritten to
   "CONFIRMED by the worker reading its own process env".
4. **A worker self-report can name its PARENT instead of itself.** An earlier round recorded the
   previous round's session id as its own; the real id was only visible from the DB plus the measured
   process window. Derive it; do not accept the self-report.
5. Ask for the provenance explicitly: a resume packet can *require* the worker to print the value of
   its own process env var as part of the report. That converts a guess into evidence at zero cost.

Ledger row shape that makes this auditable:

```json
{"task": "...", "round": "c3b", "parent_session": "<the id passed to --resume>",
 "actual_session": "<id>", "actual_session_proven_by": "state.db parent_session_id == --resume parent"
   " | first-user-message == packet head"
   " | INFERRED: dispatch order + 45 s stagger (shared packet prevents content proof)"
   " | CONFIRMED by the worker reading its own process env (HERMES_SESSION_ID)",
 "session_started_utc": "...", "session_ended_utc": "...", "session_end_reason": "agent_close",
 "packet": "<abs path>", "packet_sha256": "<upper>", "packet_bytes": 5195,
 "model": "...", "provider": "custom", "fallback": false,
 "cwd": "<lane tree>", "log": "<abs>", "receipt": "<abs>", "receipt_exists": true}
```

Build it with a reconciler script rather than by hand — see the two scripting traps below.

## 5. Scripting traps hit while building the reconciler

- **Iterating a sqlite cursor while re-executing on the same cursor truncates the outer loop.**
  `for row in cur.execute(A): cur.execute(B)` silently stops the outer result set after row 1, which
  made a 13-session scan look like a 1-session scan and reported every content match as UNRESOLVED.
  Materialise first: `rows = list(cur.execute(A))`, then query inside the loop. Symptom to recognise:
  a blanket impossible failure.
- **Never pair parent→actual by dispatch order or timestamps.** That produced 4 of 6 pairs wrong
  (two swapped) because `--resume` mints continuation ids that do not follow dispatch order and
  several sessions can share the same start second.
- Read the DB through the read-only immutable URI: `sqlite3.connect("file:<…>/state.db?mode=ro", uri=True)`.
- A quick harness to prove lane identity when content matching works: compare
  `" ".join(first_user_message.split())` contains `head_of_packet[:220]`, and take the newest match
  when a packet prefix is shared with its own earlier round.

## 6. Verifying a "one submit" budget from the engine log

A GPU lane was dispatched with an explicit **one submit** cap, yet its output directory held **two**
clips (`…_00005_.mp4` 117,027 B, `…_00006_.mp4` 147,901 B). That is not automatically a budget
violation: the server log showed **two 6/6-step sampling passes inside a single prompt execution**
(71 s at 11.86 s/it, then 33 s at 5.52 s/it with the model already resident) ending in one
`Prompt executed in 162.14 s`. Read the raw engine/server log for the number of submits and sampling
passes, and get the lane's own explanation of what each pass was (control vs fix) — do not infer
either a violation or compliance from the artifact count.

## 7. Bounded walks: a tool timeout returns NOTHING

`find <runtime-tree> -newermt … -type f` over the model runtime exceeded the 300 s tool timeout and
returned **no output at all** (exit 124) — not a partial list. Enumerate the specific subdirectories
(`output/`, `runs/`, `temp/`, `input/`) and rglob each with an early break and a hit cap, from a
`write_file`d script. The timeout kills the process; only a bounded walk reliably answers.

## 8. Incident file shape that was accepted

`manager/incident/INCIDENT_502_WAVE_A.md`:

1. the exact payload plus per-lane table (session, ran, tools, WIP);
2. classification (`RUNNING_RETRY_WAIT`, transient) with the route-probe evidence that rules out
   auth/quota/config;
3. the handling rules (exit 0 is not proof; sessions reuse their own ids; partial writes covered by
   pre-dispatch snapshots; post-wait probe recorded; no wave restart; the never-stopped lane not
   re-dispatched);
4. a **disclosed Manager-error addendum** — including the 4-of-6 wrong provenance pairing and the
   corrupted-registry/cursor bugs, each with the corrected values.
