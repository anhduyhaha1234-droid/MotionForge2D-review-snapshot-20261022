# S03-T02 - PM Review

**Decision:** APPROVED
**Reviewer:** PM/Codex

## Review result

Approved after architecture correction round 1 and PM correction round 2.
The durable API remains isolated at `/api/v2/projects`; legacy filesystem
routes are unchanged. Review round 2 found and closed three blockers:

1. Generic PATCH formerly allowed `status=archived` and restore from archived,
   violating the archive timestamp invariant. Both directions are now blocked.
2. Channel validation and Project assignment were two statements without a
   SQLite writer reservation. Project CREATE/PATCH now start
   `BEGIN IMMEDIATE` before validation, making validation plus assignment one
   serialized write boundary against concurrent Channel archive.
3. The archive race test did not force both calls past the initial active-row
   read. A repository hook now makes the winner/loser interleaving explicit and
   verifies the loser's fresh `populate_existing` re-read.

## Independent verification

- Project suite: 29 passed.
- Channel + Project + persistence bootstrap: 89 passed.
- Legacy API/import regression: 46 passed.
- Focused Ruff and mypy: pass.
- Full mandatory quality baseline run `20260804-041036`: 7/7 PASS, exit 0.
- `channels.json` SHA256 remains
  `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`.

## Automation disclosure

Hermes authored the submitted implementation. During correction round 2, two
same-lineage MAX resumes and one minimal recovery session repeatedly timed out
at the local inference proxy after reading the packet but before producing an
edit. PM applied only the three reviewed corrections above, recorded them here,
and independently reran the complete acceptance evidence before approval.
