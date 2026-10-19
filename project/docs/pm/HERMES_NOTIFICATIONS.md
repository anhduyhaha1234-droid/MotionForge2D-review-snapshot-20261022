# Hermes Autopilot — Notifications and User Actions

Session names:

- `MF-Autopilot-Main`: overall roadmap coordinator.
- `MF-A-Close-S03`: backend summary and Sprint S03 closure.
- `MF-A-UI-S04`: Sprint S04 UI shell workstream.
- `MF-B-Characters-S06`: Sprint S06 Character Library worktree.

Hermes stays quiet for routine coding, tests, corrections, and commits. Only
the following messages require attention:

| Notification | Meaning | What the user should do |
|---|---|---|
| `✅ PHASE_DONE A/B/C/D` | A whole phase passed integration and 7/7 | Nothing; Autopilot continues |
| `🟡 DECISION_NEEDED Sxx-Txx` | A real product/UX/authority choice is missing | Reply in that Hermes session with the requested choice |
| `🛑 AUTOPILOT_BLOCKED Sxx-Txx` | Three recovery attempts failed or hardware/service is unavailable | Open `MF-Autopilot-Main`, read the blocker, then ask Codex: `Kiểm tra blocker Autopilot và tiếp tục` |
| `🏁 PROJECT_READY_FOR_CODEX_REVIEW` | All roadmap/final evidence is ready | Ask Codex: `Review tổng thể MotionForge2D và bàn giao bản sử dụng được` |

The durable latest notification is mirrored at
`output/HERMES_AUTOPILOT_NOTIFICATION.md`. A missing notification means work is
continuing normally; it is not a failure.

During an active long-running manager session, "quiet" is limited by the
liveness policy: the manager must post a concise progress heartbeat at least
every 30 minutes. If no progress is confirmed for 20 minutes while runnable
work remains, it must recover or emit `AUTOPILOT_BLOCKED`; it must never wait
for a user message to wake it.

For `DECISION_NEEDED`, `AUTOPILOT_BLOCKED`, and final readiness, Autopilot also
opens a persistent Windows popup that stays visible until acknowledged. Popup
implementation: `scripts/show-hermes-autopilot-popup.ps1`.
