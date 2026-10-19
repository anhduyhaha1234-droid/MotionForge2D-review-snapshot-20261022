# R28 (MF-V1-COMFY) learnings — concurrency fix + evidence hygiene

Measured 2026-09-27 on `experiments/mf_reskin_v1/comfy` (adapter/lease ledger).

## 1. A "fingerprint changed?" guard cannot decide a race — re-take the decision under the lock
R27 fixed a same-attempt double-POST by snapshotting the durable union and re-resolving in-gate
when the snapshot differed. The residue: the snapshot was taken AFTER the decision, so a commit
landing in `[decision, snapshot]` is *already inside* the snapshot, the comparison reports
"unchanged", and the second caller POSTs again. Any design of the form
`decide(); snap = view(); ... if view() != snap: decide()` is unsound. What works: the lock is
exclusive, so **re-take the decision unconditionally inside the critical section** and drop the
snapshot from the control path (keep it as ordered audit evidence). Test it by parking the
second LIVE caller exactly at the first snapshot read with the first caller allowed to finish —
on the pre-fix bytes that row measures 2 POSTs, on the fixed bytes 1 POST.

## 2. Re-deciding under the lock needs an IGNORE-SET of self-dispositioned records
Re-taking the decision makes the caller re-read its own writes: its `not_accepted` release looks
like "this attempt is already terminal" and the legitimate retry it just authorised is refused.
Track the paths the caller itself dispositioned (marker removed + receipt written) and filter the
view with them before reconciling. This is the difference between "serialize the decision" and
"deadlock the legitimate requeue" — the two requirements pull in opposite directions if you only
have one fingerprint.

## 3. "One receipt per slot" needs exactly one legal transition, or a completed retry is unrecordable
`open()`/`close()` with `O_CREAT|O_EXCL` makes the release consume the attempt's single receipt
slot, so the retry's real terminal outcome (prompt + validated artifact) is DROPPED and every
later replay is refused as already-terminal. The fix that keeps exactly-once: allow exactly ONE
replacement, narrowly defined (predecessor = never-submitted release: `not_accepted`, no
`prompt_id`, `submit_count == 0`, not already superseded, full durable identity equal) and require
the incoming record to carry a `prompt_id`. Keep `release_count == 1`, preserve the predecessor
under `supersedes`, append `transitions[]`, write atomically, and guard the read-modify-write with
an `O_CREAT|O_EXCL` sidecar lock + bounded wait so two live closers cannot both win. An
IDEMPOTENT re-close of the *same* outcome+prompt must still return `already_released` (never an
exception), or the frozen exactly-once contract breaks.

## 4. Refuse with an EXISTING typed error when the write-set forbids adding one
A correction whose write-set excludes `errors.py` still needs a typed refusal. Reuse:
wrong identity → `ReservationConflict`; unreadable receipt → `CorruptReservation`;
already-terminal → `AttemptAlreadyTerminal`; concurrent transition → `LeaseConflict`. Tag the
details with a marker (e.g. `supersession=True`) so the caller can recognise a refusal raised from
the new path without catching errors it should propagate.

## 5. A crash is not a negative control
Running the new rows against the byte-exact preimage is the only proof they are non-vacuous — but
the FIRST prefix run crashed inside the measuring helper (`_sha(None)`, `KeyError 'transitions'`)
on the states the pre-fix code produces. A crash tells the reviewer nothing about old behaviour:
make the helpers answer "ABSENT"/tolerate a missing key, catch `BaseException` in the racing
threads, and re-run so every probed row reports a clean FAILED CHECK list.

## 6. Emit in-gate evidence BEFORE the decision, not after
Two successive defects in my own row evidence: the event was recorded after `return
self._replayed_output(...)`, and then after `resolve_durable_prior(...)` which RAISES in the
refusal case. Both times the row lost the proof exactly in the case it measures. Rule: any
evidence line about a decision goes *above* it.

## 7. Windows/MSYS traps hit again this round
* `python.exe -B "$EV/raw/x.py"` becomes `C:\c\Users\...`: interpolating an MSYS-rooted variable
  into a Windows binary's argv breaks. Pass the literal `C:/...` path.
* A guard that hashes `git show HEAD:<path>` through a `text=True` subprocess certifies the wrong
  thing (newline translation). Read git output as BYTES for any hash comparison.
