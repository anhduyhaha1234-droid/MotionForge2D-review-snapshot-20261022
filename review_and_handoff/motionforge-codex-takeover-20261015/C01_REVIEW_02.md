# C01 — APPROVED, exact candidate02 only

Independent root review, 16 October 2026 (UTC+7). Coding owner
`/root/motionforge_c01_coder` is terminal; source/test writes have stopped.
Quality Run ID: `C01-ROOT-CANDIDATE02`.

Approved gate SHA256:
`4c3f7a7213f7761b7f5cbf53d7257bfd1c893e7f50d04d4ffda38a2e3cf13996`.
Approved test SHA256:
`e2744bc198bc91fe71ce4b2afafb9682e427c17c7ac0c1207b3a7643dbf2d330`.
Candidate manifest SHA256:
`261a7d9b20c046c3eee3ede50fac250992a084aec856583c5e0992397e2a6850`.
MAIN HEAD remains `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`;
INTEGRATION HEAD remains `a52fca897906fd61a088016dd802718fdf06d217`.
The changed run artifacts are external to those Git checkouts, so exact file
hashes and byte snapshots, rather than a commit claim, identify this approval.

## Finding closure and independent evidence

C01-R01 is closed. The gate derives the required ordered frame IDs from the
current blend manifest, checks canonical names and typed entries before indexing,
then requires both the review's expected count and reviewed IDs to match it.
The actual assembly gate first verifies the current manifest frame hashes.
Complete typed dependency-map comparison and exact artifact/review identity
remain enforced. The actual assembler calls the gate before copying/encoding.

Root inspected the final production source, candidate diffs and regression test
structure, verified all 15 pinned manifest entries, and freshly ran, in order:

- `root_probe_review_binding.py --scripts R6/scripts --out root-review/candidate-02`:
  30/30 passed, exit 0. Receipt: `root-review/candidate-02/RESULT.json`.
- `root_probe_blend_frame_identity.py --scripts R6/scripts --out root-review/blend-candidate-02`:
  3/3 passed, exit 0. Full three-frame review accepts; truncated and overlong
  self-consistent reviews block through real `gate_assemble`.
- Full `R6/tests/test_codex_c01_review_binding.py -v`, with isolated fixture root:
  17/17 passed, exit 0. Raw output: `root-review/FOCUSED_CANDIDATE_02.txt`.
- `root-review/PROTECTED_SCOPE_CHECK_02.json`: 32 preimages compared; only the
  gate and three already-authorized root PM documents differ from takeover.
  Source/master/comparison media hashes unchanged; assembler/common unchanged;
  no duplicate definitions in gate/test; no unexpected tracked scope drift.

The worker's historical record-shape survey and two safe F02 bodies are additional
self-review evidence; they are not counted as root's independent reproductions.
No new unresolved finding remains within the C01 contract.

## Limits and dependency decision

This approves C01 review binding only. Parent `MF-DEMO-LONG-01` remains
`NOT_APPROVED`; semantic quality, current underlying dependency verification,
complete producer dependency capture/reuse, event/child outcomes and media gates
remain open. No render, full-source scope, UI integration or Git publication is
authorized by this approval.

## Session Opening Proposal / exact next packet

New Task ID `CODEX-C02A-DEPENDENCY-VERIFICATION`; fresh compact session
`/root/motionforge_c02a_coder`, `gpt-6-sol` / `max`, no fallback. C01 is complete,
so this is a real dependency scope transition, not a quota retry or reset.
Old owner is terminal, C01 evidence is frozen, context health is sufficient and
the complete next prompt is `TASK_C02A.md`. Require `C02A_PREFLIGHT.json: ok=true`
before writes. Maximum safe wave is one CPU-only writer, no GPU job.

Exclusive write-set: `R6/scripts/r6_cache.py`, necessary dependency validation
wiring in `R6/scripts/r6_gate.py`, new
`R6/tests/test_codex_c02a_dependency_verification.py`, fixture-only bounded edits
to the C01 test module without weakening its assertions, and `OUT/c02a-worker/**`.
All other paths are protected. Self-review then terminal submission, followed by
independent root review. The complete packet defines the finite acceptance matrix.
Root authorizes this dispatch under the user's coding instruction and rules §0.11
once the fresh preflight passes. C02B producer/reuse changes remain blocked.
