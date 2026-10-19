# Closing a correction round: dispositions a reviewer can re-derive

Measured 2026-09-24 on a review → correction → re-verify round (7 lanes, findings R1–R11, an 11-row
closure matrix, ~8 h of dispatch wall time). This is the Manager-side half: how a finding moves (or
does not move) from `OPEN` to a claim a reviewer can independently re-run.

## The closure loop

1. The reviewer files **numbered findings**, each with file:line and a reproduction, not a verdict.
2. Map every finding to the lane/session that owns those bytes. A correction **resumes the exact
   owner** — never a new session, never a different lane "because it is faster".
3. **Freeze a finite matrix BEFORE dispatch**: per-finding sub-rows, each with an explicit *expected
   AFTER* (typed refusal, or counts like `total POST = 1`), a top-level row ceiling, and the gate
   order `writer terminal → byte guard → micro repro → matrix 100 % → focused/static → affected
   module → integration gate`. Freeze it as its own hashed document so a reviewer can see the target
   was set before the code changed (and that a probe filename was not invented after the fact).
4. Dispatch/resume, byte-guard on terminal, **then re-run the reviewer's own repro yourself**.
5. Keep one tracker doc (finding → lane → commit → evidence path → state) and ship it with the packet
   instead of re-summarising from memory at the end.

## Dispositions: three shapes, and the vocabulary is the deliverable

| disposition | meaning | what it must carry |
|---|---|---|
| **CORRECTED (manager-verified)** | the decisive case now behaves as required, **re-run by the Manager** | your own run's concrete outcome: `POST 2 → 1`, "all 5 builders raise `QC_EVIDENCE_MISSING` with the render deleted", "foreign requester refuses, owner still re-attaches" |
| **SUBMITTED (lane evidence)** | mechanism plausible/verified, but content quality is the reviewer's judgement | say **which half** you checked and which you accepted (a docs/delta judgement, an identity-coverage choice, an E2E claim needing a live server) |
| **OPEN / RUNNING / BLOCKED** | not closed | name the exact missing artifact (`PENDING_FROZEN_CANDIDATE`, missing producer) — never round it into closure |

Hard rules learned the hard way:

- A row may **never** move on "the worker says it passes" — only on a command you ran in that round.
- A green broad run never waives an open binary row. Report `n PASS + m OPEN = n+m`; never an aggregate
  percentage that hides the open rows.
- A behaviour change made *by* the fix (e.g. replay of a terminal `attempt_id` now refuses where it
  used to re-run) is a **finding-level disclosure**, not a footnote — the reviewer decides whether to
  accept it.

## State your verification boundary — in every lane's verification doc

Readers cannot tell "I ran this" from "I read this" unless you say so. Per lane, write:

1. **what you executed yourself** (commands, and the numbers they printed), and
2. **what you accepted from the lane's own evidence**, naming the raw file, and
3. **coverage limits**, stated plainly: "two full-resolution comparisons + one 20-frame sheet; no
   playback, no audio"; "the seeded fixture has no cast pin, so my probe cannot exercise the positive
   path — that path is the lane's `raw/q01_*.json`, accepted as evidence, not re-derived by me".

Rounding up ("reviewed the clip") is worse than a smaller honest claim: it is the one thing a
reviewer cannot re-derive from the artifacts.

## What "good AFTER evidence" looks like (all measured in one round)

- The reviewer's probe re-run on the fixed bytes reproduces **every** required outcome, and the
  worker's `probe_after.json` is **field-for-field identical to your own run** (9/9), while the
  worker's `probe_before.json` is field-for-field identical to the reviewer's **published** JSON (9/9).
- Accepts become **typed refusals**: `MF_..._CORRUPT_RESERVATION`, `..._RESERVATION_CONFLICT`,
  `MediaEngineRefusal`, `ValidationError`, `QC_EVIDENCE_MISSING` — with the positive control still
  working (a correction that refuses *everything* is not a fix).
- **Counts, not prose**: POST / artifact / marker / receipt numbers before → after per subcase.
- The suite re-run at the frozen HEAD matches the lane's number exactly (68/68, 91/91, 131/131,
  a 47-pass/3-skip gate run) — and where a pass count was measured *before* the last hunk, re-anchor it.
- Container-level facts for media: an ffprobe tag matrix (4/4 carried, plus a stripped negative
  control that reads `unknown`), and sentinel ledgers re-hashed by you (bytes + sha256) with
  `bytes_appended = 0`.
- Recorded fixtures re-executed: rc 4/4 + verdict 4/4, and any stdout-digest difference **named**
  (live pid fields), never waived and never graded as failure.

## Generate the packet's numbers; do not type them

Build the closure tables (timings, exit codes, packet hashes, receipts) from the dispatcher's
**receipts + append-only ledger** with a script and paste the script's output. This round's generated
timing table (11 receipts / 28,833.5 s) is also what exposed three flap receipts whose logs were
124–125 B — a fact that would have been lost in a hand-written summary.

## Do not invent approval dependencies — and do not blur aggregate time with elapsed time

A closing packet is read as a claim about the world; two Manager-side habits get filed as findings
against the *Manager*, not the lanes (measured: a re-review filed exactly this as its P2).

**1. An authorization you already hold is not a gate.** The previous round's report and
session-opening proposal said the bounded media experiment "awaits a Codex decision" and that the
QA chain "awaits the INT freeze", presented as approval dependencies. The governing prompt had in
fact already granted both: the experiment was authorised conditional on the Manager's **own**
prerequisites (verified freeze → isolated lightweight server proof → ledger isolation → one lease),
and the QA execution after the integration freeze. The reviewer's finding: **avoidable idle work
caused by reporting**, i.e. the work sat still waiting for a permission nobody needed to give.

Classify every block before writing the word "blocked" / "awaiting":

| Class | Example | How to write it |
|---|---|---|
| **my own unmet prerequisite** | freeze not yet recorded, server proof not run, lease not held | list the prerequisite and *start it*; never phrase it as awaiting approval |
| **a real artifact dependency** | lane B needs lane A's frozen commit | name the artifact + owner + the condition that clears it |
| **a genuine external gate** | sprint approval, a scope decision only the reviewer can make | name the exact decision and its authority |

When you do hold a conditional grant, **quote it** in the packet ("the prompt grants I1/I2 after a
Manager-verified freeze; no separate approval is required") so a later reader cannot mistake a
self-clearing prerequisite for a missing permission — and so a reviewer does not have to reconstruct
the authorization history to see the lane was not idle by design.

**2. Aggregate ≠ elapsed.** Summing launcher receipts gives *aggregate worker duration* (this round:
11 receipts / 28,833.5 s). Program elapsed is `last finish − first start`, and any parallel wave makes
the two numbers very different. Label both explicitly, keep `server / load / wait / inference / encode`
separate where the lane measured them, and include the **last continuations** (finish runs, flap
resumes) in the accounting — an accounting that stops at the main rounds understates the run and will
be read as sloppy rather than conservative.

## Cross-references

- Probe re-run mechanics, interface-delta disclosure, volatile-stdout triage:
  `independent-evidence-verification` → `references/probe-reruns-and-interface-deltas.md`.
- Receipt-aware stall detection, finish packets, lane-name normalisation, flap resume:
  `background-worker-orchestration` → `references/monitoring-and-finish-runs.md`,
  `references/flap-resume-cycle.md`, `references/success-signals-and-phantoms.md`.
