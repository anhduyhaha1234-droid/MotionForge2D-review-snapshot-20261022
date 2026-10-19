# Worker terminal-record lifecycle: RECORD-FIRST → CADENCE → RECORD-LAST

Measured on MotionForge2D R5→R6g (dispatch-long workers, 80-turn invocations, Windows, 2026-10/14).
The terminal record (`<revision>/evidence/terminal/<invocation_id>.json`) is the ONLY terminal
authority — prose/public output never counts. Validation binds immutable dispatch fields
(run/task/owner/invocation/packet/revision/allowed_root) + artifact hashes.

## Failure modes seen in production → exact validator error

| Failure | Validator error (verbatim) | Consequence |
|---|---|---|
| No record: worker hit 80/80 iteration budget mid-work, record never written (**3× in a row**) | `[WinError 2] ... terminal\<inv>.json` → NEEDS_RECONCILIATION | full reconcile cycle; work survives only via checkpoint |
| Record written but refreshed **another invocation's filename** (prior round's id instead of own) | same `WinError 2` (own-id file absent) | full cycle |
| Same artifact path listed twice (even as same kind) | `one file cannot impersonate multiple deliverables` | full cycle |
| Append-only receipt appended AFTER record refresh → stale hash | `artifact hash mismatch: <kind>` | full cycle |
| Revision/owner/packet mismatch (old-revision result bound to new dispatch) | `invocation binding mismatch: ...` | full cycle (correct fail-closed) |

## Standing protocol (embed verbatim in continuation packets)

1. **RECORD-FIRST**: as soon as first valid artifacts exist, write a skeleton record
   (status CONTINUE_REQUIRED + CONCRETE remaining_work). The filename MUST equal the CURRENT
   invocation id (from `{{INVOCATION_ID}}` token substitution) and the `invocation_id` FIELD inside
   must equal that filename. **Never refresh another invocation's record file** — that slips
   straight past content checks and only the filename lookup catches it.
2. **CADENCE**: refresh after EACH completed batch (keys / propagate / assemble / QA). Never leave
   >1 batch unrecorded; at ~55/80 turns refresh + checkpoint regardless of batch state. Deferring
   the write "to the end" is how you lose it — the 80-turn cap kills the turn before the write.
3. **RECORD-LAST**: the final refresh is the LAST write of the invocation (no file writes after,
   reads only). Hash every listed artifact AFTER all writes stop. Exclude volatile append-only
   receipts (e.g. `<stage>_RUNS.jsonl`) from MID-FLIGHT records; include them only in the final one.
4. **DEDUPE**: every absolute path appears exactly ONCE (one kind). For TASK_SUBMITTED: exactly one
   `master` / `comparison` / `matrix` / `checkpoint` / `receipts` (+ others as `"other"`), all
   inside allowed_root; matrix = exactly the 12 canonical keys; `remaining_work: []` only then.
5. **Background chains die at turn end.** A bg process spawned inside the worker does NOT survive
   the turn boundary (observed: a keygen chain left "running" was dead when the turn closed and
   half its shots never propagated). Run batches to their receipt INSIDE the turn (poll), or leave
   state + next-command in the record. Never rely on a bg process across turns.

## Manager reconcile recipe (NR received)

- Preserve, don't backfill: copy terminal/log/receipt bytes to `manager/evidence/<rev>/preserved_*`
  with before/after sha256+bytes; re-derive the artifact-hash audit (matched/total + mismatch list
  with record-vs-current hashes). Do NOT rewrite the record to make hashes agree.
- Map the error string via the table above; classify per writer lineage; do not reset incident
  counts; append a reconcile JSON + a registry entry (bounded patch).
- NR is not task failure: resume SAME SID with the fix stated verbatim ("record must be
  `<own-id>.json`; dedupe paths; cadence"). Workers close cleanly after 1–2 cycles once the rules
  are explicit (R6d→R6g: valid at first try).

## Coordination-file patch discipline (registry/ledger JSON, CRLF)

- Read with `newline=None` (universal) and write with `newline=CRLF` to keep the whole file CRLF;
  or read raw bytes and convert anchor `\n` → `\r\n`. The `patch` tool mangles `\r\n` literals.
- **Validate BEFORE replace**: build the replacement text, run `json.loads(text)` BEFORE
  `os.replace`. Twice a stray `)` then a doubled `,` was written to disk because validation ran
  after the write — and each blind "fix" introduced a new error. Anchor must include exact leading
  whitespace/commas as they appear; adding a comma to a line whose NEXT line already starts with
  `,` produces `",\n,"` (invalid).
- Log before/after sha16 + byte count; assert the parsed result actually contains the new entries.