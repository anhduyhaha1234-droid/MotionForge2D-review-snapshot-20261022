# S03-T02 Start Prompt

Read TASK.md and every required source in full. Implement the smallest durable
Project repository/API that satisfies the approved contract. Use atomic CAS and
database-enforced/channel-aware validation; do not dual-write legacy project
directories or JSON. Register UUID-constrained durable routes before the legacy
router so literal legacy sub-routes remain reachable. Add a migration only if
the existing schema genuinely cannot enforce the contract, with preservation
evidence from the S03-T01 head. Preserve `channels.json` and all prior evidence.
Run all validation, submit LOG/REPORT, and stop without commit or roadmap edits.
