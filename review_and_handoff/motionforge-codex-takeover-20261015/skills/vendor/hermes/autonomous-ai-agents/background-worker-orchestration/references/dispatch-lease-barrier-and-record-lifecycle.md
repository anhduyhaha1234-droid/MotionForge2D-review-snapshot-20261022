# Dispatch lease barrier + terminal-record lifecycle (long-running CLI workers)

Measured on MF-DEMO-LONG-01 R5 (2026-10-11/12): Hermes CLI worker resumed by a Manager dispatch harness
(4 invocations in one night), Windows, single GPU writer (ComfyUI), each invocation ending in a
structured terminal record validated against an immutable dispatch ledger row.

## Terminal record = the only completion authority

- `exit 0` is NOT completion. Measured endings that all looked like success: exit 0 + API-error text;
  exit 0 + `⚠ Iteration budget reached (80/80)` with NO record written; and log plan-lines
  ("…will submit") matching a substring grep. Only a schema-validated structured terminal record may
  drive submission/continuation decisions; log prose is reference-only.
- Every CONSUMER re-validates, not just the dispatcher: binding = run/task/owner/invocation/packet
  sha/revision taken from the IMMUTABLE dispatch row + artifact sha256 recomputed on CURRENT bytes +
  a known-decision enum. Unknown decision, stale/foreign receipt, wrong invocation, hash drift,
  missing/truncated/duplicate-key JSON → `NEEDS_RECONCILIATION`.
- Keep the round revision explicit in the binding (r4 vs r5 style) so a previous round's record can
  never satisfy the next round; extend the schema enum as a controlled one-line addition.

## Record protocol: FIRST → LAST (two production failures taught this)

1. **RECORD-FIRST** (write a skeleton record early, refresh at milestones) fixed the failure mode
   where a worker hit its turn budget immediately BEFORE writing anything → no record at all →
   dispatch failed closed → a full reconcile cycle lost.
2. BUT record-first alone produced **STALE HASHES**: append-only receipts (`*_RUNS.jsonl`) kept
   growing after the refresh, so one listed artifact mismatched → whole record NR.
3. **Final protocol — RECORD LAST**
   - Mid-flight records list only STABLE artifacts (checkpoint .md, scripts, QA sheets, ledgers you
     will not touch again). EXCLUDE volatile append-only receipts.
   - The record refresh must be the FINAL write before the turn ends: stop writes → recompute
     sha256 of every listed artifact → write record → end immediately.
   - Near the budget boundary (~65/80 turns): refresh checkpoint + record; if any write happens
     after, refresh the record once more at the very end.
- **Reconcile policy**: read the NR error verbatim, classify (missing file / one stale hash /
  binding mismatch), then resume the SAME SID with a corrective packet that (a) names the exact
  defect, (b) updates the write-order protocol, (c) carries the open work list. NEVER backfill a
  closed invocation's record (no retagging history) — the NR receipt stands as truth.

## Single-writer dispatch barrier (one controller, one GPU)

- Under the controller mutex and BEFORE Popen: reconcile every non-released lease + ledger lineage.
  Child ALIVE → refuse (rc4 + ledger row; do NOT touch the foreign lease). Child/probe UNKNOWN →
  refuse (needs reconciliation). RESERVED with a live or unverifiable launcher → refuse (spawn
  barrier). Only verified-dead children + quiet render/queue probe → adopt (release with
  `adopted_by` evidence) and continue.
- Reserve BEFORE spawn (status RESERVED + launcher pid/created/name), promote to ACTIVE after Popen
  with child + early descendants; abandon ONLY if the child never spawned. The reservation is the
  real barrier: a second controller seeing a fresh RESERVED refuses even without lock contention.
- Terminal requires `child_state is False` (VERIFIED dead) AND lease released (children dead +
  queue quiet). UNKNOWN keeps the claim open — probe failure must never read as reconciled.
- Controller lock alone proves nothing about a detached GPU child; check the lease, not the lock.

## Render-runner detection without false positives

- Match by SPAWN SHAPE: argv0 basename (native exes e.g. ebsynth) OR interpreter-is-python + a later
  argv token that is a script path whose basename matches the runner list (video_blend / sam2 /
  r4_build / r4_render / render_run / wan_run / vace / cotracker / gmflow / inpaint / propainter…).
  Do NOT substring-match the whole command line: the LLM child's argv carries the ENTIRE packet
  text, so every word in the packet would false-positive.
- Skip argv tokens >~400 chars and tokens containing newlines (packet-in-argv); keep an exclusion
  list for the manager's own tool scripts.
- Corollary: never write literal `<render-script>.py` filenames inside dispatch packets.

## Stall handling (silence triggers an audit, never an auto-kill)

- Log silence past the threshold → AUDIT: artifact-delta over the worker's write roots + descendant
  scan + render/queue probe. PROGRESSING (fresh artifact bytes) never kills. UNKNOWN (live render
  signal or probe failure) never kills — needs reconciliation. Only TRUE_HANG (no artifact delta
  AND render probe verified quiet) kills, with a distinct classification for same-owner resume.
- A venv python shim spawns a base-python child that runs the script: a live "descendant" is NORMAL
  while the child works. Never gate the hang decision on "all descendants dead" — use the
  render-pattern probe + artifact delta as discriminators.
- Watch roots = allowed root + worker input/output/temp trees; scan only on audit (cheap).

## Heartbeat revalidation

- Each tick recompute the terminal verdict against the immutable dispatch row + current artifact
  hashes; render NR with the error and a `revalidated` marker for auditability.
- Benign tick race: a tick can read the ledger a fraction of a second BEFORE a new dispatch row
  lands → that single row shows the previous invocation; the next tick corrects. Not an error.

## Quick checklist

- [ ] dispatch refuses on foreign ALIVE/UNKNOWN/RESERVED claims; exactly one winner under a race
- [ ] lease reserved pre-spawn, promoted after, released only verified-dead + quiet
- [ ] terminal record revalidated vs immutable row + fresh hashes at EVERY consumer
- [ ] record-last protocol taught to the worker; volatile receipts excluded mid-flight
- [ ] NR reconciled via resume-same-SID corrective packet; closed invocations never backfilled
