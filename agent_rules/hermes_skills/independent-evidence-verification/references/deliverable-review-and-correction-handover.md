# Deliverable review + correction handover (2026-10-08)

Context: MF-DEMO-LONG-01 W7 — a 39,634-frame master completed and the worker
submitted `SELF_REVIEW_PASS_PENDING_CODEX`; the Manager verified it from bytes;
an external review then returned **CHANGES_REQUESTED** (identity/motion) and a
scoped pilot correction was dispatched to the SAME owner. Two reusable pieces:
(1) how to verify a FINISHED media deliverable from bytes; (2) how to hand a
reviewed correction to the same owner without forking ownership or history.

## 1. Verify a finished video master FROM BYTES (never rubber-stamp)

Measured recipe (~2–5 min, all cheap):
- Recompute sha256 + byte size and compare with the claim; verify stream table
  (`ffprobe -show_entries stream=...`), then `-count_frames` on video (must equal
  the plan frame count), then a FULL read/decode of all streams:
  `ffmpeg -v error -i master.mp4 -map 0 -f null -` → rc0 + 0 stderr lines
  (a video-only frame count misses a broken audio stream).
- Audio stream duration vs source: longer = tail kept; a few ms delta is
  container precision, NOT drift. Look for silent `-shortest`-style truncation.
- Contact sheet of head/mid/tail frames (`select='eq(n,0)+eq(n,MID)+eq(n,LAST)',
  tile=3x1`) → inspect with vision: catches black/garbage/looped content and
  gives the reviewer a playable index. This is a SPOT check — never claim
  continuous viewing.
- Counters/JSON schema surprises: `rec[key]` returning None usually means wrong
  nesting, not a missing datum — print keys before concluding anything
  (same family as gate-JSON structure sniffing in `harness-fixture-child-spawn-safety.md` §7).
- Record the claim-vs-measure table in a manager-verify JSON. Your verification
  does NOT clear the review boundary: `QUALITY_ACCEPTED=0` stays until the
  independent reviewer rules on these exact bytes.

## 2. When review returns CHANGES_REQUESTED on the deliverable

- **Worker severity labels are not acceptance.** "MINOR" / "fixed it twice" are
  not waivers. Before fixing content, fix the worker's QA: a gate that PASSES
  the known-bad negative controls of its own output is itself a finding —
  the correction contract must require the gate to REJECT the previously-failed
  cases (keep negative controls + held-out frames in the QA).
- **Same Task/RUN/owner; new correction subdir** (e.g. `D/corrections/<label>_<date>/`).
  The correction's exclusive write-set is that new dir; all history stays frozen
  (no overwrite of old media/anchors/graphs/receipts). Files that MUST be touched
  outside it (state gate, resume state, QA matrix) are patch-only exceptions with
  preimage {sha256, bytes, lines} recorded by the MANAGER before dispatch.
- **Quiesce legacy watchers BEFORE the correction starts.** Stop old watchdogs/
  runners by exact-PID lifecycle (verify pid+creation+name → kill leaf→root) so
  they can't react to the new scope's gate edits and re-render the old full set.
  A parent showing "not found" after its child was killed = the process tree
  collapsing, not a failed kill. The old claim file remains as a dead lease; the
  new scoped runner tombstones it via the existing mechanism — don't hand-delete.
- **Pilot-first scope with stress cases INSIDE it** (wide↔close, wrong role/
  count, 3-person occlusion, entry/exit — the cases the old round failed). Pass
  the pilot, then continue the rest; full re-render and downstream integration
  stay BLOCKED until the reviewer has ruled on the pilot.
- **Deliverables are deliverables.** If the contract calls for a comparison
  video / sheets / manifests, PRODUCE them as required outputs — never offer
  them as an optional extra or ask the user ("want me to also…?"). Likewise,
  inside an authorized task don't pause for per-step user confirmation — report
  status and continue.
- Out-of-scope findings from the previous round keep an explicit
  `OPEN_DEFERRED_FULL` status on the record; pilot success must not close them
  and they must not be silently dropped.
- Correction-dispatch preflight: protected heads/dirty, owner terminal (no live
  chat child process), zero legacy writers, queue empty, frozen input hashes
  re-verified in place, preimage + baseline manifest written, THEN resume the
  same sid with the new packet path and per-round log/receipt names.
