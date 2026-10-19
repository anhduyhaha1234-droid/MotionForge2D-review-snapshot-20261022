# When a worker truncates repeatedly: stop prescribing, take over the reconnaissance

Measured 2026-09-29 (MF2D CMC correction). A worker lane hit the per-response OUTPUT
token ceiling (`finish_reason='length'`) on **three consecutive resumes** and landed no
new bytes between resume 1 and resume 2. The launcher returned `exit=0` every time, so
nothing in the process signal said "stuck".

This file is the Manager-side companion to
`independent-evidence-verification` →
`references/output-truncation-and-allowlist-grants.md` (which has the lane-side
signature and the size discipline). Read this one when you are the one dispatching.

## 1. Distinguish the two triggers before prescribing anything

| Trigger | Look at the tail | Prescription |
|---|---|---|
| **(a) one oversized `patch`** | `preparing patch…` then repeated truncation at the same point | ≤60 added lines per patch; never re-paste landed code |
| **(b) investigation loop** | `preparing read_file…` / `preparing terminal…` repeated, truncation while composing the *next probe* | size rules **do not help** — the patch was never the problem |

Trigger (b) is the one that survives a "shrink your patches" instruction, because the lane
is spending its output budget reasoning plus exploring, trying to work out something it
does not know (typically: how to build a valid test fixture). Issue the size rule once;
if it truncates again, switch to §2.

## 2. The escalation that actually breaks the loop

Do the lane's open reconnaissance **yourself**, then ship the answers in the packet:

1. **Reproduce the blocker first-hand.** Run the lane's own test file and read the real
   failure text. Do not infer it from the worker's reasoning trace. Measured payoff: the
   lane's *new* tests were genuinely red (`3 failed, 40 passed`, all 40 pre-existing
   green) and the three failures had **three different causes**, each pinned to a
   file+line. That single command replaced hours of worker exploration.
2. **Resolve every ambiguity** the lane was burning budget on and write them as flat
   statements: exact `git status` / `HEAD`, exact test counts, the real list of
   routes/paths, *how to read them correctly*, the cause of each failure, the specific fix
   for each.
3. **Forbid further investigation, as numbered rules.** "No `grep`/`read` to learn more —
   everything needed is in this packet"; "no new probe or script"; restrict allowed verbs
   to patch / test / git; cut the budget (`--max-turns 60`) and say so.
4. **Demand commit-early ordering.** "patch → test → when green, COMMIT IMMEDIATELY as one
   command → then report." Committing a partially-green tree is acceptable **provided**
   the report labels the still-red test honestly. Never let a lane end holding valid
   uncommitted bytes.

## 3. Protect the bytes before you resume again

A lane you must resume repeatedly is exactly where a later destructive write costs the
whole round. Snapshot the uncommitted working files into the run's evidence tree, verify
the hashes match the worktree byte-for-byte, and quote those hashes in the packet so the
worker knows its work is safe and does not rewrite it.

## 4. The cost signature (how to spot it early)

Track **uncached input per completed call** in your usage ledger. A lane in the
investigation loop burns far more input for fewer deliverables than its siblings:

| Lane | calls | uncached input | output | note |
|---|---|---|---|---|
| sibling doing a *larger* job | 61 | 45,730 | 40,989 | normal |
| lane stuck in the loop | 43 | **522,454** | 74,878 | ~11× the uncached/call |

When one lane's uncached-per-call is an order of magnitude above its peers, suspect the
loop rather than a genuinely harder task — and go read its prompt-echo tail.

## 5. Do NOT classify this as a lane failure

Three things this is not:

- **Not a context/recovery event.** No owner transfer, no fresh session. The bytes are
  valid and in scope; the lane simply has not finished. Resuming the same owner is correct.
- **Not a destructive-write incident.** The runtime *refuses* to execute incomplete tool
  arguments, so there is no half-written file and no scope violation. Verify that
  (`py_compile`, `git diff --numstat`, allowlist check) and say so explicitly in the
  incident record — the worker behaved well.
- **Not something to hide.** Record the incident with the measured per-lane cost, and put
  forward forward-looking fixes for the next prompt (split large edits across packets;
  write the line-count rule into the packet; prefer commit-early; consider requesting a
  larger `max_tokens` for the specific lane only — never a global config change).
