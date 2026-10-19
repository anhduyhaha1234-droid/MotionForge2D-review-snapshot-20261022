# Duplicate sessions & dispatch chains — one task, two live writers

Measured 2026-09-24 during a long Manager round (Hermes desktop, Windows, `hermes -z` workers
launched from background chains). This file covers three failure modes that all look like
"the lane failed" but are actually harness/plumbing defects, plus the exact remediation.

## 1. The `sleep N && append && launch` trap — a refusal on one process does not clear the queue

Dispatch chains are built as one shell line so the ledger row and the launch cannot drift apart:

```
python tools/append_dispatch.py <args…> \
  && python tools/mfv1_launch.py <packet> <tree> <log> <receipt> --resume <owner>
```

With a stagger they become `sleep 45 && …` / `sleep 90 && …`. When `append_dispatch` refuses
(here: a copied tool still pointed at the **previous run's** directory, so it printed
`REFUSED: packet missing: …<old-run>/manager/packets/<packet>.md` and exited 2), the manager:

1. polled **one** of the three launcher handles, saw the refusal and exit 2,
2. fixed the stale path in all copied tools,
3. re-dispatched — including the lane whose first launcher had *already been rejected* (it had not).

But that first launcher was still inside its own `sleep 90` window when the fix landed. It woke
up afterwards, ran successfully, and created a **real session** — so the re-dispatch produced a
**second** session running the same packet. Net state: **two live writers on one write-set**.

Rules:

- A background chain that has **not exited** has decided nothing. Poll each handle to completion
  (or explicitly reason about its `sleep` offset) before concluding it failed.
- After repairing a dispatch blocker, enumerate every still-pending launcher and cancel or
  reconcile it **before** re-dispatching.
- Prove **one task = one session at the SESSION level**, not the process level: read the read-only
  state DB and list sessions whose *first user message* matches the packet head (one packet per
  lane makes that a proof, see `pm-worker-orchestration`). Two different chains for the same packet
  is exactly what the process table will show and it will not look wrong.

## 2. Remediation: stop the extra chain by PID, prove zero collateral

Once a duplicate is confirmed, keep the session with the most progress and stop the other chain
**leaf → root, exact pids only** — never `taskkill /T`, never a name-wide or port-wide kill:

```powershell
$before = (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } |
           Select-Object -ExpandProperty ProcessId)
foreach ($procId in @(<leaf>, <middle>, <root>)) {          # NOT $pid — see below
  try   { Stop-Process -Id $procId -Force -ErrorAction Stop; "stopped $procId" }
  catch { "already gone $procId" }
}
Start-Sleep -Seconds 3
$after = (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } |
          Select-Object -ExpandProperty ProcessId)
"pids_gone=" + (($before | Where-Object { $_ -notin $after }) -join ',')
```

Evidence to record: `python.exe` count before/after, `pids_gone` (**must equal the target set and
nothing else**), and a re-listing of surviving `hermes -z` chains showing the intended lane count
(here exactly 3). That pid-set diff is what makes "zero collateral" a measurement instead of a claim.

**PowerShell gotcha:** `$pid` is a read-only automatic variable. `foreach ($pid in …)` fails with
`Cannot overwrite variable PID because it is read-only or constant.` and the loop body never runs —
so a kill script can appear to run while stopping nothing. Use `$procId`.

## 3. Disclose the receipt/log NAME COLLISION

Both launches of the same packet wrote the **same** log and receipt paths. The surviving receipt
therefore belongs to whichever launcher finished last and **cannot identify the surviving session**.
Say that explicitly in the ledger row and the incident note; tie the canonical session to the
first-user-message match instead, and keep the duplicate row in the append-only ledger rather than
deleting it.

Also disclose the write-set risk window (how long two writers had the same write-set) and what the
tree/evidence root contained when the duplicate was stopped — in the measured case the evidence root
was still empty (both sessions were reading their packets), so there were no interleaved bytes; the
round still re-hashed the root at the end to attribute any file it could not explain.

## 4. Copied tooling carries hard-coded absolute paths

Copying a proven `manager/tools/*.py` set into a new run root is the fast path — and it silently
carries the old run's absolute paths in eight files at once (ledger path, run root constant, lane
registry). Sweep before the first dispatch:

```bash
grep -rn "<previous-run-id>" tools/          # expect hits in the copied set
# replace every hit, then re-grep for zero
grep -rn "<previous-run-id>" tools/ | head   # must be empty
```

Treat a lane refusal that names a path as **a tooling bug first**: diff the tool's expectations
against the CURRENT run root before you touch the lane or record a failure. Keep the sweep result in
the evidence root so the next round's reviewer can see the tools were re-parameterised deliberately.
