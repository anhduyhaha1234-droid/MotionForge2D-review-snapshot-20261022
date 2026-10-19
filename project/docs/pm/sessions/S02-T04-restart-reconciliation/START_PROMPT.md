# S02-T04 Start Prompt

Read TASK and all Required reading. Implement a deterministic, bounded
reconciler with no import-time behavior. Use fresh sessions to simulate actual
restart and enforce fencing before requeue/fail/cancel decisions. Resume only
from versioned compatible checkpoints and prove duplicate effects cannot occur.
Do not touch APIs/schema/legacy service. Preserve channels.json. Run all gates,
submit LOG/REPORT, and stop without commit or roadmap edits.
