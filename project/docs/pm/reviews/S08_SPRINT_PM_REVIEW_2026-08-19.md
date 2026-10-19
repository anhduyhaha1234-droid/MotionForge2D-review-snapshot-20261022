# S08 Sprint — Codex PM Review

**Decision:** APPROVED — original S08 Object Discovery and Curation foundation
contract

**Reviewed at:** 2026-08-19T14:23:01+07:00

**Reviewed worktree:** `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`

**Branch / HEAD:** `codex/s08-integration` /
`a43b20da742996bafcb2f9d1ac57b10d3f1a5204`

**Reviewed dirty snapshot:** 173 `git status --short` entries. No
commit/merge/push is authorized by this review.

**Final correction session:** `20260819_105751_c6c6a1`, resumed for C5 and
exited normally.

**Fresh quality run:** `20260819-133623`, 7/7 PASS; Gate 2 reported 1101
passed, 19 skipped and 9 deselected.

## Gate decision

The C5 implementation closes the two remaining H02-C4 findings:

1. stdout/stderr chunks now pass one atomic shared accept/reject decision
   before retention; an over-cap chunk is discarded and no sibling can append
   after abort;
2. child reap and reader joins use one monotonic remaining-deadline budget; the
   fixed five-second cleanup windows were removed.

The focused H02, API, object-correction and golden suites passed. Ruff, mypy,
diff-check, frontend typecheck/lint/build and the fresh baseline passed. The
reviewed protected MAIN state matches its recorded baseline:

- `channels.json` SHA-256
  `DD7AAE26096902EFF74986B36554957D87EB8E60C5E8FF8048064C31655EB555`;
- `data/motionforge.db` 311296 bytes, SHA-256
  `67D5C7736042B9D4E4B7249E611BEA3E85124DF0317FAFE6AAF32405FF79F2E6`;
- SAM 2.1 checkpoint 898083611 bytes, SHA-256
  `2647878D5DFA5098F2F8649825738A9345572BAE2D4350A2468587ECE47DD318`.

No blocking implementation finding remains under the original S08 contract.

## Process finding — non-blocking

The manager modified the worktree `docs/pm/ROADMAP.md` during the C5 writer
window. The writer disclosed it and did not touch that file; the change was
PM/status bookkeeping and did not overlap C5 implementation scope. This does
not invalidate the product evidence, but future manager prompts must prohibit
manager-side filesystem writes while a writer is active. Heartbeat and queue
state should be written only between writer sessions or emitted in chat.

Resident Hermes/watch processes were still visible after completion, although
no reviewed QA port was listening and no writer log continued to advance.
Before the next writer starts, the manager must identify its own watcher PIDs
and stop them without terminating unrelated desktop/application processes.

## Required bridge before S07/S09

Approval closes the original S08 foundation; it does not waive the later
Source-Locked 2D Target Profile. The reviewed role constraint still supports
only `character | prop | other`. Before S07 mapping or S09 renderer work, an
additive bridge must introduce the approved role/layer taxonomy, scene-graph
edges and backward-compatible migration required by
`docs/pm/TARGET_PROFILE_2D_SOURCE_LOCKED.md`.

The next implementation packet is `S08-A01 — Source-Locked 2D Role Taxonomy
Bridge`. It must not rewrite S08 history or weaken existing generation,
correction, CAS, grouping, restart, security or protected-data guarantees.
