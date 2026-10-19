# ETA-only stall → PREP_R_STALL (Codex verdict) + heartbeat delivery on desktop

Proven: S10-C6H continuation, 2026-09-02. Codex issued a dedicated review
(`S10_C6H_PREP_R_STALL_PM_REVIEW_2026-09-02.md`) because the Manager reported
PREP-R progress + ETA without persisting ANY artifact. Verdict:
`AUTHORIZED_TO_DISPATCH / PREP_R_STALL / NOT_APPROVED`.

## The rule that now governs progress reports

Every progress report MUST attach to at least ONE of:

- artifact path
- artifact SHA
- command exit code
- worker session ID
- exact test count
- exact pass/fail count
- registry append

If there is no new evidence, say `NO_PROGRESS` plainly — do NOT describe the
work as still running. An ETA table alone is NOT progress. A "plan + ETA"
reply to a continuation prompt that asks to persist a ledger/matrix is a
STALL: the reviewer will see `output/s10/c6h` containing only the VSS ancestor
copy and no guards/ledger/matrix/launch record, and bounce the sprint.

## The exact stall that happened

- Prompt said: persist `AUTHORITY_SOURCE_LEDGER.md/json` +
  `RETAINED_57_MATRIX.md/json` + guards, THEN dispatch.
- Manager instead: re-verified hashes, explored evidence dirs, reported the
  plan with an ETA column, and stopped before writing the artifacts.
- Codex re-inspected: no C15 dispatch, no registry append, no worker session
  ID, only `vss-ancestor/` existed under `output/s10/c6h`.
- Fix pattern: in the SAME turn as any "PREP-R resolved" claim, run the
  generator/analysis, write the .md + .json artifacts, and self-verify the
  count (57 rows) before reporting. Artifacts first; narrative later.

## Heartbeat delivery on the Hermes DESKTOP (cron does NOT reach the chat)

Symptom (verified 2026-09-02): user asks "heartbeat đâu?" while the cron job
is alive and firing. Truth table:

- `hermes cron list` shows the job with `next_run_at`, `last_status: ok` →
  the job IS running.
- `cronjob list` then shows the job too — but `repeat: forever` must be
  checked via CLI (`hermes cron edit --repeat` or jobs.json), and model via
  `hermes cron edit <id> --model X --provider Y` (cronjob tool has no model
  field).
- BUT: every cron session row in state.db has `chat_id=None`,
  `delivery_obligations` is empty, and `messages.platform_message_id` is NULL
  → the report never reaches the desktop chat. The gateway (Telegram/Discord
  delivery) is a SEPARATE service (`hermes gateway status` = no process) and
  desktop app does NOT pick cron outputs through it.
- Conclusion: on the desktop app, a cron heartbeat banner for the current
  chat is unreliable; the user-approved alternative is a terminal background
  process (Hermes shows its tab/live output in the GUI) OR have the cron
  append a heartbeat file in the worktree.

Diagnostics used (read-only, keep these in evidence):
```python
import sqlite3
con = sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro', uri=True)
con.row_factory = sqlite3.Row
# cron sessions: id starts with 'cron_<jobid>_' ; check chat_id/None + delivered
cur = con.cursor()
for r in cur.execute("SELECT id, source, chat_id, title, started_at FROM sessions WHERE source='cron' ORDER BY started_at DESC LIMIT 10"):
    print(r['id'], r['chat_id'], r['title'])
# delivery proof: platform_message_id NULL => never delivered
cur.execute("SELECT COUNT(*) FROM messages WHERE session_id LIKE 'cron_%' AND platform_message_id IS NOT NULL")
# obligations table exists and is empty when nothing was delivered
[ r[1] for r in cur.execute('PRAGMA table_info(delivery_obligations)') ]
```

## Manager session continuation policy

- Codex said the Manager session `20260902_100134_89bbc9` is resumable and
  MUST be resumed — do NOT create a replacement Manager session. The
  continuation prompt is authoritative: it re-issues RULES_LOADED requirement
  and the action sequence (recheck SHAs → persist ledger/matrix → R-GATE →
  probe route → dispatch single fresh C15 → ... → terminal). A companion
  review naming the exact deterministic disposition (48+9=57, obsolete test,
  duplicate) means PREP-R is UNBLOCKED; the next reply must contain the
  artifacts, not another ETA.
