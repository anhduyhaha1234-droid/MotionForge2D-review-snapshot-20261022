# S03-T01 Start Prompt

Read TASK and every Required reading item. Implement the smallest durable
Channel repository/API without JSON dual-write or hard delete. Reuse existing
schema where possible; add a migration only if a contract constraint genuinely
requires it, with upgrade-from-S02 preservation evidence. Keep requests
transaction-bounded and DTO/ORM boundaries explicit. Preserve channels.json.
Run all validation, submit LOG/REPORT, and stop without commit/roadmap edits.
