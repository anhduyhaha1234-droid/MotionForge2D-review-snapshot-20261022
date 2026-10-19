# S08 writer launch, model verification, and no-writer audit

Session-verified (2026-08-19/20, S08-A02-T01-R1 DeepSeek Core Recovery) techniques
for launching a spawned MotionForge2D writer, confirming the mandated model
actually ran, and proving no other writer is active before you touch the worktree.

## 1. Mandated writer model/reasoning — what actually enforces them

- `hermes chat --help` has NO `--reasoning` flag. "reasoning max" is NOT a CLI
  argument. It comes from config in `C:\Users\Admin\AppData\Local\hermes\config.yaml`:
  - `agent.reasoning_overrides: {ocg/deepseek-v4-flash: max, ...}`
  - `agent.reasoning_effort: max`
- Provider `custom` on this machine = local 9Router at
  `http://127.0.0.1:20128/v1` (provider name "9Router") with models
  `ocg/muse-spark-1.2-contributor`, `ocg/deepseek-v4-flash`, `ocg/mimo-v2.5`.
- Launch a DeepSeek writer with (background=true + notify_on_complete=true):
  ```
  cd <worktree> && unset MOTIONFORGE_DATABASE_URL && \
  hermes chat -q "Your cwd for ALL commands MUST be <worktree> — run pwd first. $(cat START_PROMPT.md)" \
    --provider custom --model ocg/deepseek-v4-flash \
    --max-turns 500 --pass-session-id --accept-hooks --yolo --source tool
  ```
- To CONFIRM the writer really launched under the mandated model, do NOT grep
  the tee'd log — it only echoes the query/prompt dump. Read
  `C:\Users\Admin\AppData\Local\hermes\state.db` (SQLite; read-only URI works):
  ```
  SELECT id, source, model, started_at, cwd, git_branch
  FROM sessions ORDER BY started_at DESC LIMIT 8;
  ```
  The newest `source='tool'` row is the launched writer; `model` must equal
  `ocg/deepseek-v4-flash`. Record that session id (`YYYYMMDD_HHMMSS_<rand>`)
  in MANAGER_STATE.md + REPORT.md as the verifiable handle.
- `--pass-session-id` injects the session id into the agent's system prompt (so
  the writer can self-report), but it is NOT printed at startup — the state.db
  query above is the fast verifiable source. `hermes serve` / Hermes desktop
  wrappers (python.exe + hermes.exe) show up in state.db too; filter by
  `source='tool'` (spawned) vs `source='cli'`/desktop.

## 2. No-writer audit (prove no competing writer BEFORE you write)

Process listing alone is not proof. `wmic process where "CommandLine like
'%hermes%chat%'..."` matches its OWN wmic invocation → self-match noise and
multi-hundred-KB truncated output. Instead:

1. `tasklist | grep -iE "codex|claude|hermes|python|node"` → identify the
   long-lived infrastructure: Hermes desktop + `hermes serve` (with its buddy
   python.exe wrapper), codex app-server + sandboxes, 9router node (cli.js +
   custom-server.js), playwright cliDaemon. None of these are code writers.
2. Dump real command lines + creation dates via a `.ps1` FILE (inline bash→
   PowerShell quoting mangles `$_` / `\` / paths):
   ```
   Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('codex.exe','hermes.exe','python.exe','node.exe') } |
     Select-Object ProcessId,Name,CreationDate,@{N='Cmd';E={$_.CommandLine}}
   ```
   Long-lived infra predates your session → not your writer.
3. mtime scan the worktree for any file touched in the last ~hour (exclude
   `.git`, `node_modules`, `__pycache__`, `.next`, your own evidence dir):
   ```
   Get-ChildItem <worktree> -Recurse -File | Where-Object {
     $_.LastWriteTime -gt (Get-Date).AddMinutes(-55) -and
     $_.FullName -notmatch '\\.git\\|node_modules|pycache|\\.next\\' } |
     Sort-Object LastWriteTime -Descending | Select -First 40
   ```
   All hits must be your own recovery deliverables + the pre-existing draft
   files. Any file you did not create = a writer mid-write.
- The MANAGER_STATE "modified by sibling subagent 'YYYYMMDD_...'" warning on
  write is benign when the modifier is your own recovery lane or a pre-recovery
  write — verify via mtime + content, do not panic-kill infrastructure.

## 3. Rewriting an unreleased migration revision — safety check first

The untrusted draft left `a0b1c2d3e4f5` as alembic HEAD. Rewriting it is allowed
ONLY because no DB has applied it. Prove that read-only BEFORE rewriting:

- `python -m alembic heads` → shows the draft as current head.
- Scan every local `*.db` — MAIN `C:\Users\Admin\MotionForge2D\data\motionforge.db`
  and `output/**/migration.db` — read-only with a SQLite URI, reading
  `alembic_version`:
  ```
  con = sqlite3.connect('file:' + os.path.abspath(db) + '?mode=ro', uri=True)
  con.execute('SELECT version_num FROM alembic_version').fetchall()
  ```
  Observed 2026-08: MAIN at `d5e6f7a8b9c0` (zero structural tables), old sprint
  output DBs at `e7f8a9b0c1d2` / `f6a7b8c9d0e1` — none at `a0b1c2d3e4f5`.
  Result: safe to rewrite the migration, but ONLY test on fresh temp DBs; NEVER
  `alembic upgrade/downgrade` MAIN or any user DB.

## 4. Recovery bookkeeping that must happen before writer launch

- Preflight evidence file under `output/<task>-r<round>/preflight-evidence.md`
  capturing: worktree/branch/HEAD/status count, MAIN HEAD match, QA ports free,
  no-active-writer proof, current draft file SHA-256s vs the reviewed hashes,
  independent reproduction of the F1-type failure.
- Append the `ABORTED_UNTRUSTED_PARTIAL_OUTPUT` incident to the prior task's
  REPORT.md (append-only; existing history untouched) before creating the
  recovery packet.
- Recovery packet dir `docs/pm/sessions/<TASK>-R1-<name>/` with TASK/START_PROMPT/
  LOG/REPORT; TASK.md carries the Codex findings (F1..F11) as NORMATIVE, an exact
  R1 allowlist, and a "forbidden in R1 (R2 owns)" list so the writer cannot
  silently widen scope (no schema/router/frontend in a persistence-recovery round).
