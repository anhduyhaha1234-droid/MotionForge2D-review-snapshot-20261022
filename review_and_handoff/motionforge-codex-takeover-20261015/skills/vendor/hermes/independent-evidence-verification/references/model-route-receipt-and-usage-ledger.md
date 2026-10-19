# Proving the model route + keeping a usage ledger honest (verified 2026-09-29)

Context: a Manager session had to prove that every lane really ran the newly
mandated route (`custom / cmc/deepseek/deepseek-v4.1-flash`, fallback OFF) and
had to keep a per-task usage ledger — while resuming long-lived worker sessions
that had previously run a DIFFERENT model (`ocg/deepseek-v4.1-flash`).

## 1. The launch flag is not the receipt; the log line is

`hermes chat -m <model> --provider <p>` plus a receipt JSON recording `model`
proves only what you *asked for*. The per-request receipt lives in
`~/AppData/Local/hermes/logs/agent.log`:

```
2026-09-29 16:29:10,109 INFO [<session>] agent.conversation_loop: API call #2:
  model=cmc/deepseek/deepseek-v4.1-flash provider=custom base_url=.../v1
  in=235570 out=640 total=236210 latency=28.6s cache=215936/235570 (92%)
```

Parse THAT line. It carries the resolved model, provider, input/output and cache
read — i.e. model proof *and* usage in one row.

Fallback-OFF proof is a separate command: `hermes fallback list` →
`No fallback providers configured`. Also confirm the model id exists in
`GET <base_url>/models` before blaming the tooling.

### The resume trap — filter by MODEL, not just session id

A resumed session's log contains **both rounds**. In the observed run the same
`session_id` had 100 earlier calls on `ocg/deepseek-v4.1-flash` and 60 new calls
on `cmc/deepseek/deepseek-v4.1-flash`. Therefore:

- `grep "<session_id>" agent.log` **mixes two models** and cannot prove route
  compliance for the new round.
- Assert per-round: filter by `model=`, then check the newest `API call #`
  numbering restarted at `#1` for the new model. A call-number restart plus the
  new model string is the signature of a genuine resume-time route switch.
- Record both counts (`ocg` round N calls, `cmc` round M calls) in the ledger —
  do not silently drop the pre-switch round, and do not credit it to the new
  route.

## 2. Usage-ledger dedupe: `(session, api_call_no)` is NOT a key

The first ledger used `seen = (session_id, api_call_no)`. Because a resume
restarts call numbering at `#1`, **every row of the second round collided with
round one and was silently dropped** — the tool reported `rows_added=22` once and
`rows_added=0` afterwards while the log clearly held new `cmc/...` requests.

Fix — make the key per-request, not per-(session, ordinal):

```python
key = (session_id, api_call_no, model, at_local)   # at_local = the log timestamp
```

Then **reconcile ledger against raw log** as a hard gate — this is the check that
catches the class of bug:

```
truth  = distinct (sid, n, model, ts) parsed straight from agent.log
have   = rows accumulated in ledger v1 + v2
assert missing == 0 and extra == 0, and print per-session counts
```

Observed reconciliation after the fix: `truth 120 have 120 missing 0 extra 0`
(per-session `59` + `61`), where before the fix it was `truth 119 have 105
missing 15`. A silent dedupe bug looks exactly like "the router stopped logging"
— reconcile before concluding anything about the provider.

Keep the buggy ledger file. Never rewrite history: emit `usage-ledger.v2.jsonl`
next to v1 (v1 is the evidence of the defect), point the tool at v2, and say in
the report which file is authoritative.

## 3. Two tooling traps met while building the monitor/ledger

**(a) `Path("")` is `Path(".")` — and `read_bytes('.')` raises
`PermissionError: [Errno 13] Permission denied: '.'`.** A launcher receipt written
BEFORE the child exits has no `log` key yet; `Path(receipt.get("log", ""))` then
points at the current directory and the monitor dies with a permission error that
reads like a filesystem problem instead of "still running". Guard explicitly:

```python
if log is None or str(log) in ("", "."):
    return {"exists": False, "reason": "receipt has no log path yet (still running)"}
```

**(b) Probe the DB schema before writing a monitor query.** A monitor selecting
`job.status` died with `no such column: status` — the real column was `state`.
One `PRAGMA table_info(job)` costs nothing; guessing the column and reading the
traceback as "the DB is wrong" wastes a cycle. Read the DB `mode=ro`: a monitor
must never mutate the artifact it is observing.

## 4. Keep monitor scripts LLM-free

The whole point of the heartbeat loop is to *not* spend a model call per poll.
The monitor reads local state only (app `/health`, Comfy `/queue` + `/prompt`,
read-only DB counts, lane log size + tail markers) and appends one row per
`HEARTBEAT.jsonl`. "Still running with no new output" produces a heartbeat FILE,
not a conversation turn.
