# S12-T06B direct-write escalation (2026-09-07)

Session-specific detail for the "Log growth without tip movement" and
"Committed state outranks the wrapper exit code" bullets in SKILL.md.
Final lane (W7 acceptance, read-only production) sat at 0 bytes
22:48 -> 23:13 reading production context; converged via the ladder below.

## Escalation ladder as observed

1. Status-only nudge ("bao trang thai that") returned delivery-only text,
   WT still pristine — burns a full cycle for zero bytes. Never start with
   a status-only nudge on a stalled lane.
2. Direct-write order (broke the stall same turn): name EXACT files
   (`tests/s12/s12-t06b/conftest.py` + required fixtures,
   `test_scenario_f_4k.py` + required cases), ban further reads
   ("doc production them la vi pham lenh"), demand report-back of
   filenames + line counts. Result: conftest.py 455 lines +
   test_F 192 lines, Manager-verified no-mock. Shape to reuse: exact
   paths + per-file contents + report-back format + read ban.
3. Finish-order nudge (5 files exist + collect OK + ruff clean, worker
   idling): full-suite pytest + LOG/REPORT + diff-check + allowlisted
   commit + TASK_SUBMITTED in ONE turn, explicit KHONG push/merge.

## Failed wrapper can still land the message

A nudge wrapper exited `NUDGE8_EXIT:1`
(`API call failed after 3 retries: Connection error`) — yet the session
`message_count` advanced 76 -> 81 and the worker's `write_file` calls
landed in the WT the same turn. Rule: on ANY non-zero nudge exit, check
session msg count + WT porcelain BEFORE re-sending — re-nudging blindly
double-prompts the worker. (Companion to the "Committed state outranks
the wrapper exit code" bullet: the inverse direction also holds.)

## Zero-model-call Manager pre-gates used on the lane

- `rm -rf tests/s12/s12-t06b/__pycache__` before gates (worker pytest
  runs leave it behind; keeps the tree clean).
- `pytest --collect-only -q` confirmed 12 tests before the full run;
  `ruff check --select F` clean. Both local, zero model calls.
