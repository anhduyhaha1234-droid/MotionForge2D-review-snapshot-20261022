# S09-C4 cycle notes — exact affected-scope/layer regeneration, five-kind dispatch

Session-specific detail for the C4 correction round (launched 26/08 morning).
Companion to SKILL.md; prior arcs live in pm-correction-cycles.md,
s09-c2-full-cycle.md, s09-c3-unified-freeze-cycle.md.

## What Codex's C3 review added (F1–F7, review 2026-08-26 09:51 +07)

- F1 P0: production UI submitted ALL completed loops as scope
  (CorrectionPanel derived overlap but returned `completedLoops`; QA DB job
  `d2bad83e-…` shows requested/affected d1–d4, all `regenerated=true`, real
  render_ms per loop). Artifact equality of unaffected loops was BYTE-IDENTICAL
  RERENDER, not reuse — the core S09 promise broken at the UI layer.
- F2 P1: z-order effect wrote corrected z to `placements[0]` in every
  group_place entry and the dispatcher never passed affected_layer_ids — a
  two-placement program targeting layer 2 moved layer 1 instead.
- F3 P1: every kind routed through `_apply_z_order_effect`; mask/contact/
  mesh_parts/route_override had NO render dispatcher → non-z kinds could
  re-encode unchanged media and mark regenerated=true (false success).
- F4 P1: fingerprint was two-field (base_job_id + context SHA) — frozen-
  evidence re-pin could collide with a completed job from another generation.
- F5 P1: worker guard compared `record.workspace_id != record.workspace_id`
  (self-comparison no-op) — direct durable submits could cross-bind workspaces.
- F6 P1: acceptance spec checked only artifact identity/hash/size/frame_count;
  status schema didn't expose per-loop `regenerated` — Chromium ×2 passed while
  the DB proved all four loops rendered. Acceptance must assert result.
  affected_loop_ids + regenerated flags + renderer invocation count via DB
  attempt; artifact-equality alone is NOT discriminating evidence.
- F7 P2: registry lock table left all-PENDING while later rows claimed done —
  append a reconciled state table at terminal, never leave stale locks.

C4 BA contract (frozen, §4 of the prompt): stable machine layer IDs from
structural evidence (no display labels / placements[0] / array position /
filenames); zero or >1 binding match fails closed BEFORE render/publication;
five kinds each get canonical render-effect context (mask resolves immutable
artifact evidence, mesh carries FULL applied transform, contact binds exact
end-frame/time/anchor to the operation, route uses measured-passing route_to);
three-part fingerprint base_job_id + correction_context_sha256 +
frozen_evidence_sha256 (server-verified machine value, not caller-trusted);
status exposes read-only generation_evidence + per-publication regenerated
from the attempt result (never inferred from hash equality); worker fail-closed
on cross-workspace/wrong type/state/scope-outside-base before publication.

## Dispatch mechanics lessons from this launch

- CLI flag drift bit us: packet notes said `-q "$(cat prompt.txt)"` but the
  installed hermes build's one-shot flag is `-z`. All 5 lanes died EXIT=2 with
  an argparse usage dump naming the ENTIRE prompt text as "invalid choice:
  'RESUME — S09-T05A-C4 …'" — instantly recognizable once you read the log
  head. Fix: verify flags with `hermes --help` against the INSTALLED binary,
  then redeploy. Recorded in registry as wrapper failure, never as lane
  failure. The successful relaunch used:
  `hermes --resume <owner> --provider custom -m alpha --yolo -z "$(cat output/<lane>/prompt-prep.txt)" > <lane>/dispatch.log 2>&1; echo "EXIT-<tag>=$?" >> <lane>/dispatch.log`
- Startup banner: this build prints ~307 bytes of venv-repair warnings BEFORE
  any output ("A previous lazy-backend refresh may have left the venv
  unhealthy…"). That banner alone ≠ started; wait for the
  `↻ Resumed session <id> (N user messages, M total messages)` line.
- PowerShell from MSYS bash: single-quote the entire `-Command '...'` payload
  (bash must not expand `$_`, `@{}`); double quotes inside get consumed by
  bash and inline `# comment` text leaks into the PS parser producing cascading
  parse errors. Working liveness probe pattern:
  `powershell -NoProfile -Command 'Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "python.exe" -and $_.CommandLine -like "*hermes*" } | ForEach-Object { "{0}`t{1}" -f $_.ProcessId, $_.CommandLine }'`
- Session store: owner sessions verified via `hermes sessions list | grep
  <timestamp>` (the sessions/ dir holds request dumps, not session folders).

## Router-wide TTFB stall (live incident, 10:36→11:05+)

After correct relaunch, ALL five lanes sat silent for 25+ min: logs frozen at
307 bytes (just the venv banner), leaf python CPU creeping hundredths of a
second per probe window, sockets ESTABLISHED to :20128, no `Resumed session`
line yet. Decisive evidence was in the Manager's OWN app log
(`~/AppData/Local/hermes/logs/agent.log`): repeating
`Codex stream produced no bytes within TTFB cutoff (120s > 120s, model=alpha)
... Killing connection so the retry loop can reconnect` + `APIConnectionError,
Retrying API call (attempt N/3)` — including for the Manager chat itself.

Disposition: provider-side outage shape → every lane classified
RUNNING_RETRY_WAIT per Rules §7 (infinite wait-5-min → liveness-audit → retry
cycles on the SAME processes), nothing killed, blocker named plainly in the
heartbeat with revised ETA. Contrast with the C3 T04 case: that was ONE lane
frozen while others progressed (worker-side streaming hang → kill exact PIDs).
The simultaneous-silence-across-all-lanes-plus-manager signature flips the
verdict to "wait, don't kill".

## Freeze chain retained across rounds

J1-v4 remains the sole authority into C4 (manifest SHA ae92247b8bfd…, 13 files
re-hashed clean pre-Wave-A at 10:12 +07). I03 run-A 12de1345…, run-B dab37e41…,
I05 decision d289929d948ddfa7ae961810c47e43d4e1a37bda8aea21074c5a7df8c13063e9
all carried forward WITHOUT rerun — C4 workers are forbidden from touching the
13-file set; any byte drift ⇒ BLOCKED_FREEZE_DRIFT with owner attribution, not
an automatic re-pin. Re-hash recipe: load manifest JSON, sha256 each relative
path, compare — 13 entries, expect zero drift lines.

## Registry skeleton that opened C4

Lock table columns: Task ID | Owner session | Provider/model | State |
Exclusive write-set | Depends. Append log entries so far: PREFLIGHT OK (rules
SHA, HEAD match, dirty count vs review snapshot, alembic head, DB unset,
zero writers), J0-C4 PASS (re-hash), first-launch EXIT=2 (wrapper syntax),
REDEPLOY with proc ids, LIVENESS AUDIT (PIDs + router-stall classification).
Each entry timestamped +07 from actual `date` output.
