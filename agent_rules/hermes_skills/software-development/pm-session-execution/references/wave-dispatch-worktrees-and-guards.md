# Wave dispatch: per-task worktrees, before-guards, monitor lanes, submit verification

Recipes proven across a 28-task DAG delivery (Hermes-as-Manager, one Hermes session per task, 2 worker slots + Manager = cap 3). Use alongside `hermes-cli-dispatch-and-verify.md`.

## 1. Per-task worktree bases (DAG dependencies must be PHYSICAL in the tree)

- One worktree per task: `<delivery-root>/<TASK_ID>`, branch `codex/<task>-<date>`, created with `git worktree add -b <branch> <path> <base-sha>`.
- **Base = the task's dependency OUTPUT commit, not the wave start SHA** — a task whose packet imports/patches a dependency's module must see that module's committed bytes. Chaining `wave-1 output -> task 11 -> task 12 -> task 13` worked precisely because each base was the predecessor's commit.
- **Multiple dependencies -> transport merge**: create the worktree on the LAST dependency's commit, then merge the other dependency commit in:
  `git merge --no-ff <other-dep-commit> -m "transport <TASK> (<what>) into the <NEW_TASK> base"`
  Verify `git status --porcelain | wc -l == 0` after the merge, record the merged base SHA in the dispatch ledger, and tell the worker in the packet that BOTH dependencies are already in the tree.
- Keep the layer plan honest: only dispatch tasks whose dependencies are terminal + verified; leave a slot idle (with a recorded reason) rather than starting a blocked task.

## 2. Before-guard: measure before you write the packet

Run at dispatch time, one JSON per task under `manager/guards/<TASK>_before.json`:

- `git rev-parse HEAD`, `git status --porcelain` count (must be 0), `python -m alembic heads` if the repo uses migrations.
- For EVERY write-set path: `exists` + `bytes` + `sha256` (files) — the NEW vs EXISTING split decides the packet's instruction:
  - NEW file -> whole-file generation allowed.
  - EXISTING file -> "patch bounded with preimage" (never overwrite); the worker's commit must show a delta, not a rewrite.
- Baseline test command + observed counts (e.g. `pytest tests/product_delivery/test_<task>.py` and the broad suite).
- These numbers go INTO the launch packet, so the worker never guesses.

**Migration-head pitfall (measured)**: a regex scan of `down_revision` in `migrations/versions/*.py` produced a STALE head pin and the worker had to re-measure. Always resolve with `python -m alembic heads` (sole head) and pin `down_revision` to that value; tell the worker to re-confirm with the same command before writing the new migration.

## 3. Launch packet skeleton (beyond the task packet)

Task packet = scope/acceptance authority. The Manager launch wrapper adds: model pin (`--provider custom -m <model>`, fallback OFF), worktree path + base SHA + porcelain, evidence root, "read RULES + packet originals first / report RULES_LOADED", the guard measurements, proof-measured facts the worker must NOT re-discover (paths of research docs, which node classes are unregistered, known provider quirks), gate order (micro -> acceptance/negative -> focused -> ONE broad), retry policy (stop clean on API error; resume same session after >=5 min), payload budget (<=200 chars per command, write files with scripts), tool-call budget.

## 4. Monitor lane lifecycle (long runs)

- A monitor script holds a hardcoded `LANES = {name: session_id}` read at process start. **Editing the file does NOT change a running instance** — to track new lanes, copy the script to a new name (new log file) and launch a fresh process; let the old one finish its cycle.
- When a lane reaches terminal, its rows keep printing (frozen counts) and can trip `STALL_AUDIT` — treat stall flags as meaningful only for lanes that are still supposed to be running.
- Resolve "which session is which task" by first user message: `SELECT session_id, (SELECT content FROM messages m WHERE m.session_id=s.id AND m.role='user' ORDER BY m.id LIMIT 1)`. Do it once per launch and pin the mapping in the ledger; never infer from launch order.

## 5. Verifying a worker submission (before dispatching the next task)

1. `git show --stat --format=%h <commit>` — file list MUST equal the allowlist (note size and +/-).
2. `git status --porcelain` in the task worktree — clean.
3. `git branch -r --contains HEAD | wc -l` == 0 (worker did not push).
4. Independently re-run the task's focused tests on the committed bytes yourself (do not accept the worker's transcript alone).
5. Reconcile claimed vs actual: a worker's "gate 16/16" counts gate ROWS, not tests — compare with the real pytest counts you measured.
6. Record: commit sha, parent, scope check, your independent test result, disclosures (worker self-declared crashes/reconstructions), and whether a correction round was needed.

## 6. When the provider flaps mid-run

Signature: process exits 0 but the log ends in HTTP 502/503, or a 422 on a tool message; artifacts on disk are complete but the final docs/ledger were never written. Fix: wait >=5 min, then relaunch a SMALL docs-only packet on the SAME session (`--resume` keeps the session id for `hermes chat`), telling the worker to avoid large tool payloads. Do not re-run the heavy work.
