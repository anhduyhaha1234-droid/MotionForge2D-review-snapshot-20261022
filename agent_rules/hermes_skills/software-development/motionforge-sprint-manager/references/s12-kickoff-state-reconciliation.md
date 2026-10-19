# S12 kickoff: STATE_RECONCILIATION + new-sprint bootstrap (2026-09-07)

## Snapshot docs go stale; live user authority wins

At S12 kickoff, `CODEX_PM_HANDOFF.md` / `ROADMAP.md` still said "S12
planning-only, blocked", while the user explicitly ordered S12 CODING with a
binding contract. Procedure, now standard for any snapshot-vs-order conflict:

1. Record `STATE_RECONCILIATION` in the new REGISTRY: exception engineering
   per explicit user authority, NOT a retroactive prior-sprint CLOSED claim;
   prior evidence roots untouched; no beta/release claim until Codex confirms
   predecessor gates plus the new sprint review.
2. Proceed on the live order. Never let a stale snapshot veto an explicit
   user order, and never rewrite the snapshot — annotate the divergence.

## New-sprint bootstrap from a frozen HEAD

1. Verify canonical HEAD clean + local==remote (porcelain 0, ls-remote equal).
2. New integration worktree + branch (e.g. `codex/s12-integration`) at the
   exact HEAD, verified clean after creation.
3. Per-task worktree + branch (`codex/s12/<task>-<runid>`) at the same HEAD;
   audit pre-existing path/branch first, never overwrite or duplicate owners.
4. Evidence root `s12/<runid>/`; baseline manifest distinguishing
   `NEW-YET-ABSENT` (greenfield allowlist files) from `EXISTS`+SHA-256
   (protected files); guard capture per protected file before dispatch.
5. REGISTRY pinning wave-base, DAG/waves, session registry; first task
   `AUTHORIZED_TO_DISPATCH`, the rest auto-activate per DAG after the
   Manager gate — no per-task user re-prompt.
6. One NEW owner session per new Task ID (never reuse prior-sprint owners);
   dispatch pins `-m` model + `--provider` explicitly; record the new
   session ID back into the REGISTRY the same turn.

## Liveness audit to answer "is any worker still running?"

Three independent signals, all read-only (verified 2026-09-07: machine clean):

1. Hermes-tracked background processes (`process list`) — history rows with
   `exited` status are not live workers.
2. OS process table (`tasklist` / `wmic` on Windows): `hermes desktop` and
   `hermes serve` are infra, not workers; unrelated user scripts
   (e.g. anything under Downloads) are out of scope — attribute by
   command line before alarming.
3. State-DB per-session max message id + timestamp (`mode=ro&immutable=1`):
   every prior owner terminal (`TASK_SUBMITTED`, no new messages since its
   submit time) plus zero worker PIDs ⇒ report machine-clean. A UI spinner
   after that is stale display — ask for a screenshot of where it shows.
