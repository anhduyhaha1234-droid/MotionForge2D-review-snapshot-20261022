# Terminal-record handshake: producer-side failure modes (measured)

Context: a dispatch harness validates a worker's structured terminal record against the
immutable dispatch row (invocation id, revision, packet hash, artifact hashes). Across ONE
task lineage (5+ invocations), the worker broke its own record in FOUR distinct ways — each
NR (NEEDS_RECONCILIATION) cost a full reconcile+re-dispatch cycle. All four are producer-side
protocol slips, NOT work defects. Recognize the validator error strings below instantly.

## The four modes (validator signature -> cause -> fix)

1. `[WinError 2] cannot find <evidence/terminal/<INV>.json>` after a long run (~80/80 turns)
   -> worker hit the iteration budget immediately BEFORE writing the record. Prose said
   "complete" but prose is not terminal.
   FIX (packet): "RECORD-FIRST" — write a skeleton record (status CONTINUE_REQUIRED +
   remaining_work + current artifacts) EARLY, refresh at each milestone, and refresh before
   ~65/80 turns. A record that exists-but-stale is recoverable next round; a missing record
   is NR.

2. `artifact hash mismatch: <kind>` where ONLY append-only receipts differ
   -> worker refreshed the record at a milestone, then kept WRITING to listed artifacts
   (appended rows to *_RUNS.jsonl). The refresh-before-final-writes staleness.
   FIX (packet): "RECORD-LAST" — the record refresh must be the ABSOLUTE LAST write of the
   invocation; exclude volatile append-only receipts from mid-flight records (add them only
   in the final record when all writes have stopped); manifest hashes must also be computed
   AFTER the final record write.

3. `[WinError 2]` at the CORRECT path pattern but a DIFFERENT filename than the dispatch's
   invocation id -> worker refreshed the PREVIOUS invocation's record file (name from
   context/checkpoint) instead of writing its own `{{INVOCATION_ID}}.json`.
   FIX (packet): state the exact rule — "record path MUST be `<evidence/terminal>/<THIS
   invocation's id>.json`; the `invocation_id` FIELD must equal the filename; NEVER
   refresh or edit another invocation's record file."
   Do NOT backfill the misfiled record afterwards (closed invocation, no history rewrite).

4. `one file cannot impersonate multiple deliverables` -> the artifacts list contained the
   SAME absolute path twice (two rows, typically both kind "other").
   FIX (packet + pre-write helper): dedupe by path — `len(paths) == len(set(paths))`;
   each path appears exactly once with one kind; TASK_SUBMITTED additionally needs exactly
   one artifact of each required kind.

## Standing policy when NR happens (manager side)

- The receipt/receipt stands; do NOT backfill or rewrite the closed invocation's record.
- Write a reconcile evidence file (root cause verbatim error, work actually done, decision,
  next fix) under the NEW round's evidence tree; append to registry history.
- Add the specific fix to the next continuation packet as a numbered "SỬA LỖI BẮT BUỘC"
  section — one defect per bullet, with the validator's exact error string quoted.
- Full-turn hygiene: even when the worker ends cleanly, verify record path name + field +
  dedupe + fresh hashes as the FIRST check of reconciliation.

## Quick reconciliation checklist for a new invocation receipt

1. `decision` + `error` verbatim from receipt.
2. Does `evidence/terminal/<inv>.json` exist and does its `invocation_id` field MATCH the filename?
3. Recompute sha256 of every listed artifact vs record (expect 0 mismatches for a clean close).
4. `len(paths)==len(set(paths))` (dedupe).
5. Only then accept CONTINUE_REQUIRED / TASK_SUBMITTED as the class; otherwise NR + packet fix.

Related: IEV ref `structured-terminal-recheck.md` (verifier-side); this ref is the
producer-side counterpart.
