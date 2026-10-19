# Lane dispatch recipes

Concrete shapes that survived a multi-round fleet run (8 lanes, 36 ledger rows, 4 upstream flaps, 1 duplicate-session
incident). Adapt paths/ids; keep the FIELDS — the fields are what make the evidence auditable.

## 1. Dispatch-ledger row schema (append-only JSONL)

```json
{
  "at_utc": "2026-09-26T10:35:12+00:00",
  "task": "MF-P1-QC-EVIDENCE",
  "round": "roundD-finish",
  "parent_session": "20260924_230630_4b16f4",
  "actual_session": "20260925_002014_42c623",
  "actual_session_proven_by": "first-user-message == packet head (read-only state.db, newest match)",
  "grade": "PROVEN",
  "packet": "manager/packets/<LANE>-<round>.md",
  "packet_sha256": "…", "packet_bytes": 3560,
  "worktree": "C:/…/<tree>",
  "log": "manager/logs/<LANE>-<round>.log",
  "receipt": "manager/receipts/<LANE>-<round>.json",
  "outcome": "TASK_SUBMITTED — commit abc123 (parent intact, N files, allowlist only, porcelain 0) …",
  "note": "free text; use it for incidents (STOPPED_OVER_CAP, DIED_ON_502_FLAP, receipt/log name collision)"
}
```

Append the row at DISPATCH time with `actual_session: null, grade: "PENDING"`, then append a second row when the lane lands
(never rewrite the first). Compute `packet_sha256` from disk at write time so the row cannot disagree with the file.

## 2. Read-only session resolver (the only trustworthy parent→actual mapping)

```python
con = sqlite3.connect(f"file:{Path(DB).as_posix()}?mode=ro", uri=True, timeout=25)
cur = con.cursor()
since = datetime(2026, 9, 24, 17, 0, tzinfo=timezone.utc).timestamp()
sessions = list(cur.execute("SELECT id, started_at FROM sessions WHERE started_at > ? ORDER BY started_at", (since,)))
for s in sessions:                                    # list() FIRST — a reused cursor truncates the scan
    first = list(cur.execute("SELECT content FROM messages WHERE session_id=? AND role='user' ORDER BY id LIMIT 1", (s["id"],)))
    fm = " ".join(str(first[0][0]).split())[:60] if first and first[0][0] else ""
    tag = next((k for k, h in PACKET_HEADS.items() if h[:45] == fm[:45]), "-")
    print(s["id"], tag, fm)
```

`PACKET_HEADS` = `{task: " ".join(open(packet).read().split())[:60]}`. Grade PROVEN only on a match; a merged packet or a
hand-written session can only be INFERRED/CONFIRMED.

## 3. Dispatch shape + stagger

```bash
cd <run>/manager && python tools/append_dispatch.py <TASK> <round> manager/packets/<pkt>.md <PARENT_ID_OR_NEW> \
    "<tree>" manager/logs/<name>.log manager/receipts/<name>.json \
 && python tools/mfv1_launch.py "<abs pkt>" "<tree>" "<abs log>" "<abs receipt>" --resume <PARENT_ID>
# NEW session (no --resume). Stagger 45 s between lanes; cap concurrent upstream streams (evidence: flaps at 4).
```

Wrap in `terminal(background=True, notify_on_complete=True)`; a launcher that is still sleeping has not failed yet.

## 4. Cap-enforcement ledger row (when a 4th stream slipped through)

```json
{"task": "S12-LC3-QA", "round": "roundD", "actual_session": "…-STOPPED", "grade": "STOPPED_OVER_CAP",
 "actual_session_proven_by": "NOT a task result: launched, then stopped ~30 s in to keep the stream cap at 3 "
   "(chains alive: CONTRACT, QC-finish, COMFY-resume2). Zero collateral (python.exe 10->8, only chain pids gone).",
 "note": "QUEUED for re-dispatch on the first freed slot; packet is written and hashed, nothing else needed"}
```

Stop order: children → hermes → parent, one at a time, by exact PID. In PowerShell use `$procId` (`$pid` is read-only).

## 5. Duplicate-dispatch incident record (write it, don't hide it)

Heading: what happened · the two sessions with first-message + start time · which one was KEPT · how the other was stopped
(exact pids, leaf→root) · collateral proof · disclosed side-effects (shared write-set window, colliding receipt/log names)
· prevention rule for next round. File it in the run's `manager/` root and reference it from the ledger row.

## 6. Guard / manifest checklist (before the first writer)

- [ ] Capture a **preflight baseline** (per-tree HEAD + porcelain + mtime) into `manager/audit/*.json` — the guard reads it.
- [ ] Capture a **per-lane write-set manifest** (path, sha256, bytes, logical lines, mtime, tracked/dirty) via the project's
      canonical guard tool; lanes whose write-set is empty at capture time get RE-captured after their first round.
- [ ] Re-run the guard after every terminal, and expect **live lanes to appear as drift** — list the excluded lanes in the
      verification note.
- [ ] Treat a guard run that dies with `FileNotFoundError` on a manifest as a TOOLING gap, not a lane failure.

## 7. Timing accounting (never conflate the two numbers)

```python
total = sum(json.load(open(r))["duration_seconds"] for r in receipts)      # aggregate worker time (overlaps)
elapsed = max(ended) - min(started)                                        # program wall time
print(f"aggregate worker time {total:.0f}s over {len(receipts)} receipts; program elapsed {elapsed:.0f}s")
```

Also list which receipts died on flaps (log < 200 B) so the aggregate is not read as productive work.

## 8. Lane packet skeleton (fields that made packets work)

`Task ID` · **Owner session to RESUME (exact id)** · model route pinned exactly (provider/model/base/api/thinking/fallback)
· tree+branch+**baseline HEAD measured fresh** · **literal evidence root with "no nested NEW folder"** · write-set
allowlist + explicit forbidden paths · the finding bundle verbatim (file:line + measured before/after) · frozen subcase
table with expected binary outcomes · gate order · byte-guard/patch-only rules · no-push/no-rebase · terminal state +
budget · connection-error policy (stop, print the log line, wait 5 minutes, resume same owner/model/scope).
