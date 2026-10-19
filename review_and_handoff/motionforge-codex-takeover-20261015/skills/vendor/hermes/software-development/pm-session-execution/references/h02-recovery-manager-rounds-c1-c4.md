# H02 C2→C4 — multi-round security findings + recovery manager protocol (verified 2026-08-18/19, S08)

Distillation of the S08-H02 correction chain (Codex CHANGES_REQUESTED rounds
C1→C2→C3→C4) for reuse on any future local-API security hardening round and any
full-sprint recovery-manager session.

## 1. Multi-round REPORT integrity + FORCE-STOP trap (bit a real gate 2026-08-19)

- **Heading-level trap:** workers write BOTH `# CORRECTION C1` (single hash) and
  `## CORRECTION ROUND C2` (double hash) in the SAME packet. A manager gate that
  greps only `^## (CORRECTION|Outcome|Manager)` returns **0** on a packet whose
  latest section is single-hash `#`, reading as a FALSE "history wiped" alarm.
  Grep `^#+ (CORRECTION|Recovery|Outcome|Manager|VALIDATION)` (one-or-more
  hashes) and read the section body before declaring the report incomplete.
- **Force-stop inverse:** a worker killed mid-append can leave LOG.md's own new
  entry claiming `REPORT.md appended ... Status: SUBMITTED` while REPORT.md
  genuinely LACKS that section. The handoff will say exactly this ("LOG claims
  REPORT was appended, but that is false"). Verify by READING REPORT.md's tail,
  never by trusting LOG's claim. In the 2026-08-19 recovery, the C1 log line had
  complete-looking validation numbers but REPORT lacked the whole C1 section —
  the worker had been stopped at "Let me append to REPORT.md."

## 2. Codex "CHANGES_REQUESTED on the sprint" round protocol (C3/C4, strict)

- **NEW session per round — do NOT resume the task's old session.** Codex
  explicitly forbade reusing `20260818_020323_151164` for C3/C4 (overrides the
  usual same-session-resume default from earlier rounds).
- **Record run timestamps in the packet, never inferred from a reused session id:**
  `run_started_at_local` (ISO-8601 with +07:00), `run_started_at_utc` (Z),
  `run_finished_at_local/utc`, `elapsed_seconds` (monotonic delta). Capture
  local+UTC+epoch at guard-check time (`date "+%Y-%m-%dT%H:%M:%S%z"`, `date -u`,
  `date +%s`) and hand them to the writer in the START_PROMPT to fill in.
- **FINAL_REPORTED_TO_USER contract:** task is NOT COMPLETE until a user-facing
  final message is sent containing exit code, local finish time +07:00, duration,
  test result, report path — then record `FINAL_REPORTED_TO_USER=true` in
  MANAGER_STATE + tracking. If final delivery fails, remain active and retry.
- **Heartbeat ≤5 min** (not a file written only at end); enforce real deadlines
  (<1 s for a 0.2 s timeout, tight window e.g. <0.30 s). Stop at SPRINT_SUBMITTED,
  never APPROVED/CLOSED, never start S07/S09 while S08 is open.

## 3. Repeatable local-API hardening finding classes (one round each)

- **C2 — preset path containment:** client `body.name` (save) and
  `preset_filename` (apply) reached the filesystem unvalidated. Fix pattern:
  server-owned filename (client name display-only) + strict single-segment
  `.json` + reserved-name 422 BEFORE write + resolved containment under
  `<project>/presets`; apply rejects symlink/junction escape via
  `resolve()` + `is_relative_to`.
- **C3 — probe deadline + preset root + collision:**
  (a) subprocess pipe drain must be CONCURRENT (threads), not sequential
  `readline()` then `stderr` — a blocking read past the deadline reproduces
  "timeout 0.2 s actual 3.0 s";
  (b) preset root itself may be a junction outside the project — anchor BOTH
  unresolved and resolved presets root to the VALIDATED project dir, not just
  `presets_dir.resolve()`;
  (c) distinct names collapsing to one slug (`A!`/`A?` → `a.json`) must not
  silently overwrite — server-owned unique filename or explicit 409.
- **C4 — atomic preset + exact probe bounds:**
  (a) `candidate.exists()` then write-later is a race — use O_CREAT|O_EXCL
  exclusive reservation (retry next suffix on FileExistsError) or UUID filename;
  REAL concurrent 2-thread + barrier test required;
  (b) byte cap must count `len(bytes)` BEFORE decode — `text=True` +
  `len(chunk)` counts decoded chars and lets >1 MiB multibyte pass; capture
  binary, cap first, decode UTF-8/errors=replace only after kill+cap pass;
  (c) every `proc.wait`/`join` uses `max(0, deadline - monotonic())`, else a
  child closing pipes near the deadline gets a second full timeout window.

## 4. Recovery-manager re-verification that closed these rounds

Fresh isolated roots, `-p no:cacheprovider`, shallow basetemps
`C:/Users/Admin/AppData/Local/Temp/<task>-mgr-*`, env `MOTIONFORGE_DATABASE_URL`
unset (echo `[${MOTIONFORGE_DATABASE_URL:-UNSET}]` — the `:-UNSET` guard prevents
a `set -u` abend when echoing an unset var, a real blocker hit on the verify
script). Scope audit via mtime window (`find app tests migrations -newermt ...`)
must show ONLY in-scope files (e.g. projects.py + preset_service.py +
video_probe.py + the security test); frontend must be untouched for backend-only
rounds. Junction/symlink tests must prove they RAN (pytest `-rs` shows 0 skipped
when privilege exists); the log tail must show "3 passed ..., 0 skipped"-style
evidence rather than a silent skip. Protected MAIN verification is byte-size +
SHA-256 via certutil with forward-slash paths.

## 5. Wrong script/launcher hygiene pitfalls (all hit during S08)

- Manager verify scripts: put `.sh` in Temp (outside both repos), `bash -n`
  before launch, and use `${VAR:-UNSET}` not `$VAR` where a var may be unset.
- Watcher vs self-match: `powershell Get-CimInstance ... -match 'watch-s08'`
  matches the *check's own* bash wrapper. Confirm a watcher is really gone by
  matching the script PATH (`watch-*.sh`) and counting 0; plain `-match
  '<task-id>'` returns self-match PIDs that look like live processes.
- Server verification scripts that only ever "ran" a failed attempt (e.g.
  unbound-var abort) produce ghost notifications with exit 1 / empty output —
  the manager must re-read the corrected attempt's log, not the first one.
- Launcher prompt: no double quotes in the body; only the `@"` / `"@`
  here-string delimiters allowed; pre-launch quote-scan
  `sed -n '6,33p' run-*.ps1 | grep -n '"' | grep -v '@"'` must be clean.
