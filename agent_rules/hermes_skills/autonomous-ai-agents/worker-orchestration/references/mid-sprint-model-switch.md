# Mid-Sprint Worker Model Switch — mechanical procedure

When the user orders ALL workers onto a new model mid-sprint (quota save,
route death, self-test swap), the switch has two halves: stop the OLD model's
consumers and re-pin every FUTURE dispatch path. History files are evidence —
never rewritten.

## 1. Audit live consumers first (before killing anything)

- `ps -ef | grep -iE "watch_24|heartbeat|remind|<old-model>"` — list every
  loop/watchdog/nudge process with PID + cmdline.
- `hermes cron list` — any scheduled job pinned to the old model.
- Already-running writers dispatched under the old binding keep their
  `-m/--provider` cmdline until exit — show cmdlines as proof, do NOT kill
  unless told (their model was correct at dispatch time).

## 2. Kill only the loops, keep the writers

Kill watchdog/nudge/heartbeat PIDs (plain `kill`, escalate `-9` only if a PID
survives), then RE-VERIFY with a second `ps` pass — empty output is the only
proof. Never touch unrelated lanes' workers (verify by cmdline task tag).

## 3. Patch dispatch paths with a backup chain

- `cp watch.sh watch.sh.bak-<old>-<UTC-timestamp>` BEFORE editing.
- Patch ONLY the dispatch line (`-m <new> --provider <p>`) + bump the header
  comment to the next version (v2 → v3 → v4) with user-order timestamp.
- Prompt files for not-yet-dispatched waves: same treatment. Prompts for
  already-dispatched waves stay as historical record.
- History/registry/state files keep the OLD model strings — they describe
  what actually ran. Add ONE append-only errata file (`MODEL_SWITCH.md`):
  who ordered it, timestamp, old→new mapping, what was killed, what was
  re-pinned, current lane state at switch time.

## 4. Restart + verify

- Relaunch the watchdog from the patched script in background; confirm the
  new PID appears in `ps` AND a fresh `WATCH... START` line lands in the log.
  A stale process keeps the OLD code in RAM — file patched ≠ process updated.
- Verify the route exists on the proxy (`/v1/models` grep) BEFORE the first
  dispatch on the new model; a missing route is BLOCKED_MODEL_ROUTE, never a
  silent substitution.
- First dispatch after switch: resume the exact owner session with the new
  `-m/--provider` pin; record the supersession (old→new, timestamp,
  scope=future-dispatches) in the registry.

## 5. Switch-backs

A switch-back is the same procedure in reverse (new backup, next version
number, second errata entry). The backup chain (`*.bak-<model>-<ts>`) makes
every direction auditable without git archaeology.
