# Controller lock, GPU lease, and process identity (measured 2026-10-11, MF-DEMO-LONG-01 R4)

## One controller (filelock)
- Lock at `<run>/manager/locks/controller.lock` (filelock.FileLock, timeout=0,
  poll ~0.05). Meta json `<...>.meta.json` records owner_sid, pid, create_time
  (wmic-format), name, acquired_utc, note, run, released_utc, release_outcome.
- Acquire: on Timeout read the meta and identity-check the holder.
  Holder DEAD => `break_lock()` + re-acquire (explicit supersede — record it).
  Holder ALIVE or UNKNOWN => refuse (UNKNOWN never supersedes; fail closed).
- Refusal path: append ledger row {action: dispatch_refused, reason:
  controller_locked, holder: {...}} and return a distinct rc (=4). No child spawned.
- Release: write released_utc + outcome into the meta BEFORE releasing. OS-level file
  locks self-release on process exit, so a crashed controller cannot deadlock the
  run — the next acquirer supersedes via the meta identity check.
- Dispatch acquires the lock BEFORE any receipt/ledger writes and releases on all
  explicit exit paths (normal end + exception branch).

## GPU lease that survives detached children
- Lease file `<run>/manager/leases/gpu_lease.<invocation_id>.json`; fields: run,
  run_path, owner_sid, invocation_id, job, acquired_utc, status (ACTIVE/RELEASED),
  detached (bool), children [{pid, created(wmic-format), name}], release_attempts[],
  released_utc, release_reason.
- Acquire immediately after the child spawn, using the SAME identity recorded in the
  ledger child_spawned row.
- Release is a PROBE, not a delete: check every child identity AND a render probe
  (Comfy queue empty via HTTP AND no `-B ...runner*.py` process via psutil). If any
  child is ALIVE, any identity is UNKNOWN, the queue is busy, or the probe itself
  fails => keep ACTIVE, set detached=true with a note. "Controller exit must never
  free a busy GPU lease while a detached render child still runs."
- Heartbeat rows carry `controller_lock` (meta + holder ALIVE/DEAD/UNKNOWN) and
  `leases` (ACTIVE leases with per-child ALIVE/DEAD/UNKNOWN) so ownership is visible
  without tailing logs.

## Process identity rules (psutil)
- pid alone is never liveness (PID reuse reads a recycled pid as alive). Use
  pid + create_time (+ name where recorded).
- AccessDenied / unreadable = UNKNOWN, NEVER DEAD. Fail closed: an UNKNOWN child
  keeps the lease; an UNKNOWN holder is not superseded; an UNKNOWN scatter-gather
  result is UNKNOWN evidence, not proof of absence.

## wmic-format create_time compatibility
Legacy ledger rows store wmic CreationDate strings ("20261011130528.956349+420").
New code records the same shape from psutil: `time.localtime(create_time)` +
`.%06d` microseconds + local offset as ±HHMM minutes. Compare with a ±2ms tolerance
on the fractional microseconds (absorbs double-read rounding between producers);
never loosen the datetime part (to the second).

## Windows venv python is a two-process shim
`<venv>/Scripts/python.exe -B script.py` appears as TWO processes with the same
cmdline: the venv launcher (parent) and the base interpreter (child, ppid = launcher).
This explains "two heartbeats" / "duplicate loop" alarms — verify ppid before declaring
a duplicate. Stop/start decisions target the pair, not one pid.

## Stopping a monitor loop without collateral
1. Write the STOP file the loop checks at the top of each tick
   (e.g. `manager/HEARTBEAT_STOP`); wait for the loop's identities to disappear
   (poll psutil ~6s, up to ~4 min for a 120s tick).
2. Remove the STOP file ONLY after exit (else the next loop exits immediately).
3. Census before/after: list matching processes by pid+create_time. If a loop does not
   exit, kill ONLY the exact verified pids leaf→root and diff the interpreter census to
   prove zero collateral. Never kill-all python.
4. Start the replacement, then verify its FIRST tick already carries the new schema
   keys before leaving it unattended.
