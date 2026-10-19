# Hermes-Manager correction lanes (Codex-gated CHANGES_REQUESTED rounds)

Proven pattern from the S13-P00 lane, run C0–C6 on 2026-08-23 (MotionForge2D, integration worktree).

## Per-round load order
1. Read the FULL rules file (`docs/pm/HERMES_AUTOPILOT_RULES.md`) in THIS turn — never from memory. Hash-check against last read; if hash/mtime changed, re-read fully and report drift before anything else.
2. HANDOFF + ROADMAP next; same drift check (they change between rounds as Codex appends live updates).
3. Any prompt-named extra docs (SESSION_PROTOCOL, TARGET_PROFILE, reviews/S*_PM_REVIEW_*.md) in full.
4. Report RULES_LOADED / WORKSPACE_INSTRUCTIONS_LOADED with path + line counts + sections loaded.

## Preflight (before every dispatch)
- HEAD/branch/dirty-count via git; DB-guard env var must be UNSET.
- SHA-256 baseline of ALL artifacts (synthesis + lane files) into `manager/C<n>_hash_baseline.txt` BEFORE dispatch.
- Byte-stability snapshot of the write root two reads ≥3s apart.
- Confirm no concurrent writer owns the write root (process scan by exact command line).
- Liveness evidence for the previous round: EXIT marker + STATUS line in its dispatch log.

## Dispatch
- Resume EXACTLY the owner session:
  `hermes chat --resume <sid> -q "$PROMPT" --provider custom --model alpha --yolo --pass-session-id --checkpoints --max-turns 200 --source cli`
- Always background=true; log to `manager/dispatch-d-c<n>.log`; append `EXIT=$?` (use EXIT_R2/EXIT_R3 markers per attempt).
- Prompt goes in a temp file loaded via `$(cat ...)`; structure: hard guard block first → resume context + do-not-regress list → per-finding binding fixes quoting EXACT wording to delete/add → acceptance checklist for manager verification → final-line requirement `STATUS: TASK_SUBMITTED`.

## Monitoring & recovery
- Heartbeat ≤20min; audit if no log growth for 8min (log size delta, process scan by cmdline, tail).
- Worker death: establish zero-side-effect or partial-write state via synthesis mtimes + `sha256sum -c` baseline; wait ≥5min; resume SAME session SAME route. Backend/app restarts kill child CLI processes — transient, not session loss.
- Large sessions compact ~230k tokens at resume start ("Preflight compression") — normal, wait through it in background mode.

## Independent verification (never trust worker REPORT)
- Grep each finding's old wording (expect 0 operative hits; history mentions OK if labeled) and new wording (expect present in the named file).
- Count task IDs/rows/nodes yourself.
- `sha256sum -c baseline`: expect EXACTLY allowlisted files changed, lane files byte-identical.
- Check terminal state vocabulary; never accept APPROVED/CLOSED from a worker.

## Reporting
- Terminal: `TASK_MANAGER_VERIFIED -> PENDING_CODEX_REVIEW`, production NOT_OPENED.
- Finding→file→verification table with quoted grep evidence.
- External drift (HEAD moved, foreign commit appeared): attribute by timestamp+content vs worker window (grep dispatch log for git commands); record as foreign-owned, never revert.

## Pitfalls
- mkdir the log directory BEFORE redirecting output — bash dies before hermes starts otherwise.
- Guard blocklist trips on complex one-liner payloads (`\b` regexes, for-loops): split into several simple grep commands instead of retrying the blocked shape.
- Stale revision labels in verdict blocks are a recurring P2 across rounds — sweep "current revision" wording each round.
- Keep per-round prompts in Temp with `s13p00_cN_prompt.txt` naming; delete after verify.
