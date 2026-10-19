# C01 — CHANGES_REQUESTED, independent root review

Candidate gate SHA256 `62c2bfee57f438baa3addb087d2045c68d042dc6d0d70a8bb6fc8b5036f1b8c0`.
Root read actual diff and complete new test module. Fresh root probe suite30/30
and full new module16/16 pass. These close the initial missing-input/type/path
reproductions; a further mechanism-derived consumer case is still open.

## C01-R01 [P1] Bind blend review frame identity to the consumed frame set

Location: R6/scripts/r6_gate.py, require_review, `if blend_name` block.
The patch compares expected.frames only to len(record.frames), then compares
record.frames to range(1,len(record.frames)+1). Both quantities are supplied by
the same review, so neither constrains the consumed blend frame count.

Fresh real gate_assemble with3 manifest frames, valid hashes/full dependency
mapping and matching key review accepts each of these blend records:

- expected.frames=3, frames=[1,2,3] — correct positive.
- expected.frames=1, frames=[1] — should BLOCK, actual ACCEPT.
- expected.frames=4, frames=[1,2,3,4] — should BLOCK, actual ACCEPT.

Evidence: root-review/blend-candidate-01/RESULT.json, saved probe_source.py and
root_probe_blend_frame_identity.py. The probe uses isolated bytes and actual gate
functions; it makes no semantic/decode claim. Impact: the new frame-identity
check permits a review for a different frame set to authorize assembly.

Required correction: compare review expected/count/ordered frame identity to
the actual current bound blend frames (and ensure malformed current frame input
fails closed). Keep exact complete dependency matching and valid producer schema.
Add full/truncated/overlong regression controls through real gate_assemble;
rerun all C01 tests and original root probes. Do not rewrite historical reviews.

## Session Opening Proposal / authorized correction packet

Resume exact owner `/root/motionforge_c01_coder`, gpt-6-sol / max, no fallback.
Same task CODEX-C01-REVIEW-BINDING, WIP1, CPU only. Root verified writer terminal
and preserved candidate bytes; status AUTHORIZED_TO_DISPATCH correction R01.
Write allowlist stays r6_gate.py, test_codex_c01_review_binding.py and c01-worker
evidence. Existing source/test patch-only; preserve candidate preimage before
edit. No other work, GPU, commit, runtime/model/registry/PM/media/review writes.
Self-review plus fresh test output/diff/hash/checkpoint, then stop writing for
root review. No new worker/context required for this focused correction. C02
remains BLOCKED_DEPENDENCY until C01 is independently accepted.

Start: reproduce the3 cases above on candidate01, patch the consumer identity
check, add meaningful regressions and submit a new immutable candidate manifest.
