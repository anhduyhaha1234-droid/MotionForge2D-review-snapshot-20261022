# Parallel demo lane handoff + evidence-only dispatch (beside a running lane)

Trigger: opening a SECOND lane (e.g. demo V3 R2) that runs parallel to an
existing manager-owned lane (e.g. S12) sharing the machine but nothing else.

## 1. Zero-competing-writer proof (before HANDOFF_ACCEPTED, all live)

Run all six; any hit = stop dispatch, reconcile, never create a rival owner:

1. `grep -rl "<LANE-TASK-PREFIX>"` across the lane work tree AND the evidence
   root (excludes `.git/`) → must be zero hits outside this run's own files.
2. Evidence base dir for the lane must not exist before this run; create only
   `<base>/<UTC-run-id>/{_manager,<T00>}`.
3. `runtime-runs/` holds only prior-owner era dirs; the sole `<LANE>-*` dir is
   this run's.
4. `hermes sessions list` shows no worker sessions for the lane prefix.
5. Process scan for lane worker patterns (`hermes|codex|python.*<lane>`) → none.
6. Repo dirty set matches the handoff packet's intentionally-dirty list exactly;
   capture a byte baseline (below) and require VERIFIED before dispatch.

Record the proof in `_manager/HANDOFF_ACCEPTED.md`. Never resume the prior
owner (Codex UUID or foreign session) and never feed its ID to a Hermes resume.

## 2. Model route: probe the SESSION id, not the user-typed string

Users transpose long model ids from memory
(`...muse-spark-contributor-1.3...` vs `...muse-spark-1.3-contributor...`).
Both strings can even `pong` on a tolerant router — pong alone does not pick
the winner. Ground truth order:

1. Read this session's exact id from `agent.log` `turn_context` rows for the
   CURRENT session (`model=<id> provider=<p>`).
2. Probe BOTH the session id and the user-typed string with
   `hermes -z "ping" -m <candidate> --yolo`; record the matrix (candidate /
   exit / latency) in the registry.
3. Dispatch workers with the EXACT session id, same provider, reasoning max,
   fallback OFF. On route failure report `BLOCKED_MODEL_ROUTE` with raw
   output; never silently switch, never edit router/keys/global config, never
   retro-apply the lane model to the other lane or the prior owner.

## 3. Byte baseline before any writer

Use `docs/pm/tools/write_set_guard.py` (or equivalent) `capture` with
`--snapshot-dir`, then `verify --max-shrink-percent 10 --report`:

- One manifest for the lane dirty write-set (every tracked-modified +
  untracked pilot file, enumerated via `git status --porcelain=v1` +
  `git ls-files --others --exclude-standard`).
- One manifest for protected roots (MAIN DB, S11/S12 pins, immutable
  source/asset/checkpoint hashes — each re-hashed by a command you ran, never
  copied from the packet).
- Require `VERIFIED, failures 0` on a clean re-run; snapshot hashes must match
  source hashes at capture time. A fresh baseline never erases a known drift
  finding (e.g. F05) — it references the historical baseline as evidence.

## 4. Dispatch verify: 0-byte log + live PID is STARTUP SILENCE, not death

Launch form: prompt file on disk, `hermes -z "$(cat prompt.txt)" -m <exact-id>
--yolo` from the lane repo cwd, background with notify-on-complete, START row
in `commands.jsonl` written BEFORE spawn. After launch require BOTH:

- (a) no argparse/usage error in the log head, AND
- (b) the `Resumed session <id>` line within the startup window (~2 min).

A 0-byte log with a LIVE wrapper PID at 90–120 s is normal prefill/TTFB
silence (large prompt context load), NOT a failed dispatch — do not kill it.
Keep 8-minute audit cycles: log-size delta + resume line + EXIT marker,
cross-checked with process liveness. Kill only on the proven stall signature
(frozen log AFTER mid-work progress + leaf-CPU near zero across two probes),
then resume the SAME owner session per Rules §7.

## 5. Non-interference with the running lane

The other lane's manager sessions, workers, worktrees, registry, evidence,
ports and processes are read-only or off-limits: HEAD/status check ONLY for
guard comparison, never resume/command/stop/reconfigure. Protected ports of
the other lane are never taken; verify a free pair (e.g. 3190/8190) and record
it without killing occupants. Resource checks (disk/RAM/ports) precede heavy
renders; on saturation, defer heavy jobs and keep light evidence work going.

## 6. Evidence / runtime layout (fresh per run)

- Evidence: `<evidence-base>/<lane>/<UTC-run-id>/{_manager,T00..T05}` —
  manager owns `_manager/` (RULES_LOADED, REGISTRY, HANDOFF_ACCEPTED,
  commands.jsonl, manifests); each task owns only its `Txx/` subtree.
- Runtime: `<work>/runtime-runs/<LANE>-<UTC>/Txx/{db,temp,cache,output}` —
  created BEFORE dispatch; every launch/test resolves paths here first, never
  MAIN defaults. No shared mutable code root, DB, output, fixture store,
  cache or approval state between lanes.
