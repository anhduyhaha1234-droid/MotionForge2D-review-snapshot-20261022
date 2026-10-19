# Hermes-CLI Worker Dispatch — Proven Patterns (MotionForge PM lane, Windows)

Session-specific detail distilled from running correction rounds C2–C6 and a
post-P00 wait audit for one synthesis-owner session (`20260823_033031_3a5082`)
on the s08-integration worktree. All timestamps +07.

## Dispatch command shape (background, always)

```bash
cd /c/Users/Admin/MotionForge2D-worktrees/s08-integration && \
PROMPT=$(cat /c/Users/Admin/AppData/Local/Temp/<prompt>.txt) && \
"C:/Users/Admin/AppData/Local/Programs/Python/Python311/Scripts/hermes.exe" chat \
  --resume <OWNER_SESSION_ID> -q "$PROMPT" --provider custom --model alpha \
  --yolo --pass-session-id --checkpoints --max-turns 200 --source cli \
  > output/<run>/manager/dispatch-<x>.log 2>&1; echo "EXIT=$?" >> ...dispatch.log
```

- ALWAYS `terminal(background=true, notify_on_complete=true)`. Foreground
  shells get cut (~420s); the child hermes may survive as an orphan but the
  EXIT marker is lost.
- `mkdir -p` the log directory BEFORE dispatching (redirect fails instantly
  otherwise; hermes never starts).
- Append markers per attempt: EXIT / EXIT_R2 / EXIT_R3 so one shared log file
  keeps full lineage.
- Route check before EVERY dispatch: `curl -s http://127.0.0.1:20128/v1/models | grep -c '"alpha"'` must be ≥1.

## Prompt-file pattern

Write the prompt to a file via `write_file` (never inline `$()`, backticks or
complex quoting into `-q`). Two proven locations: `%TEMP%` for scratch prompts,
`output/<run>/<task>/prompt.txt` / `resume-<n>.txt` when the packet should live
with the round's evidence (preferred — survives cleanup, auditable by Codex).
The inline `-q "$(printf '...')"` shape looks convenient but DIES on any
apostrophe in the text (`unexpected EOF while looking for matching quote`,
exit 2) and the worker receives nothing — the failure is silent unless you
grep for your EXIT tag afterward. This bit TWICE in one round (S09-C2, T06B-C2
R2): the failed dispatch printed only `bash: unexpected EOF while looking for
matching \`''` and exit code 2 on the background-process notification; the fix
was writing `resume-r2.txt` via write_file and dispatching with
`$(cat .../resume-r2.txt)` — worked first try. Standing rule: EVERY
resume/correction prompt goes through a prompt file, no exceptions, even when
the text "looks quote-free". After ANY dispatch, grep the log for your unique
EXIT tag (`grep -aoE 'EXIT-R2B=[0-9]+' log`) to confirm the launch actually
happened before telling the user the worker is running. Structure that survived
Codex review six rounds:

1. HARD WORKTREE GUARD (pwd / rev-parse --show-toplevel / branch / DB unset;
   fail → write nothing, report BLOCKED).
2. RESUME CONTEXT: which session this is, verdict driving the round, standing
   rules, EXCLUSIVE write allowlist (exact 9 files), FORBIDDEN list, append-only
   history rule ("preserve C0..Cn verbatim").
3. DO-NOT-REGRESS list of previously verified invariants.
4. Findings F1..Fn with binding wording, exact paths, exact replacement text.
5. MANAGER WILL VERIFY INDEPENDENTLY list (what I will grep after submit).
6. Required REPORT tail: mapping table + write ledger + attestation +
   final line exactly `STATUS: TASK_SUBMITTED`. "Stop after that status line."

## Liveness monitoring loop

```bash
sleep 480; date '+NOW %T'; grep -a 'EXIT=' manager/dispatch-x.log || echo RUNNING; \
ls --time-style=+%T -la synthesis/*.md | awk '{print $6, $7}' | sort | tail -3
```

- Heartbeat ~8min cadence; log mtime frozen >8min ⇒ audit immediately:
  `wmic process where "name='hermes.exe'" get ProcessId,CreationDate,CommandLine`
  (desktop-app Electron processes are NOISE; filter on CommandLine containing
  `chat --resume`).
- `process(action='poll')` returning not_found + no EXIT marker + frozen mtime =
  worker died without marker (backend restart kills child trees mid-run).
- Compaction phase prints "Preflight compression ~230k tokens" — heavy but
  survivable in background mode; do not panic-audit during it unless mtime
  freezes >10min.
- Recovery: wait ≥5 min, re-dispatch SAME owner session SAME route, same prompt
  temp file (keep it until round closes), marker EXIT_Rn. Verify disk state
  between attempts (`sha256sum -c baseline`) to know what the dead attempt
  already wrote — the resume continues from session context, so partial writes
  are usually fine; verify FULL acceptance coverage at submit regardless.

## Independent verification gates (after TASK_SUBMITTED)

Never trust worker REPORT alone. Grep each finding yourself:
- count task rows / IDs (`grep -c '^## S13-T'`), stale-wording sweeps scoped to
  operative sections excluding SUPERSEDED/history lines,
- invariant greps (state vocabularies, single-namespace write-sets, gate wordings,
  risk-ID uniqueness via `grep -oE '\| R1[0-9] \|' | sort | uniq -d`),
- hash diff vs pre-round baseline: exactly the allowlisted files changed, lanes
  byte-identical, HEAD/channels.json unchanged.

Keep verification commands SIMPLE — complex pipelines with `\b`, loops, or
multiple `||` fallbacks trip the terminal guard's blocklist. Split into several
plain greps instead of retrying the original.

## External-change attribution

If HEAD moved mid-round: `git show --stat <sha>` → author/time/files; check
whether the commit touches your lane's outputs and whether either dispatch log
contains git commands. Commit landing BETWEEN two worker attempts with zero
lane paths = external snapshot (user/Codex-side): record attribution in the
manager log, never revert.

## Readiness/wait audits (no-dispatch rounds)

For wait/preflight-only prompts: prove liveness claims with measured deltas
(`S1=$(stat -c %s f); sleep 30; S2=$(stat -c %s f)`) instead of single mtimes;
parse Alembic heads statically via a Python scan of revision/down_revision
(no DB needed); write only the two allowlisted evidence files; end at exactly
the terminal condition string the prompt specifies.
