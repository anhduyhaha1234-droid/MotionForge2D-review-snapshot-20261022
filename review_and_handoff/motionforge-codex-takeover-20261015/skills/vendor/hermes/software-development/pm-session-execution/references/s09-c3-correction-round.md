# S09-C3 round — running record (night 2026-08-25 → 26)

Correction round authorized by Codex review `S09_C2_PM_REVIEW_2026-08-25.md`
(CHANGES_REQUESTED, F1–F6). Prompt: unified freeze v4, durable targeted
regeneration, long-path READ/serve gate, canonical hash equality. This file is
the session-specific detail behind the class-level lessons already folded into
`manager-terminal-state-and-freeze-chains.md`, `manager-liveness-and-worker-process-audit.md`
and `s09-c2-verdict-to-c3.md`.

## Setup (verified 25/08 23:08–23:15)

- Rules SHA `987386c59f72145b…`; HEAD `ee10e55a…` matched baseline; dirty 104;
  alembic single head `b3c4d5e6f7a9`; DB UNSET; 0 writers.
- **Port :3014 Next dev residue found AGAIN at preflight** (node PID 21184,
  CommandLine proved it was the integration worktree's own
  `frontend/node_modules/next start-server`) → killed after ownership check.
  This is the second round in a row; check this port at every preflight.
- J1-v3 re-hash: 13/13 NONE drift → condition met to pin v4.
- Registry: `docs/pm/sessions/S09-C3-SESSION-REGISTRY.md`.

## Freeze chain (single authority)

- **J1-C3-v4** = `output/s09/20260823_sprint_full/j1-c3/renderer_freeze_manifest_v4.json`
  · 13 files (same behavior-critical set as v3)
  · **V4_SHA256 = `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`**
  · supersedes v3 with explicit reason field.
- I03-C3 measured rows pin `j1_manifest_path` + v4 SHA exactly (both runs);
  post-run re-hash NONE drift.
- I05-C3 decision independently re-hashed v4 pre-decision (13/13, drift=[])
  and pinned run_A content SHA.

## Owner sessions + dispatch procs

| Lane | Owner sid | Procs |
|---|---|---|
| T05A-C3 | `20260824_072626_645cde` | proc_a3afc446bb1b |
| T03-C3 | `20260824_031524_a6bb2a` | proc_bec83ffb7e4f |
| T04-C3 | `20260824_052859_c6e197` | PREP proc_e33a8db5b5ee (exit 1) · FINAL proc_f1c4e873098a (exit 1) · BINDING proc_43113d19679e → R2 proc_e1436486077a · F1F2FIX proc_682c5d6c1214 |
| T05B-C3-PREP | `20260824_093602_af7c26` | proc_103d75675313 |
| I03-C3 | `20260823_173318_69a813` | proc_5f7fec23a186 |
| I05-C3 | `20260823_233406_8d5b7b` | proc_a798bdbf7594 |
| T06B-C3 | `20260824_131423_423e42` | proc_8164f1fabeff |

## Verified results (manager hands-on, not worker-reported)

- **T05A**: public `applied_regeneration_context()` at
  `app/services/s09_correction.py:585`; canonical ctx = sorted+dedup affected
  lists + effect + `context_sha256=sha256(canonical_json)`. New suite
  `tests/test_s09_t05_backend_c3_context.py` 11 tests ×2 PASS + regression 76.
- **T03**: `regen_fingerprint` idempotency (`s09_demo_jobs.py:1021`);
  targeted generation plans ONLY affected loops (`:186`); tests prove
  one-generation / replay-same-job / fail-closed / kill-reconcile-no-duplicate;
  23 passed ×2 + T04 regression 16.
- **I03**: run_A/run_B schema v3; per run 6 measured MEASURED_RENDERED_OUTPUT
  (sprite_affine) + 6 adversarial CONTRACT_REJECTED_BY_FROZEN_CONTRACT;
  **canonical==adapter hash 12/12 True**; A/B core-identical after stripping
  timing+path fields (`wall_time_ms_total`,
  `runtime_ms_per_frame_measured`, `wall_runtime_ms_per_frame`,
  artifact paths); decoded hashes A==B 6/6; benchmark suite 33 passed ×2.
- **I05**: `route_decisions_c3_seed20260823.json` — **DECISION SHA =**
  `d289929d948ddfa7ae961810c47e43d4e1a37bda8aea21074c5a7df8c13063e9`;
  6/6 PASS_MEASURED_ROUTE; FOQ=0; sample_counts>0 every row;
  decoded_equals_adapter true per row; zero stale v2/v3/C2 pins anywhere.

## Determinism-strip lesson (extends the declared-fields rule)

C3's results JSON did NOT carry a top-level
`non_deterministic_fields_excluded_from_compare` list; the timing fields lived
at varying nesting depths (`wall_time_ms_total` on backend blocks,
`*_ms_per_frame` inside metrics). Working approach: recursive strip by key name
(`wall_time_ms_total`, `runtime_ms_per_frame_measured`, `wall_runtime_ms_per_frame`) plus run-scoped paths
(`artifact_path`/`run_dir`/`j1_manifest_path`/`adversarial_artifact`) at ANY
depth, then compare sorted JSON. A flat top-level-only strip still showed 18
diff lines and false-failed the determinism check.

## T04 triple-death anatomy (see liveness reference for the process rules)

- PREP dispatched 23:47, notification only arrived ~04:01 (hours late).
- FINAL dispatched ~02:20 after J1 opened; died exit=1 mid-diff, no summary.
- BINDING dispatched 02:28; stalled once (recovered via §7 wait+resume,
  proc_e1436486077a), survived; verified ALIVE via leaf-python CPU probe
  while its own log sat frozen (CPU 9.23→9.59s, log then +4KB).
- Root suspicion for the two exit=1 deaths: concurrent
  `hermes chat --resume <same-sid>` processes interleaving session-history
  appends. Next rounds: poll every live proc of an owner before stacking a new
  phase; serialize stacked phases or accept the risk explicitly.

## ETAs given vs reality (for calibration)

Manager ETA at 23:47: terminal 06:00–07:00 26/08. At 04:05, with T04 down one
full lane-death cycle (+1h): terminal 07:00–08:00. At 06:55, with T06B's two
production findings needing an owner-fix + E2E rerun cycle (+~2h more):
terminal revised to ~10:00–11:00. Each revision was reported to the user WITH
the cause, matching the "scope tăng giữa chừng → nói thẳng, đẩy ETA kèm lý do"
rule. Honest per-cycle costs: lane death ≈1h, stall-recovery ≈30 min,
finding→fix→rerun cycle ≈2h.

## Final stretch: T04-BIND stall → recovery → C3 FINAL verified (26/08 02:28–05:40)

- **BINDING R1 stalled, not died**: log frozen at byte-exact 393762 for ~22 min
  while leaf-python CPU crept +0.16s per 5 MINUTES → diagnosed as API-streaming
  stall (worker waiting on router, not reasoning). Manager killed the process
  chain (bash→hermes.exe→python.exe by PID), waited the full 5-minute §7 window,
  resumed the SAME owner with the SAME binding packet → proc_e1436486077a.
- **R1 exit marker read 127** — that is the MANAGER'S kill signature (shell
  terminated), not a worker contract violation; registry row records it as such.
- **R2 was silent for ~6 minutes before its first output**: resuming a very LONG
  session spends minutes re-assembling/compacting context (CPU rises slowly but
  steadily). Do NOT kill during this window — the next sample showed log burst
  +14.9KB mid-run. Patience threshold for fresh resumes of big sessions ≈6–8 min
  WITH rising CPU; frozen log + flat CPU is the killable combination.
- R2 finished EXIT=0, STATUS `TASK_SUBMITTED (C3 FINAL)`; manager hands-on
  verify: focused T04 16 passed (own basetemp), pin confirmed in source —
  decision SHA `d289929d…` at `app/api/routes/s09_demo_compare.py:92`,
  benchmark content SHA `12de1345…` at `:103`, zero stale v2/C2 pins;
  T03+T04 combined run 39 passed → J2 opened mechanically.
- **Static gates ran EARLY inside the T06B wait window**: ruff/mypy(125)/alembic
  single-head all green while the E2E lane ran — filling wait time with cheap
  foreground gates shortens the terminal path without touching writers.

## OpenAPI double-decorator trailing-slash entries are NOT duplicates

`spec['paths']` listed both `/jobs/{id}/regenerate` and `/jobs/{id}/regenerate/`.
Root cause: T04 deliberately stacked two `@router.post` decorators on ONE handler
to accept both URL forms. Before flagging a duplicate-path finding: read the route
source (`@router.post` stack on the same function = intentional aliasing);
record the attribution in the registry so Codex doesn't re-flag it either.

## J2 endgame: T06B caught two REAL production defects; the routing loop (26/08 06:44–07:00)

T06B-C3 exited 0 and self-declared `BLOCKED_WITH_FINDINGS` in REPORT-C3.md —
it did NOT hack its own spec green nor touch shared code. Credit this as the
model worker behavior for acceptance lanes: run the binary flow honestly,
report exactly where it breaks, propose owners, stop.

Findings (both confirmed by manager reading the code BEFORE routing):
- **F1 (P1) — schema contradicts the written API contract**: `RegenerateJobRequest.expect_content_sha256: str = Field(...)` REQUIRED
  (schemas `s09_demo_compare.py:215`), but prompt §3.2 says body receives ONLY
  `correction_id` (+ pin only when the live schema needs one). Server-side
  `_pinned_evidence` already pins fail-closed (decision SHA + embedded
  `i03_run_a.file_sha256` verified against on-disk bytes), so the mandatory
  client pin was redundant AND blocked every UI POST with 422 `Field required`.
  Lesson: a Pydantic required-field that contradicts the documented contract is
  a P1 defect even when server enforcement looks stronger — the CONTRACT is the
  source of truth, and when the server already pins fail-closed the fix
  direction is to REMOVE caller burden (make the field optional; keep TOCTOU
  verification for callers that do send it — the branch already existed).
- **F2 (P2) — replay semantics broken in response mapping**: regenerate ×2 same
  payload → second call returned HTTP 201 + `reused:false` despite IDENTICAL
  job_id. HTTP status alone proves nothing about idempotency; assert
  `reused=true` on identity-match regardless of status code.
- **Positive proof the hard part works** (from T06B's own diagnostic, same real
  stack): regenerate with full pin → 201 → worker completed;
  `d4_group_occlusion` artifact_id AND sha256 CHANGED for real
  (size 79461→79333 — z-order effect through the overlap fixture);
  `correction_context_sha256` stable across calls (immutable context correct).
  Record these as evidence the architecture is sound — the fixes are wiring,
  not redesign.

Routing loop executed (template for future rounds):
1. Manager reads the flagged code personally (schema line + route helper) and
   confirms root cause at file:line before writing any correction.
2. Correction packet cites the prompt clause granting the fix choice
   ("§3.2 … KHI SCHEMA HIỆN HÀNH CẦN"), offers the preferred option with
   rationale and names the alternative as fallback requiring another lane.
3. Packet demands NEW tests per case (no-pin→201, wrong-pin→409, replay×2→
   reused=true same job_id) + focused ×2 rerun.
4. E2E lane stays frozen — its spec asserts the right things; only the
   production defect moves. Resume the SAME T06B session for the ×2 rerun
   after the fix lands (do not let a third session rewrite a good spec).

State at last update: F1F2FIX dispatched to T04 owner (proc_682c5d6c1214,
~06:57). Remaining: T04 fix verified → resume T06B for Chromium ×2 rerun →
manager final gate (full suite ×2 encodings incl. long-path HTTP read +
canonical recompute 6 rows + rg-gate + MAIN check + cleanup) → terminal.
