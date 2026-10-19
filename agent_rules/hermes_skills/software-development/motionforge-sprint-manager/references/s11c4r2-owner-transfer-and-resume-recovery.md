# S11-C4-R2 owner transfer + resume recovery (2026-09-05, session 20260905_192221_6da09b)

Session-specific forensics and recovery recipes from the S11-C4-R2 Bootstrap
Transaction lane. Manager: Hermes; worker route `cmc/meta/muse-spark-1.3-contributor`
@ provider `muse` via 9Router `127.0.0.1:20128/v1`.

## 1. Two writers on one worktree — freeze the later, keep the earlier

Parallel evidence roots spawned two competing owners on the SAME worktree
`s11-c4-r2` / branch `codex/s11/c4-r2`:

| Session | First user msg (VN) | Verdict |
|---|---|---|
| `20260905_192221_6da09b` | 19:22:27 | KEEP — owning lane |
| `20260905_192249_150b51` | 19:22:53 | FROZEN — competitor, never `--resume` it |

Detection: query sessions ordered by `started_at` desc, compare first
user-message timestamps — earlier first-msg = owning lane. Confirm tip +
porcelain unmoved (no write collision yet), freeze the competitor, continue
only via `--resume <earlier-sid>`, record both SIDs + first-msg times +
decision in REGISTRY. Never create a third writer to "fix" it. (The frozen
competitor stalled at baseline/RED-repro, 39 msgs — no usable bytes lost.)

## 2. Context-health forensics via state-DB `messages.tool_calls` (read-only)

R1 owner `20260905_043139_01a91f` violated patch-only discipline with heredoc
`python - <<EOF` + `Path.write_text()` on tracked
`app/workflow/qc_checks_handler.py`. Proven without touching the DB:

```python
import sqlite3, hashlib
uri = 'file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro&immutable=1'
con = sqlite3.connect(uri, uri=True, timeout=10)
cur = con.cursor()
for mid in [174611, 174613, 174621, 174940, 174973]:
    payload = (cur.execute(
        'select tool_calls from messages where id=?', (mid,)).fetchone()[0] or '')
    print(mid, hashlib.sha256(payload.encode()).hexdigest(), len(payload))
con.close()
# 174611 09c281f4… 2189 | 174613 ae547c28… 4004 | 174621 b22201a2… 943
# 174940 46522feb… 2354 | 174973 e80354c3… 1241 (assistant text, no write)
```

Notes: there is NO `tool_calls` table — payloads live in
`messages.tool_calls` JSON. Never copy/vacuum/mutate state.db. Record payload
SHA-256 hashes in REGISTRY. Any recurrence = `BLOCKED_CONTEXT_HEALTH`: freeze
the owner immediately, no retry.

## 3. Wrapper dead, session alive — resume, never replace

A `hermes chat --resume` wrapper can exit `DISPATCH_EXIT:143` (tcsetattr
noise) or `RESUME_EXIT:1` after `API call failed after 3 retries: Connection
error` while `sessions.ended_at` stays None — and the worker later commits
(`938d759`) on the exact branch. Procedure: verify liveness via state-DB
(`ended_at is None` + recent tool messages), wait 5 min on transient
connection failure, resume the SAME session ID. Committed state outranks the
wrapper exit code: on any non-zero exit, check tip movement + porcelain +
`show --stat` before judging the lane failed.

## 4. R2 mechanism outcome (for the next reviewer)

Commit `938d759` (parent `e98ccd9`, local only): `_BOOTSTRAP_LOCK =
threading.RLock()` wraps the whole bootstrap transaction; ANY ordinary
Exception → full snapshot restore + `RunQcChecksError(QC_RUN_BOOTSTRAP_CONFLICT)`
with `__cause__`; KI/SystemExit roll back then re-raise unwrapped
(live-probed); 3 new durable subprocess tests (import-RuntimeError,
explicit-RuntimeError, two-live-thread barrier with 60 s bounded joins).
Manager verify: c4r1 file 5 passed / 5.13 s, EXIT 0 — exact match to worker claim.
