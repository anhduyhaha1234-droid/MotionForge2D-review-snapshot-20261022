# Monitoring lanes, and finishing runs that stopped on turn budget

Measured 2026-09-24 on a 3-lane parallel round (6 workers over ~4.5 h). Every item below
is a false signal or a recoverable state that cost real Manager time until it was named.

## Receipt-aware stall detection: DONE is not STALL

A lane that has **exited** looks exactly like a **stalled** lane to a naive watchdog: its last
message timestamp freezes and its row count stops growing.

- Measured: a watchdog flagged `CONTRACT rows=194 age=8.8m <-- STALL` while that run had already
  returned `exit 0` minutes earlier with a receipt on disk. The §7 audit (read the launcher
  **receipt** + the log tail) showed "already finished", not "hung".
- Rule: the stall check must **exclude lanes whose launcher receipt file exists** — the wrapper
  writes that receipt only after `subprocess.run` returns, so it is ground truth for "returned".
  Tag such lanes `DONE(exit, not stalled)` in the heartbeat line, keep the row (it is evidence),
  and never raise the stall flag for them.
- Refresh the monitored set whenever the wave changes. Two independent staleness bugs:
  a stale **pid list** makes "all workers exited" fire while other lanes still run, and a stale
  **session-id list** makes a healthy new lane invisible (or watches a dead session forever).
  After every exit: update session ids AND pids, restart the watchdog.

## Active-writer sets need lane-name normalisation

Guard/verification tools that skip "trees with a live writer right now" must normalise derived
lane names. A **closing run** uses the *same tree* as its parent lane but is dispatched under a
derived name (`CONTRACT-finish` vs `CONTRACT`):

- Without normalisation (`a.split("-finish")[0]`), the guard reports the lane's own live edits as
  `protected_tree_drift` — a self-inflicted false FAIL that costs a full investigation.
- Same class: a verified HEAD advance. When a lane commits, its tree HEAD legitimately moves.
  Accept the advance **only if** (a) the old HEAD is still an ancestor
  (`git merge-base --is-ancestor old new`) **and** (b) every path in
  `git diff --name-only old..new` is inside that lane's own allowlist. Anything else is drift.

## "exit 0" ≠ finished — build a finish packet from the worker's own log tail

Workers stop on **turn budget**, not only on error. Read the log TAIL before trusting the receipt.

- Clues in the tail: an explicit remaining itinerary ("còn lại: pytest … ruff … git add … commit"),
  "CHƯA commit", "raw/** chưa tạo".
- Resume the **same owner** (never a new one) with a short finish packet containing:
  1. the exact remaining commands, quoted from the worker's **own log tail** (don't invent them);
  2. the literal evidence-root path, and "no nested `NEW` folder inside it";
  3. the row table it must fill;
  4. "closing run, not a redesign" + a small iteration budget;
  5. the same non-negotiables (allowlist, patch-only, local commit only, terminal vocabulary).
- Measured effect: closing run 19.6 min vs 55.7 min for the main round, same lane, same scope.
- Give every finish packet its **own file and its own ledger row**. Provenance resolution matches a
  session's *first user message* against a *packet head*; an unregistered finish packet shows up as
  `matched_task: null` even though the run is real — so add it to the resolver mapping at dispatch
  time, together with the requested-parent → actual-id row.

## Monitor the CONTINUATION id, never the parent — the 341-minute false stall

`--resume <parent>` mints a **new** session id, so the parent's activity ages forever while the lane
works. Reading the parent in the heartbeat turns a healthy wave into an apparent outage:

- Measured 2026-09-25: three live lanes reported `age = 341.3m / 46.8m / 100.1m` on their parent ids
  while the actual continuation sessions were **0.0–0.7 min** fresh and mid-`terminal`. The parents were
  last active when their *previous* round ended; nothing was wrong, but the numbers read as three hung
  workers and nearly triggered a full §7 stall audit.
- Rule: immediately after every dispatch **and every resume**, resolve the actual session and put THAT
  id in the watchdog's `LANES` map and in the heartbeat. Resolution: list sessions started after the
  dispatch timestamp, read each one's first user message, match against the packet head (one packet per
  lane per round makes it a proof — see the sibling references).
- Record `parent → actual` plus the proof method in the registry/ledger so a reviewer can re-derive it.
- Cross-check before auditing: if a lane looks stalled but that reading came from a parent id, resolve
  first; if the actual session is fresh, fix the monitoring set and log the false alarm as such.

## A flap-resume is not a budget-finish — re-measure what landed first

Two interruption shapes need two different resume packets. Classify by reading the **log payload** and
the **tree**, never the receipt's exit code:

| Shape | Log | Tree / evidence root | Resume packet must say |
|---|---|---|---|
| turn-budget stop | large, containing the worker's own remaining itinerary | committed, or clean with a report gap | "do exactly the remainder you listed" |
| connection flap | **~125 B**, `API call failed after 3 retries: HTTP 503 … 502 fetch connect timeout` | may hold **partial landed work** | "here is what you already landed — verify it, then continue" |

- Measured: the same lane flapped **twice** in one round. First flap: `porcelain=0`, evidence root empty
  → resume as "nothing landed, same round from the start". Second flap: **4 dirty allowlist paths**
  (`adapter.py`, `lease.py`, two new test files) + 4 raw files → the packet listed those exact paths,
  stated "your work IS on disk", and ordered *verify the landed code is reachable → complete the frozen
  matrix → gates → commit → freeze*.
- Never restart a flapped lane from scratch without measuring `git status --porcelain` and the evidence
  root first; a blind "start over" wastes a full round and can duplicate work already valid.
- Tell the worker the retry policy in the packet (re-flap is expected, recoverable, same model/scope)
  so it does not rush a half-finished migration to avoid being interrupted again, and hand it the
  mitigation explicitly: **one bounded step per tool call, raw file written immediately**, so the next
  interruption costs at most the step in flight.

## Heartbeat content that survives a review

Each heartbeat line carries: lane, row count, newest message UTC + age (minutes), last tool name,
log bytes. Add `DONE(exit, not stalled)` (above) and keep the log appended, not rewritten — the
heartbeat file becomes the liveness ledger a reviewer re-reads.

## See also

* `pm-worker-orchestration` → `references/correction-round-closure-and-dispositions.md` — the closure
  half of the same round: finding→owner mapping, the matrix frozen before dispatch, the three
  disposition shapes (`CORRECTED (manager-verified)` / `SUBMITTED (lane evidence)` / `OPEN`), stating
  your verification boundary per lane, and generating packet tables from receipts instead of typing them.
