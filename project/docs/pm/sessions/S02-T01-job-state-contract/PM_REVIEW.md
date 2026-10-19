# S02-T01 - PM Review

**Decision:** APPROVED
**Reviewer:** PM/Codex

**Reviewed:** 2026-08-03 18:57 +07:00

## Blocking findings

1. Section 4 declares `failed` and `cancelled` terminal and says terminal rows
   never transition, but the Job transition table allows both states to return
   to `queued`. Choose one coherent retry model; preferably retry creates a new
   Job linked to the terminal predecessor, or define non-terminal attempt state
   without mutating terminal Jobs.
2. JobStep transitions use `cancelling -> cancelled`, but `cancelled` is absent
   from the JobStep state set.
3. Cancel-during-running says outputs published by earlier completed steps remain,
   while the cancelled invariant says no ready output published by the Job may
   exist. Define ownership/visibility semantics consistently: already committed
   checkpoint outputs may remain durable but must not be exposed as final Job
   output; partial/staging outputs must never appear complete.

Add a compact invariant audit covering every transition endpoint and rerun 7/7.

## Final decision

Correction round 1 resolves all three contradictions. Terminal Jobs remain
immutable and retry creates a linked successor; JobStep `cancelled` is declared;
checkpoint/intermediate artifacts remain durable but are never exposed as final
outputs of cancelled/failed Jobs. The endpoint audit is complete.

PM independently verified quality run `20260803-190707`: 7/7 PASS. S02-T02 is
released.
