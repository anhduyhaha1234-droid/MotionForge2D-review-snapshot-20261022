# Parallel Verify + Pre-stage Under Serial Gates

Manager-side throughput patterns for PM-gated correction sprints (class-level;
proven in S11-C2 Wave C2-A; no session-specific IDs below).

## 1. Parallelize independent read-only verification

When 2+ lanes are SUBMITTED on disjoint worktrees/branches, run the Manager
re-verify (independent pytest reruns on committed bytes, diff-check, allowlist
check) CONCURRENTLY — one background terminal per lane, each appending its own
raw log. Typical saving vs serial: 40–60 min on lanes with minute-scale suites.

Hard rule: only parallelize READ-ONLY work. Never run a verify pytest against
a scope a worker is still writing; re-check `git status --porcelain` + tip SHA
in that worktree immediately before launching each verify.

## 2. Read-only pre-staging under a serial gate

When a downstream lane is serial-blocked (e.g. consumer lane must wait for an
integration merge + combined gate), the owner may start early READ-ONLY
research: read current bytes, study the prior/misrouted commits, derive the
contract independently. The pre-stage prompt must explicitly forbid writes and
name the exact gate event that unlocks writing. No history rewrite to hide a
prior misroute — record retained-vs-replaced bytes in LOG/REPORT.

## 3. Integration merge-state check before further merges

In the canonical worktree, prove lane membership with
`git merge-base --is-ancestor <lane-SHA> HEAD` per lane, and read the INT tip
commit message for BLOCKED markers (e.g. `BLOCKED_GATE_RED` with failing
suite names) before merging anything else. A tip that already contains the
lanes but carries a red gate means: resolve the gate first, do NOT stack more
merges on top.

## 4. Session-identity verification via state DB (read-only)

When two owner sessions share a timestamp/wave (same-start-time lookalikes),
confirm exact identity queriably: Hermes state DB, `messages` table filtered
by `session_id`, first `user` message header names the Task ID. Never dispatch
to a lookalike session; freeze the wrong-owner session out of that task's
write set and disclose the incident in the registry.

Duplicate dispatch onto the SAME worktree/branch (proven S11-C4-R2): two
parallel evidence roots each dispatched their own owner within one minute onto
one worktree/branch. Detect via first-`user`-message timestamps + prompt
headers (earlier dispatch = kept lane, later = frozen competitor), plus
tip/porcelain proving no write collision yet. Resolution: keep exactly one
writer, freeze the other permanently, append the incident with both session
ids to REGISTRY.md, and continue ONLY via `--resume` of the kept owner.
Wrapper `DISPATCH_EXIT:143` (bash `tcsetattr: Inappropriate ioctl for device`
noise) is NOT worker death while the session row shows `ended_at None` —
resume the same owner per the connection-retry rule, never create a
replacement writer.

## 5. Date-anchored progress reporting

Every status answer: run `date` first, then lead with a table of remaining
legs with Expected/Worst columns. State explicitly what runs in parallel vs
what is serial-forced, name the single riskiest lane + its failure mode, and
notify the user in the SAME turn a worker EXITs or a gate flips (never verify
silently and report later).
