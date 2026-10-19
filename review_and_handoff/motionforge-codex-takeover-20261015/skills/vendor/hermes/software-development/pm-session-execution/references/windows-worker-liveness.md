# Windows worker liveness & safe-stop (Hermes CLI workers on MSYS/git-bash)

Lessons from a real misdiagnosis (S09-T01, 2026-08-23): manager declared the
writer dead at 01:05; the writer was alive and reached TASK_SUBMITTED at 04:13,
writing production files the manager had already labeled "orphaned drift".

## Liveness proof hierarchy (never conclude death from one signal)

1. `ps aux` in git-bash does NOT map Windows PIDs reliably. After a bash
   wrapper subshell exits, its hermes.exe/python.exe child keeps running but
   becomes invisible or shows wrong PIDs in MSYS ps. NEVER conclude "worker
   died" from ps absence alone.
2. Best single source: a wmic scan for the worker's unique marker in the command
   line (e.g. grep the embedded session id: `wmic process where "CommandLine like '%--resume 20260823_033031_3a5082%'" get ProcessId,Name`) —
   proves liveness AND ownership in one shot. Include the marker in every
   worker prompt to make this possible. Note (2026-08-23): bare
   `tasklist //FI "IMAGENAME eq hermes.exe"` fails under MSYS flag-mangling
   (`//FI` rejected) and desktop-app Electron children ALSO run as hermes.exe —
   filter by CommandLine (`chat --resume`), never by exe name alone.
3. Log-size sampling: take `stat -c%s <dispatch.log>` twice, >=30s apart
   (preferably across minutes). delta>0 ⇒ alive. A single frozen reading
   proves nothing — output buffering can pause writes for a long time.
4. Only treat a worker as dead after (2)+(3) agree AND the manager-side
   background-process registry agrees (`process poll` → not_found is strong
   death evidence when the proc id was dispatched minutes earlier — but see
   the third-death-mode note in manager-liveness-and-worker-process-audit.md:
   registry wipe happens when the MANAGER backend itself restarts, which kills
   the whole worker tree at once).

## No stdin channel on `-q` workers

- `process(action='submit')` against a `chat -q … --yolo` worker fails with
  "stdin not available": you CANNOT inject a mid-flight scope correction or
  safe-stop into an already-running non-interactive worker.
- Workarounds: (a) bake a stop-poll convention into the prompt up front
  ("before each write phase, check `<task-dir>/STOP`; if present, wrap up as
  SUBMITTED_BLOCKED_SCOPE immediately"); or (b) accept wait-for-natural-exit
  while preserving all writes for attribution.
- Never `kill` a process whose ownership is not proven via cmdline; broad
  python kills can kill Hermes itself.

## Superseded contract discovered mid-flight (Codex re-scope)

1. Do NOT reset/restore/delete anything the out-of-scope worker wrote — hash
   intersection files before/after and keep everything for Codex attribution.
2. Mark the task `BLOCKED_DEPENDENCY_PENDING_CODEX_SCOPE_REVIEW` in the
   registry; do NOT run manager verification on the superseded product even if
   its gates are green (verification would legitimize the old contract).
3. New lanes may only dispatch once the snapshot is provably stable: owning
   proc absent via cmdline check AND log size static across spaced samples.
4. Shared worktree caveat: sibling sprint lanes (e.g. S11 corrections) write
   app/tests too — attribute mtimes via cmdline evidence, not assumption.

## Manager adversarial spot-checks (cheap, high yield)

Verify worker REPORT claims against the repo directly: grep the cited
file:symbol, open the cited line range, confirm "0 matches" claims yourself,
and require raw evidence (env_guard fields, RAW_RESULTS.json) for any
"measured" number. Workers self-report; only rerun-or-grep counts.

## Terminal command shapes that survive the guard

- Keep commands small and sequential; very long compound `sleep … && for … do
  if grep …` chains can trip the hardline parser blocklist — split them.
- Prefer wmic/tasklist/grep via bash; PowerShell one-liners can stall
  unattended awaiting consent and burn minutes.
