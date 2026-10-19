# Lane-orchestration playbook — running N CLI workers against a Manager gate

Class-level notes from a 12-dispatch correction round (9 lanes, 8 h of dispatch wall time, 11 receipts).
Everything below was measured, not theorised; the numbers are the evidence.

## 1. The three traps that make a "success" look real when it isn't

| Trap | Measured signature | Rule |
|---|---|---|
| Launcher exit code | `exit 0` with a **124–125 byte** log containing `API call failed after 3 retries: HTTP 503 … 502 fetch connect timeout` | Gate on **log bytes + payload**, never the exit code. 125 B is the flap signature. |
| Pipe masks the real RC | `npm run build 2>&1 \| tail -30; echo "RC=$?"` printed `RC=0` while the build was fine **and** while lint was failing — `$?` was `tail`'s | For any gate whose result you will report, **never pipe**: redirect to a file (`cmd > out.txt 2>&1; echo RC=$?`) or use `${PIPESTATUS[0]}`. This produced one wrong `PASS` in a UI gate before it was caught. |
| `exit 0` after a long run | 55 min run, implementation complete, **no commit / no report / evidence root never created**; the worker's own log tail listed the remaining steps | That is turn-budget exhaustion, not success and not a blocker → resume the same owner with a **finishing packet** naming the exact remaining commands. |

## 2. Packet shapes: finishing vs confirmation vs retry

Pick the shape from what is already on disk — do not redesign the work.

- **Finishing packet** — artifacts are absent/incomplete. List the exact commands the worker itself said remained, the
  report shape, and state plainly that the run ended on budget, not on an error. Budget ~35–70 calls.
- **Confirmation packet** — artifacts are complete and the run died *after* writing them (e.g. report + commit + clean
  tree exist, log tail is a flap). Ask for a **read-only** re-read: footprint (`HEAD`/`HEAD^`/`git show --stat`/porcelain),
  sentinel re-hash, and one explicit open question. Say "this run should normally write nothing". Budget ~25 calls.
- **Retry packet (flap)** — same packet shape, launched after the canonical wait (5 min), same owner/model/scope, and
  labelled so the ledger shows the cycle (`resume-after-502`, `…-b`).

## 3. Liveness monitoring that survives a wave change

- **Receipt file == DONE.** A lane's launcher writes its receipt only at process exit, so `receipt exists` is a
  reliable "finished" marker; **`ended_at` in the session DB is not** (killed sessions stay open forever).
- **Watch out for the pid-list expiry.** A watchdog seeded with the *current* worker pids exits with
  "all workers exited" the moment that wave ends — even though the next wave is already running. Re-arm the watchdog
  (new pids **and** new session ids) every time you dispatch a new batch, and teach it to skip lanes whose receipt
  exists, otherwise a normal exit is reported as an 8-minute stall.
- **Progress signal that works:** `message rows` for the lane's session from the read-only state DB (open with
  `mode=ro`), plus the newest `tool_name`/timestamp. Rows commit at turn boundaries — a lane that is "thinking" shows a
  stale row for a few minutes; only a >8 min freeze with zero new rows and zero new tool processes is a stall.
- **SQLite discipline:** materialise rows before running an inner query (`rows = list(cur.execute(A))`), or a loop
  silently truncates to one iteration and every match reports UNRESOLVED.

## 4. Byte-guard design for a lane (post-worker checks)

Order: **worker terminal → byte guard → micro repro → matrix → focused/static → affected-module → integration gate.**

The guard must do four things, and each has a way to produce phantoms:

1. **Manifest verify** (sha/bytes/lines/snapshot) — allow every captured path to change so only *disappearance*,
   *destructive shrink* or *snapshot damage* fails.
2. **Scope containment** in the lane's own tree — parse porcelain **per line, after slicing**; stripping the whole
   stdout first eats the significant leading space of the first line and reports a violation that never happened
   (see the discipline skill's #43).
3. **Other trees unchanged** — but exclude lanes with a live writer *and* accept a **verified advance**: if a lane's new
   HEAD has the old baseline as an ancestor and every file in `base..HEAD` is inside that lane's own allowlist, that is
   a legitimate commit, not drift. Accepting this removed 2 of 2 phantom "protected_tree_drift" failures.
4. **Lane-name normalisation** — a `-finish` run writes the same tree as its base lane; map `"<LANE>-finish"` →
   `"<LANE>"` before deciding which trees to skip.

## 5. Session provenance that a reviewer can re-derive

- **One packet file per lane per round.** That single rule is what makes `first user message of the session == head of
  that lane's packet file` a valid proof of the parent→actual mapping; a merged packet destroys it.
- `--resume` **mints a new session id**; the requested parent is the argument, the actual id is new. Record both in the
  ledger plus the proof method, and resolve with a read-only query against the first user message.
- Grade rows: `PROVEN` (content match) / `CONFIRMED` (worker self-reported its own id and it matched) / `INFERRED`
  (order + stagger only). Never present `INFERRED` as proven.

## 6. Independent verification ladder (Manager side)

1. **Re-run the reviewer's own probe**, but never in place — the scripts usually write their results next to themselves
   and would overwrite review evidence. Copy to your own scratch and repoint only the output/scratch paths (assert the
   substitution so a silently-unmatched replace cannot no-op).
2. **Compare hashes, not narratives:** the probe header embeds the module sha it imported; recompute the same sha from
   disk and require equality before believing either side.
3. **Cross-check worker vs reviewer vs yourself:** worker "before" evidence should reproduce the reviewer's published
   results field-for-field; your after-run should match the worker's after-run.
4. **Re-run the load-bearing suite yourself** — matches are only meaningful if the numbers agree (e.g. 68 passed /
   185.25 s reproduced).
5. If the reviewer's script **aborts** on fixed code, that abort can *be* the fix (a typed refusal replacing a silent
   pass). Capture per-item outcomes in `try/except` and say so explicitly rather than reporting "probe failed".

## 7. Reporter-facing details that decide whether a claim survives review

- **Interface deltas must be disclosed**: if the fix removes/renames a parameter the reviewer's probe calls (e.g. a
  caller-supplied boolean replaced by a backend-resolved proof object), state the old call, the new call, and that the
  reviewer's one-liner will now raise — with the exact re-run form.
- **Staleness is judged by BYTES, not mtime.** A deterministic re-export rewrote a candidate with identical bytes and a
  new mtime; the correct verdict was "freeze unchanged, evaluation stands", with the mtime movement disclosed.
- **Lineage before transport**: measure `merge-base` between each source branch and the integration base *before*
  dispatching a transport owner. A branch can be missing the integration base as an ancestor while still sharing an
  older merge-base — that changes the transport method (cherry-pick with conflict-abort, not fast-forward) and must be
  written into the packet.
- **Coverage honesty beats completeness theatre**: state exactly which artifacts/frames were inspected and which were
  not; a technical all-PASS is never a visual PASS.
