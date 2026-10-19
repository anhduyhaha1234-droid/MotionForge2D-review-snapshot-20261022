# Duplicate dispatch, stale path carriers, and post-hoc lane verification

Measured 2026-09-24 (MotionForge2D correction round `20260924T1557Z`). Every item below cost a real
round-trip, so keep the checks even when the dispatch "obviously" worked.

## 1. Sweep EVERY absolute path when you copy tooling into a new run root

Starting a fresh run root, I copied `manager/tools/*.py` from the previous round. Two of them carried a
**hard-coded run root** inside the file (`RUN = Path(".../mf-core-tool-delivery-20260924/20260924T1055Z")`).
Consequence: `append_dispatch.py` looked for the packet under the OLD root, printed
`REFUSED: packet missing: <old-root>/manager/packets/<packet>.md`, returned rc=2, and the `&&` chain never
reached the launcher.

Fix and rule:

```bash
# before the first dispatch of a new round, prove no stale root remains in the copied tooling
grep -rn "<previous-run-id>" manager/tools/ ; echo "(empty = clean)"
```

Replace with a byte-exact rewrite (read/write with `newline='\n'`), then re-grep. Do this for the ledger,
the guard, the heartbeat, the watchdog, the reconciler and the session resolver — they are usually all
parameterised the same way.

## 2. A launcher inside `sleep` has NOT refused anything yet

The same round: the relaunch was issued while the first launcher was still inside its `sleep 90` stagger
window. The first launcher then ran, the path fix had already landed, and it created a real session — so the
relaunch produced a **second** session for the same Task ID (one-task-one-session violated), both writing the
same evidence root.

Rules:

* Never conclude "the dispatch failed" from an early poll. Poll the process to actual exit
  (`process(action='poll')` → `status: exited`) before re-issuing, or wait out the declared stagger.
* If the dispatch chain has `sleep N` in it, treat the launcher as *pending*, not *failed*, until `N` plus a
  margin has elapsed and the process has exited.
* Record the launcher pid returned by the background start so the two can be told apart later.

## 3. Detecting and repairing a duplicate dispatch

Detection (fast, read-only):

```python
# sessions created since a cutoff, with the first user message (packet head) as proof of identity
rows = list(cur.execute("SELECT id, started_at FROM sessions WHERE started_at > ?", (cutoff,)))
# then per session: first role='user' message  -> same packet head proves the same Task ID
```

Two sessions matching the same packet head = duplicate. Repair:

1. Keep the **more advanced** one (higher message count / extra artefacts), not the later id.
2. Identify each chain by **process tree**, not by time: `hermes.exe` processes whose command line contains
   the packet name, then their parent/child pids.
3. Stop the duplicate **leaf → root, exact pids one at a time**. Never `taskkill /T`, never a name-wide or
   port-wide kill.
4. Prove zero collateral by diffing the interpreter pid set before/after and printing which pids disappeared:

```powershell
$before=(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } | Select-Object -ExpandProperty ProcessId)
foreach ($procId in @(<leaf>,<mid>,<root>)) { try { Stop-Process -Id $procId -Force -ErrorAction Stop; "stopped $procId" } catch { "already gone $procId" } }
$after=(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } | Select-Object -ExpandProperty ProcessId)
"before=$($before.Count) after=$($after.Count) gone=$(($before | Where-Object { $_ -notin $after }) -join ',')"
```

5. Disclose the side-effects in an incident file: shared write-set window, **colliding log/receipt names**
   (both launchers wrote the same receipt path, so the surviving receipt is not proof of the surviving
   session — the first-user-message match is), and an append-only ledger row for the duplicate rather than
   deleting it.

**PowerShell trap:** `$pid` is a read-only automatic variable — `foreach ($pid in @(1,2))` fails with
`Cannot overwrite variable PID` and, because the loop body never runs, **nothing is killed** while the script
still prints its summary lines. Use `$procId`. Always verify `targets_alive=0` afterwards instead of trusting
the loop's own output.

## 4. When the pre-dispatch manifest could not exist (a brand-new task root)

A new task's write-set is empty at capture time, so the normal before/after guard cannot run. Verify the lane
post-hoc instead — three independent checks:

1. **The lane's own pinned manifest**: re-hash every SHA it recorded and compare (`ok / bad / skipped`).
2. **Tree drift sweep**: every other repo/worktree at its pinned HEAD and porcelain count.
3. **Window sweep**: files touched inside the run window outside the lane's own root — expected to be only
   other *live* lanes, which you name explicitly.

**Trap that makes this vacuous:** my first parser guessed the manifest schema (`files`/`artifacts`/`sha256`
at top level), found nothing, and printed `checked=0 matched=0` — which reads like a pass. A check that
verifies **zero** items is a failed check. Print the producer's own top-level keys first, walk the real
structure, then verify. (Same family as a 100 %/0 % result being a bug signal.)

## 5. Route + vision proof at session start (when the route must be re-proven)

* `/v1/models` on this 9Router build can return the model row with **null** `vision`/`tools`/`reasoning`
  flags while the model actually does all three. Do not report `BLOCKED_MODEL_ROUTE` on null metadata:
  prove capability **behaviourally** — (a) generate a PNG whose nonce and colour order you print to the
  console, read it back through native image input, and compare; (b) issue a real `chat/completions` call with
  a tool schema and assert `finish_reason=tool_calls` plus the exact argument you asked for.
* The router appends `data: [DONE]` to an otherwise ordinary JSON body, so `json.loads` raises
  `Extra data: line 1 column N`. Use `json.JSONDecoder().raw_decode(raw)` (or trim the trailing SSE line) —
  this is a body-shape artefact, not a route failure.
* Resolve the API key from the Hermes config by exact model match, else the first provider pointing at the
  local router; print only `key_present` / `key_len`, never the value. A 401 usually means the lookup picked a
  different provider entry, not that the key is wrong.

## 6. Continuation-packet shape after a flap that landed nothing

125-byte log + `API call failed after 3 retries: HTTP 503 … fetch connect timeout` = transient. After the
mandatory 5-minute wait, resume the same session with a short packet that says: what died, that the tree is
provably untouched (HEAD + porcelain), "treat this as the same round, re-read the original packet — it stays
authoritative for the subcase table and gate order", plus the 20-minute progress line and the
connection-error-vs-deterministic-error split. Do not restate the frozen matrix inside the continuation
packet; point at the file so the two cannot drift apart.
