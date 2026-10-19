# Full-sprint isolated-worktree playbook (S11 T02..T06 — 14 waves / 19 IDs, proven 2026-09-03/04)

Class-level Manager playbook for a full-sprint PM-gated execution where every Task ID
runs in its own git branch + clean worktree from an immutable WAVE_BASE, with one
Git-only integration owner ("S11-INT01") reused for all waves. Everything below was
executed end-to-end and verified.

## 1. Topology and Git protocol

- Canonical integration worktree (e.g. `s11-integration`, branch `codex/s11-integration`)
  stays clean (porcelain 0) the whole sprint. Implementation NEVER happens there.
- Per task: branch `codex/s11/<task-lower>-<token>` created at the CURRENT canonical
  HEAD (the wave base); one clean worktree `s11-<task-lower>-<token>`; prove
  HEAD==base and porcelain=0 before dispatch; one writer per worktree.
- Product worker commits ONLY its exact binding write-set + own
  `docs/pm/sessions/<task>/**`, records SHA/range, writes TASK_SUBMITTED, exits.
  Never push/merge/rebase/reset/clean/stash.
- INT01 (one session, resumed every wave): pre-merge proof porcelain=0 +
  `git ls-remote origin` == local base; serial waves → `git merge --ff-only`; parallel
  waves → ff the first, `git merge --no-ff --no-edit` for siblings (disjoint files →
  zero conflict expected); on conflict `git merge --abort` + BLOCKED_INTEGRATION_CONFLICT,
  never resolve by hand. Push ONLY after the Manager's wave gate on integrated HEAD,
  non-force, then verify remote SHA == local HEAD. That SHA becomes the next wave base.
- Wave gate runs in a DISPOSABLE detached verifier worktree at the integrated HEAD
  (remove it only after its process exited; never remove a task-owner worktree mid-sprint).
- Manager never touches implementation; defects route back to the exact owner session.

## 2. Dispatch mechanics (Hermes CLI on Windows)

- Materialize the task packet BEFORE dispatch with the FULL binding block verbatim
  (all 8 fields: Outcome/Depends-on/Write-set/Forbidden/Tests/Session rule/Acceptance/Trace) —
  never summarize fields away, never change acceptance.
- Baseline manifest of allowed + protected paths (sha256/bytes/lines/mtime), and
  `mkdir` the packet/log dirs BEFORE redirect. Dispatch:
  `hermes chat -q "$(cat prompt.md)" -m <exact-model> --provider custom -Q`
  background=true + notify_on_complete=true, workdir = the task worktree.
- W6-style parallel waves: dispatch each worker in its OWN background terminal call
  (4 for W6, 2 for W9/W12) — all dependency-ready members go out in one turn.
- Worker model policy: exact model/provider, reasoning max REQUESTED, fallback OFF,
  TTFB 900. CLI session rows often carry `reasoning_config=null` → record
  RUNTIME_CONFIG_GAP; never claim max is proven.

## 3. Session-ID safety (a real mistake here)

- Workers killed mid-run never print `session_id`. Recover the id via
  `hermes sessions list --limit 15` (the `--workspace <worktree>` filter does NOT
  match task worktrees — filter by time window and title instead).
- ALWAYS verify the id before `--resume`. Resuming the WRONG session injects another
  task's prompt into that session's history (happened once; kill the stray resume
  immediately — within seconds no message is written, but do not rely on it).
- Resume = same exact session; a `-q` resume creates a new effective row — record
  requested + effective ids.

## 4. Verification loop per task

1. Worker EXIT → `git log --oneline -2`, `git diff --numstat <wave-base>` — zero
   deletions, ONLY allowlist + session docs, porcelain 0 after commit.
2. Fresh focused pytest: short Windows-native basetemp, `-p no:cacheprovider`,
   `env -u MOTIONFORGE_DATABASE_URL`. Re-run binary AC checks (greps, DB probes,
   idempotency, GET-only, hash-match).
3. ruff `--select F` on the task's files; alembic single head unchanged when the task
   must not migrate.
4. Mark `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`, freeze range, INT01 merge, wave gate,
   push, verify remote.

Worker-REPORT hashes are NOT authority: even a precise-looking "after SHA" in a worker
REPORT can be wrong (T02A REPORT claimed models.py after-hash `9dafe988…` while the
committed LF blob was `dae86eea…` — harmless but recorded). Always recompute from
`git show <ref>:<path>` (LF-normalize on Windows) before pinning anything.

## 5. Contract-VALUE verification (the P1 that slipped through)

When the binding plan freezes EXACT enum/string values (reason codes, operation names,
statuses), compare THE VALUES against the binding text — "enums exist and tests pass"
is not enough. T02A shipped `z_order`, `clipping`, `identity`, `flicker`,
`audio_timecode` instead of binding `z_order_error`, `silhouette_clipping`,
`identity_drift`, `temporal_flicker`, plus MISSING `edge_halo`; it passed structural
review and 31 tests, and only broke when W6 detectors hit DB CHECK constraints
(T03D actually got stuck reasoning about the mismatch). Grep the tuple VALUES against
the plan's exact list before verifying any schema task.

## 6. Cascade corrections (enum/schema fix ripples)

A schema/enum fix cascades to every consumer: media manifests, seeds, calibration
fixtures, test fixtures. Route EACH to its exact owner (never fix cross-owner), one
bounded packet per owner, then re-run the CUMULATIVE gate after each merge and expect
the failure count to step down (S11 saw 28 → 26 → 0). Do not reopen downstream
parallel waves until cumulative green on the new base. Fast-forward exact task
branches to current canonical HEAD before each correction resume (writer stopped,
clean tree).

## 7. Pausing a parallel wave for an upstream fix

On a cross-task defect: kill ALL in-flight parallel workers BEFORE they commit wrong
code — `process(action='kill')` per session id, NEVER pkill python (Hermes runs on
python). Fix upstream, ff each task branch to the new canonical HEAD (their untracked
drafts survive; their analysis survives in session history), then resume the exact
sessions with a compact "what changed" note (enum now X, branch now at Y).

## 8. INT01 drift handling (local-ahead authorization)

An integration owner refusing a merge because remote != local is CORRECT behavior.
If the remote lag is the integration owner's OWN previous push (local = remote +
Manager-verified merges), the Manager may explicitly authorize "local-ahead" for that
merge window — document the waiver in the prompt, merge, gate, then push remains a
clean fast-forward. Never waive when the remote could be a foreign push.

INT01 resumes can hit transient HTTP 502/connect-reset (seen on a wave push) — the push
never ran, so there is no half-state. Follow RUNNING_RETRY_WAIT: report, wait 5 minutes,
resume the SAME session with the same exact command, verify ls-remote after. Record the
retry in the wave evidence.

## 9. Static gates: run on INTEGRATED HEAD, not per-branch

mypy/ruff on a task worktree reports errors from OTHER owners' files whose branches
aren't merged yet (mypy follows imports). Fix pattern: each owner verifies only their
own file(s); after ALL corrections merge, run the full scope once on the integrated
HEAD → Success. At sprint exit, a finite mypy matrix (file:line:error) routed to 5
owners in PARALLEL (disjoint files) cleared 9 errors in one round.

## 10. Sprint-exit gate — the 10 items that closed the sprint

1 all 19 acceptance matrices + unique Task/session ownership audit
2 one-command measured acceptance with FRESH run id (outer runner + inner suite + leak assertions)
3 all protected regression files (collect + byte-compare + one fresh full run)
4 impacted older-sprint suite fresh (S10 71/71)
5 alembic single head + REAL round-trip (upgrade→downgrade to the PREVIOUS revision→upgrade; downgrade to head itself is a no-op and proves nothing) + PRAGMA foreign_key_check + integrity_check
6 OpenAPI materialize: zero duplicate operationIds AND zero removed paths vs a saved baseline snapshot
7 ruff F full scope + mypy full scope + pytest collect (duplicate/lost-def audit) + git diff --check
8 frontend tsc + scoped eslint + `next build` producing a BUILD_ID + Playwright specs on task-owned ports/roots
9 ffmpeg/ffprobe survivor scan = 0 (T06C 15s window + final machine scan)
10 protected hashes byte-compare + per-session raw write audit (zero write_file/replace-mode on existing files outside allowlist)
Then: materialize SESSION_REGISTRY + SPRINT_REPORT ONLY with zero active writers, commit as coordination bytes via INT01, final non-force push, verify remote, write NEXT_REVIEW_PACKET.md mapping every ID (session/model/worktree/branch/range/integration SHA/tests/corrections/write-audit) + notes. Terminal is `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW` — never APPROVED/CLOSED.

## 11. Windows/MSYS quirks verified this sprint (recurring, high-value)

- `git -C /c/Users/...` INTERMITTENTLY fails "cannot change to … No such file or
  directory" even though the directory exists (MSYS path resolution state). Symptom
  looked like vanished worktrees — plain `ls`/`cd` proved they existed. Cure: `cd` to
  the parent first, then `git -C <relative-name>`.
- `core.autocrlf=true` → disk sha256 != git blob sha. Compare after
  `hashlib.sha256(open(p,'rb').read().replace(b'\r\n', b'\n'))` (LF-normalize).
- `cmd //c "mklink /J …"` fails silently in git-bash; use
  `powershell -Command "New-Item -ItemType Junction -Path … -Target …"`.
- npm deps sharing: junction node_modules from the read-only archive (lock-hash must
  match) — BUT Next.js Turbopack hard-rejects it ("Symlink … points out of the
  filesystem root") → run `npx next build --webpack`; verify `.next/BUILD_ID` exists.
- `frontend/test-results/.last-run.json` mtime attribution: an mtime BEFORE the sprint
  start = pre-existing artifact, not a leak from the current wave.
- `git worktree remove` must be run in the OWNING repo (`git -C <integration> worktree
  remove <dir>`), not from the parent directory.

## 12. Cadence and honesty (user expectations)

- User asks "ổn ko / tiến độ / bao giờ xong" repeatedly → lead with status, `date`
  anchor, ETA table per wave with buffers (worker-chết + corrections), and report
  drift IMMEDIATELY with reason. Faster-than-baseline is worth stating explicitly.
- Heartbeats ≤20 min; kill-pause events, cascade corrections and drift decisions are
  reported as they happen (user watches actively).
- Only the parallel groups the plan authorizes (W6=4, W9/W12=2). Never invent new pairs.

## 13. After the sprint terminal: the stale-notification flood

Every background `hermes chat` wrapper (original dispatch AND each resume/correction)
fires its own "[IMPORTANT: Background process proc_XXX completed/exit 1 …]" notification
when the bash wrapper finally exits — many land MINUTES TO HOURS after the sprint is
terminal. Do not re-open work on receipt. Classify each by proc id against the live
registry/ledger: if the task/commit/push it belongs to is already verified and merged,
it is cleanup noise — reply "no action" (one line; resist re-verifying the same SHA).
The one useful case: an exit-1 notification whose failure was already handled live
(e.g. 502 retry) — confirm the retry succeeded and move on.