# S02-T03 Start Prompt

Read TASK and all Required reading. Build a deterministic durable worker around
the approved repository, with explicit lifecycle and no import-time thread. Use
an injectable clock/sleeper/handler registry so retry, heartbeat and race tests
are fast and reliable. Enforce fencing on every worker mutation and fail closed
on missing output validation. Do not touch APIs, migrations or the legacy live
JobService. Preserve channels.json. Run all validation, submit LOG/REPORT, and
stop without commit or roadmap edits.
