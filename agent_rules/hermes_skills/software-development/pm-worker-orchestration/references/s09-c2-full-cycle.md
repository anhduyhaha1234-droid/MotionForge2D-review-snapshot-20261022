# S09-C2 full-cycle case notes (2026-08-25, terminal reached 21:30 same day)

Companion to SKILL.md rules and pm-correction-cycles.md. This file records the
COMPLETE C2 arc end-to-end (C1's file covers only through the F1 regrade) so a
future manager can see what a full successful cycle looks like with real
numbers, plus the incidents C1's notes don't have.

## Timeline of record

- 10:11 preflight: RULES_LOADED (SHA match vs review record), HEAD ee10e55a
  matched expected baseline, dirty=94 pre-existing, alembic head b3c4d5e6f7a9,
  DB unset. All 6 owner sessions verified to exist in state.db BEFORE dispatch.
- 10:25 Wave A ×5 parallel: T02-C2 (f5516b), I03-C2-PREP (69a813), T03-C2
  (a6bb2a), T04-C2 (c6e197), T06B-C2-PREP (423e42).
- 12:50 T03 WAITING_JOIN verified (15 passed ×2). 13:25 T04 submitted (13 ×2 +
  tsc). 14:20 T06B-PREP exited early → R2 relaunch. 14:30 T02 verified
  (51+14 passed ×2, mypy 125 files clean incl. TYPE_CHECKING fix for PEP 562).
- 14:45 I03-PREP exit FAILED verify: schema bump mismatch → FIX1 resume.
  15:25 FIX1 green (29 ×2) → Wave A complete.
- 15:25 J1-C2 v1 pinned: machine manifest {path: sha256} ×13 files,
  SHA 1d854969… — derivation written down this time (no brute-force repeat).
- 17:15 I03 measured run A/B: 5/6 classes pass; f5 honest FAIL
  (z_order_inversions=6, root cause composite.py:431 bbox=None full-frame
  stretch). Manager chose option (b): contract-owner correction.
- 17:50 T02 occluder correction verified (68 ×2; occluder_regions typed rect,
  backward compatible). J1-v2 pinned aa405015… (version/supersedes/reason
  lineage fields). 18:50 I03 FULL rerun: 6/6 PASS, controls 6/6
  FAILED_AS_EXPECTED, drift NONE.
- 19:15 I05 decision verified: fail_open_question_count=0, all six
  PASS_MEASURED_ROUTE, decision SHA ebce8c4b… pinned and quoted verbatim in
  every downstream packet.
- 19:25–20:50 binding wave ×3 parallel (T03 final / T04 final / T06B final),
  all packets carry "no v1/C1 fallback" clause + frozen SHAs verbatim.
- 20:55–21:50 final gate per §11 checklist: one rg-gate catch (T02 tests still
  loading superseded v1 artifact → rgfix resume → 44 ×2 green); late drift
  audit on benchmark_results.py attributed to disclosed T03 deviation → J1-v3
  pinned b8928aec…; cleanup killed stray uvicorn :8099 by PID.
- 21:30 TERMINAL: TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW. Beat the
  "tonight 22–24h" estimate despite a mid-cycle scope growth.

## What made the cycle close in one day

1. PREP/final phase split: every lane had an explicit mid-phase STATUS
   (WAITING_JOIN / CORRECTION_SUBMITTED_C2) so the measured chain never waited
   on a lane that was still writing.
2. Honest-fail handling followed the §3.2 rule mechanically: no relitigation,
   no threshold tuning, straight to contract-owner → re-freeze → rerun.
3. Every resume packet quoted frozen SHAs verbatim + "no prior-cycle fallback".
4. Manager ran decisive commands itself every time (never trusted worker
   counts): per-class overall_pass audit from JSON, determinism structural
   diff after stripping declared fields, three-grep decision audit, mtime probe
   `find MAIN -newer <manifest>` for protected-tree integrity.

## Incidents unique to this cycle

- Inline printf resume prompt with quotes/apostrophes died at bash parse time
  (exit 2) — worker received NOTHING while the wrapper reported completion.
  Detected because EXIT marker grep came up empty and log tail showed only the
  OLD session output. File-based prompts are now mandatory (SKILL.md rule).
- Worker self-reported "TASK_SUBMITTED" while its own LOG listed remaining
  steps ("Chưa xong (blocker cuối cùng)") — caught by reading the LOG tail, not
  the REPORT header. Resume packet restated ITS root-cause + exact remaining
  steps + correct phased STATUS.
- Late drift at final gate (benchmark_results.py hash ≠ manifest v2 entry):
  attribution showed mtime 19:24 = T03 PREP round, before any evidence it could
  taint, disclosed in T03's REPORT under the named escape clause, diff purely
  additive (SUPPORTED_SCHEMA_VERSIONS (1,) → (1,2,3)). Disposition: accept +
  re-pin J1-v3 including it. This is the documented exception path; undisclosed
  or post-evidence drift would have invalidated downstream instead.
- ffmpeg rawvideo rgb24 independent-hash MISMATCH on a perfect artifact
  (pixel-order difference); project public decode_rgb_frames matched exactly.
  Rule recorded: canonical decoder first, ad-hoc decoders second.
- MSYS quirks hit this cycle: `taskkill //PID` invalid-argument (use powershell
  Stop-Process -Id); heredoc append to shared registry then patch() same file
  fails (append-only discipline); hardline block on exotic compound grep
  (rephrase as python -c).

## Registry shape that worked as the Codex packet

docs/pm/sessions/S09-C2-SESSION-REGISTRY.md sections, in order: baseline
preflight line (HEAD/dirty/head/DB/rules-SHA) → lock table (task → owner
session → proc id → state → write-set → deps) → join definitions with manifest
paths+SHAs → BA-decision quotes from authorizing prompt → FG/C1 lineage
reconciliation → append-only timestamped log where every row carries REAL
verify numbers (passed counts ×2, SHAs, gate names). The registry alone gave
Codex everything needed without re-walking the transcripts.
