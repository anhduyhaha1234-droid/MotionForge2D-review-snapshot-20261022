# Hermes→Hermes lane takeover from an external packet (S12 R6, verified 2026-09-15)

Scenario: an external orchestrator (Codex) hands the user a NEXT_HERMES_PROMPT that says:
transfer a set of existing task IDs onto Hermes owners on a pinned model, run correction
lanes to a terminal state, return a packet. This file is the exact working recipe —
5/5 readiness probes + 5 lane dispatches verified live, zero-write proof included.

## 1. Dispatch mechanics (per lane: readiness → work → verify)

READINESS (new session, strictly non-writing; proves route + tools + clean tree):

```bash
cd <worktree> && EV=<lane-evidence-dir> && hermes chat -q "$(cat "$EV/prompt-readiness.txt")" \
  -m "ocg/deepseek-v4.1-flash" --provider custom -Q --yolo --accept-hooks \
  --pass-session-id --max-turns 30 > "$EV/readiness-console.txt" 2>&1
echo "EXIT=$?" >> "$EV/readiness-console.txt"
```

- Launch via `terminal(background=true, notify_on_complete=true)`; the `cd <worktree>` sets cwd.
- Readiness prompt MUST contain: task id + one-time transfer reason + pinned route
  (model/provider/fallback OFF) + worktree/branch/base, an explicit "ZERO WRITES" ban
  (no file edit, no commit, no pytest, no fetch/pull/push), exactly 7 read-only commands
  (`pwd` / `git rev-parse HEAD` / `git branch --show-current` / `git status --short` /
  `git log --oneline -2` / `ls <allowlist-dir> | head` / `<python> --version`), and the
  required report: session_id (from system prompt) + cwd + raw outputs + `READINESS_OK — không ghi gì`.
- Session id capture: the `-Q` console ends with `session_id: 2026…`; with `--pass-session-id`
  the worker also sees/reports its own id. Grep, don't read the whole console (it contains the
  model's visible thinking — the gateway streams deepseek reasoning into the output; large logs
  are normal, not an error).
- Prove zero-write AFTER readiness: run the pre-captured write_set_guard manifests in verify
  mode with NO `--allow-change` (anything changed = failure). 10/10 VERIFIED on the S12 run.

WORK (resume the exact owner session — new task never gets a second session):

```bash
cd <worktree> && hermes chat -q "$(cat "$EV/prompt-work.txt")" -r <session_id> \
  -m "ocg/deepseek-v4.1-flash" --provider custom -Q --yolo --accept-hooks \
  --pass-session-id --max-turns 400 > "$EV/work-turn1-console.txt" 2>&1
```

- Inline the full work prompt via `$(cat file)` — 7–9KB verified safe through bash→hermes.
  (The <2KB prompt limit applies to PowerShell here-string launchers only.)
- One `-q -r` invocation = ONE turn (up to max-turns tool iterations). If the worker stops with a
  plan instead of work, resume again with `tiếp tục làm việc đi` (1 extra turn per resume).
- Every lane's work prompt carries: required-reading list (rules file, packet sections, its own
  review findings, its acceptance rows), sync-to-wave-base first action, the correction semantics,
  exact test runtime (`python -B -m pytest <nodes> -q -p no:cacheprovider`, short unique basetemp),
  write-set + FORBIDDEN list, evidence dirs, commit-on-local-branch instruction, and the
  bounded-patch-only rule for existing files.

## 2. Heartbeat turn-waker (desktop chat, gateway off)

Cron heartbeats do NOT deliver to desktop chat. To wake yourself roughly every ~19 min while
workers run, arm a background process that sleeps then collects + exits:

```bash
sleep 1140; powershell -NoProfile -ExecutionPolicy Bypass -File heartbeat_collect.ps1; echo done
```

with `notify_on_complete=true`. When the notification fires: poll worker consoles, report status,
re-arm. `heartbeat_collect.ps1` appends to `HEARTBEAT.md`: per-lane console size/mtime/last-line +
count of live workers via
`Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where {$_.CommandLine -match 'hermes' -and $_.CommandLine -match 'chat -q'}`.

## 3. Pitfalls hit this session

- **`shutil.copytree(symlinks=False)` MATERIALIZES symlinks** → a 58-file snapshot appeared as
  116 files and looked like an active writer mid-copy. The tree actually held `*current` SYMLINKS
  pointing at numbered dirs (test-harness pattern). Fix: re-copy with `symlinks=True`, then verify
  (a) sorted relative file list, (b) sorted symlink list, (c) per-file SHA-256. Diagnostic order
  before ever blaming an active writer: `find -newermt "N minutes ago"` (the real quiescence
  signal), `find -type l` (symlink check), process-cmdline scan.
- **Foreign-owned worktree → git "dubious ownership"**: a `.git` written by another Windows user
  (here `CodexSandboxOffline`) makes every git command fail. Use `git -c safe.directory='*' …`
  per-invocation (works for rev-parse/status/commit); NEVER add global config under a takeover task.
- **`git -C /c/msys/path` false "cannot change to" errors** → `cd` into the directory and run git.
- **Bash heredoc eats backslashes**: `replace('\\','/')` inside a `python - <<EOF` block arrives as
  `replace('','/')` → `SyntaxError: unterminated string literal`. Write the script with write_file
  and run the file; drop heredocs for any content containing `\` escapes.
- **Quiescence check needs `-not -path ./.git/*`** to keep `find -newermt` output meaningful, and
  `find -type f` does NOT count symlinked files — never diff `-type f` counts across a
  symlink-preserving vs materializing copy.

## 4. Byte-guard recipe (allow + protected manifests per lane)

```bash
python docs/pm/tools/write_set_guard.py capture --root <worktree> \
  --manifest <ev>/guard-allow-pre.json --path a.py --path b.py ...
python docs/pm/tools/write_set_guard.py verify --root <worktree> \
  --manifest <ev>/guard-allow-pre.json --allow-change a.py --allow-change b.py --report out.json
```

- Two manifests per lane: `guard-allow-pre.json` (the exclusive write-set; verify WITH
  `--allow-change`) and `guard-protected-pre.json` (other lanes' files + models/migrations/
  contracts; verify with NO allow-change). Dir globs expanded by a manager script before capture.
- Untracked critical bytes: byte-copy into the evidence dir + prove SHA equality (existing test
  preimage 385B; a whole untracked `work/` tree with 58 files + 19 symlinks via `symlinks=True`).
- Snapshot once pre-dispatch, verify post-readiness AND post-work; destructive shrink = stop writer.
