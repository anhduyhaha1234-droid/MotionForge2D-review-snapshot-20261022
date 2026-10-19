# Worker liveness via the state DB + wave dispatch (verified 2026-09-22)

Session: MF-RESKIN-MODEL-UPGRADE wave 1 (MotionForge2D). Three CPU workers dispatched in
parallel, GPU work serialised behind a gate. Every command below was actually run; the numbers
are the measurements, not estimates.

## 1. The empty-log problem

Dispatch used the proven launcher shape:
`hermes -z "<packet text>" -m <model> --pass-session-id [--resume <session>]` with cwd = the
task worktree, stdout+stderr redirected to `NEW_EV/manager/logs/<task>-rN.log`, and a receipt
JSON written on exit (`packet sha256`, argv shape, cwd, started/ended UTC, exit code, duration).

**Six minutes after dispatch, all three logs were 0 bytes**, and they stayed at 0 bytes for the
whole run — while `tool_call_count` in the state DB climbed and the worktrees gained files. The
receipts were written correctly at exit. Conclusion: the redirected stdout is not a progress
channel. Do not diagnose from it, in either direction.

## 2. Read-only liveness query

```bash
python - <<'PY'
import sqlite3, datetime
con = sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro', uri=True)
cur = con.cursor()
for sid in ['<id1>', '<id2>', '<id3>']:
    msgs, tools, end, cwd = cur.execute(
        "SELECT message_count, tool_call_count, ended_at, cwd FROM sessions WHERE id=?", (sid,)).fetchone()
    last = cur.execute("SELECT role, tool_name, substr(content,1,120) FROM messages "
                       "WHERE session_id=? ORDER BY id DESC LIMIT 1", (sid,)).fetchone()
    print(sid, "msgs=", msgs, "tools=", tools, "end=", end, "cwd=", cwd)
    print("   last:", last[0], last[1] or '', str(last[2])[:110].replace('\n', ' '))
PY
```

The `mode=ro` URI is what keeps the DB untouched. Rules forbid mutating the state DB; a plain
`sqlite3.connect(path)` can create WAL/journal side files, so always pass the URI.

Result shape observed for three healthy workers ~6 min in: `msgs=31 tools=18`,
`msgs=32 tools=19`, `msgs=40 tools=28`, `end=None`, last message `role=tool` with a concrete
`tool_name` (`terminal`, `execute_code`, `write_file`). That is liveness: the tool counter is
rising and the newest row is a live tool call.

## 3. The two traps in that same table

- **`ended_at IS NULL` ≠ alive.** Sessions from the previous wave (machine died) sat at NULL
  indefinitely; two of them were 80 and 416 messages deep. `ended_at IS NULL` only means no
  close was recorded.
- **`exit_code == 0` ≠ done.** A resumed owner exited 0 with a **52-byte** log whose entire
  content was `API call failed after 3 retries: Connection error.` — no deliverable, clean exit
  code, receipt present. Always pair the receipt with a count of the artifacts the packet asked
  for, on disk.

## 4. Positively identify the sessions you just created

Do not assume the new ids map to the tasks in dispatch order. Enumerate by time window and read
the packet text back out of the session:

```sql
SELECT id, source, model, started_at, message_count, cwd, parent_session_id
FROM sessions WHERE started_at > <dispatch_epoch> ORDER BY started_at;
```

then

```sql
SELECT substr(content,1,180) FROM messages
WHERE session_id=? AND role='user' ORDER BY id LIMIT 1;
```

The first user message **is** the packet, so the mapping is proven rather than guessed. This
also catches duplicate dispatches and a second manager chat: in this run the query returned
exactly 4 rows — the manager plus the three intended workers.

## 5. Resume lineage when the resumed round produced nothing

- `--resume <id>` minted a **new** session id (parent `…212227_80336a`, 13 messages,
  `end_reason=agent_close`, 52-byte log) → recorded `parent → actual` immediately and used the
  actual id in the registry.
- The resumed worker had no landed bytes from that round, but its *prior* commits
  (`449de4d`, `9e57f3e`) were the frozen preimage for this wave. So the continuation packet was
  scoped to the new findings only (F01 mechanism fix + F06 registry + a handoff artifact),
  **not** a re-send of the earlier required-reading list.
- Before resuming, confirm the parent is terminal and no concurrent writer exists: process scan
  showed exactly two `python.exe` (both Hermes: `desktop`, `serve`), no listener on the engine
  ports, and 1.9 GiB of 12,227 MiB VRAM used at 3 % — i.e. an idle machine.

## 6. Guard ordering: capture, re-verify, THEN dispatch

Per Rules §8.2, before any writer starts:

1. `capture` the protected set → one manifest holding 10 protected repos, the frozen wave-base
   tree (1,837 blobs) and per-file SHA-256 / bytes / lines / mtime.
2. `verify` it immediately, pre-dispatch → `VERIFIED, failures 0` — this proves the guard itself
   works before it is ever used as a gate.
3. Capture each task's own exclusive write-set as a **preimage** with byte snapshots, including
   the untracked bytes of a quarantined lane (a lane you are intentionally NOT resuming but must
   not lose): 14 untracked files / 178,714 B snapshotted, 14/14 snapshot hash-match. Recovery
   evidence only — never written back over the implementation.

A declared protected path that does not exist is recorded as an **honest miss** in the report,
not silently dropped from the manifest.

## 7. 60-second sampler

A background sampler appending one JSON line per tick (per-task log bytes + receipt presence,
worker process count excluding the two Hermes PIDs, GPU used MiB, engine listener ports) exits
when every receipt file exists. It feeds the ≤20-minute heartbeat and supplies the
"8 minutes with no progress → audit" trigger without any LLM call.

## 8. Wave shape that worked

- Three tasks, disjoint exclusive write-sets, all CPU: a correction round on an existing lane
  (mechanism fix + capability-registry correction + a frozen handoff artifact for the next
  lane), a new lane doing source/upstream verification + public-weight download + runtime
  scaffold, and an independent evaluation lane building its checklist/harness against
  **frozen** artifacts only.
- GPU work held back: exactly one heavy GPU job at a time, gated behind the correction lane's
  micro tests + real-server ownership gate, and behind the frozen adapter handoff.
- Every worker packet carried its own stop conditions (do not infer GPU permission; stop rather
  than touch the global CUDA/driver; stop on a license/payment requirement) so the wave cannot
  silently expand.
