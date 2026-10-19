# S11-C3 exact-identity + restart-proof + fail-fast exit (2026-09-04)

Trigger: Codex verdict `S11-C2 = CHANGES_REQUESTED / NOT_APPROVED` on pushed
canonical `7474eb7` (local == remote). Finite residuals only — no history
rewrite, no S12/S13.

## Findings → closure map (Codex S11_C2_PM_REREVIEW_2026-09-04.md, 183 lines)

- [P1] Completion authority accepts inconsistent identity
  (`qc_check_runs.py:310-361, 420-440, 491-541`): 5 fresh Alembic-head tamper
  rows returned `completed` (source ID/SHA mismatch, wrong-but-nonempty
  detector revision, manifest policy_id mismatch, manifest schema mismatch,
  generation-vs-evidence contradiction). Owner T03G `20260903_170546_0d42f6`
  from clean tip `e7e9242`. Closure = exact-value binding matrix: manifest
  schema_version PRESENT integer == RUN_QC_SCHEMA_VERSION; policy_id/hash ==
  current server policy; fingerprint == current evidence; source_generation
  non-empty == job input_generation AND recompute evidence with that
  generation; source artifact ID/SHA == persisted current source;
  detector revision map == server-owned registry (not just non-empty).
  Legitimate no-source representation supported exactly as producer writes —
  never default-to-cover missing/corrupt.
- [P1] Restart test overclaims affected/QC-read proof
  (`test_s11...acceptance.py:1958-2010, 2057-2074`): snapshot role-A AND
  role-C preimages (row IDs, artifact IDs, state, path, SHA-256, size, bytes);
  prove new recompute-job artifacts bound to A (not pre-existing) with
  expected purposes + valid hashes; byte-identical C proof + zero C
  publication; fresh-session reads assert correction status, recompute
  job/attempt/effect, QCItem status, computed readiness — no resolved/ready
  claim if contract says awaiting recheck. Exact node run TWICE on separate
  fresh DB/managed/basetemp roots. Owner T06C `20260903_223530_b90853`.
- [P1] Static-gate masking: pre-push log hid a mypy `no-any-return` failure
  and an OpenAPI command on a nonexistent test file behind a later shell
  exit 0. Fail-fast ladder preserves EVERY per-command exit (PowerShell:
  check `$LASTEXITCODE` immediately after each command); any red/missing/
  command-not-found is RED, never an aggregate green. OpenAPI via direct
  `app.openapi()` scan (floor: 274 paths / 340 ops / 0 dup IDs).
- Stranded `e7e9242` (T03G mypy fix, committed 16:42, canonical pushed 16:29
  without it): INT01 must merge ALL verified successors incl. follow-ons and
  prove every verified tip is an ancestor of final HEAD.
- [P2] Model/evidence exactness: per-turn `cmc/muse-spark-1.3-contributor`
  via custom 9Router, requested reasoning max, fallback OFF, TTFB 900 — log
  requested vs actual from `session_model_usage`, never silently switch.
  Hermetic evidence: explicit S11-C3 evidence-root env var for Manager
  evidence; temp-local default for ordinary reruns (never mutate prior-round
  evidence dirs).

## Wave plan

- Preflight: canonical local == remote == `7474eb7`, porcelain 0 everywhere,
  zero writers, fresh `s11-c3/<run-id>/` evidence root (never append C2),
  write_set_guard baselines + preimage snapshots.
- C3-A1 (T03G) + C3-A2 (T06C): max two parallel lanes, disjoint
  worktrees/write-sets/evidence/temp roots.
- T04B conditional ONLY on a new executable product RED from strengthened
  assertions; T05A read-only unless a real integrated consumer RED (then only
  real owner `...4a4548`; `...5b3841` permanently frozen from T05A).
- INT01 Git-only merge → fail-fast ladder (five-row matrix, both T03G
  modules ≥98+new, T06C node ×2 then full module, both T05A modules 14/14,
  ruff F, retained mypy scope, diff-check vs base `7751598`, one Alembic
  head + fresh upgrade, outer ≥12, inner ≥380+new, T01 64/64, S10 71/71,
  frontend/migration hashes unchanged, porcelain 0) → ONE non-force push →
  ls-remote == local proof → terminal packet.
- Terminal verbatim only:
  `S11-C3 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`.

## Post-compaction evidence discipline (lesson 2026-09-04)

After context compaction, terminal/process results may arrive SUMMARIZED
(e.g. "exit 0, 1 lines output") with real stdout hidden. That is NOT proof
of values — never assert SHAs, counts, or tips as "just verified" from a
pruned result. Re-read the raw evidence file via read_file (returns full
content: dispatch logs, registry, raw gate files) before claiming numbers,
or explicitly qualify values as carried from pre-compaction verified state.
Preflight claims need a live command whose output you actually saw.
