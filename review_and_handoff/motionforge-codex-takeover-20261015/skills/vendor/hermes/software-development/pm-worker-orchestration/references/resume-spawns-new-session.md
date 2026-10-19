# Resume spawns a NEW session id — C14-T3 proof (2026-09-02)

## Symptom
Dispatched `hermes --resume 20260902_013803_4d5ce5 -z "<prompt>"` for a worker
whose session had `end_reason=agent_close`. Worker ran for ~25 minutes, produced
real files, exited 0 — but querying the OLD session id showed **0 new messages**:

```sql
SELECT count(*) FROM messages WHERE session_id='20260902_013803_4d5ce5' AND id > 146913;
-- → 0  (looks like "worker never ran" — WRONG conclusion)
```

## Root cause
`hermes --resume` of a CLOSED session (end_reason=agent_close / cron_complete /
max-tool-iterations) does not append to that id. It creates a NEW continuation
session. Actual work landed in:

```
20260902_102609_ee5195 | src=desktop | model=comboBAI | parent=None
| st=09-02 10:26 end=09-02 10:51 | agent_close | msgs=197
```

Found via:
```sql
SELECT id, source, display_name, model, parent_session_id, started_at, ended_at,
       end_reason, message_count, tool_call_count
FROM sessions ORDER BY rowid DESC LIMIT 8;
```

## Why the ledger/registry goes stale
Codex PM review said "actual C14 writer is `20260902_013803_4d5ce5`" — true for the
first run — but by the time we resumed, that session had closed, so the resume
landed in `20260902_102609_ee5195`. A ledger naming a session id is a POINTER,
not proof of where future work will land. Always re-query `sessions` after a
resume to bind the REAL continuation id to the dispatch.

## Manager rule distilled
1. After ANY resume dispatch (foreground or background), query
   `SELECT ... FROM sessions ORDER BY rowid DESC LIMIT 8` and record the NEW id
   in the registry/ledger entry.
2. Never use the old id's message count to judge whether the worker ran.
3. If forensic evidence must be tied to a session, use the continuation id,
   not the original (see `hermes-session-forensics`).

## Corollary (proven same session)
`effect_disposition` in the `messages` table was populated on only **1 of
72,096** tool rows → NOT a reliable patch-success signal. Parse the tool
result JSON (`{"success": true, ...}` + `diff` field) instead.
