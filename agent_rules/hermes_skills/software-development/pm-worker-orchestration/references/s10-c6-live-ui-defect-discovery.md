# S10-C6 live-UI defect discovery (verified 2026-08-30)

Non-vacuous UI acceptance immediately exposed two hidden blockers that every
prior "green" gate had masked. Full arc: PREP -> T04B-C3 (20 tests = 10
scenarios x desktop+mobile Chromium, zero skip) -> live run R1 (port-origin
config error) -> R2 (real defect A) -> R3 (API-surface gap B) ->
`BLOCKED_SCOPE_EXPANSION / PENDING_CODEX_DECISION`.

## Defect A — UI reads top-level snapshot keys that real approvals don't have

- `frontend/src/features/apply/ApplyCard.tsx:105-111`: `selection` derivation
  reads `snap.scene_manifest ?? snap.structural_lock_manifest ?? snap.shots ??
  snap.scenes` and `snap.mapping ?? snap.mappings ??
  snap.renderer_routes_per_segment` — all TOP-LEVEL keys.
- Real `apply_checkpoint.snapshot_json` (probed from run DB, checkpoint
  `eb8e53a5` run2 / `bede34ed…` run3) contains ONLY:
  `{schema, note, compatibility_policy{policy_version,
  structural_lock_manifest_id, renderer_routes_per_segment}, warnings_accepted,
  overrides, demo_artifact_refs, correction_history_refs}`.
- Consequence: `selection` is always null -> Apply never enabled with a real
  approval. The C5-F1 "acceptance theater" was exactly this: old spec asserted
  helper visibility, never `toBeDisabled()`/`toBeEnabled()`.

### Manager verification recipe (do this before routing)
1. Read the derivation code at the cited lines.
2. Open a REAL snapshot row:
   `python - <<'PY'` sqlite connect run DB -> `SELECT snapshot_json FROM
   apply_checkpoint LIMIT 1` -> json.loads -> `print(sorted(s.keys()))` and
   check individual keys (`scene_manifest`, `mapping`, `shots`, etc.).
3. Classify: UI reads wrong shape = T04B production defect (allowed to fix
   under C6 §5.3); harness/seed missing data = fixture issue; server wrong =
   backend (frozen -> Codex).

## Defect B — request-only required field = API-surface gap

- Server submit binding (s10_full_apply.py:160-163) requires
  `structural_lock_manifest.manifest_hash == slm.manifest_hash`; planner
  requires 64-hex manifest_hash (s10_chunk_plan.py:91-95).
- Real `slm.manifest_hash = bfb41c7b…` differs from BOTH checkpoint_hash
  (`0bb9353a…` — probe A used it, 422) and timebase_fingerprint
  (`1db7d4ad…` — probe B, 422).
- OpenAPI scan (app.openapi(), 261 paths): CheckpointOut has only
  checkpoint_hash/timebase_fingerprint; ReskinConfigData has
  structural_lock_manifest_id + lock_policy_version; RendererRouteEvidence
  has structural_lock_manifest_id. No public read schema exposes
  `slm.manifest_hash` (SubmitFullApplyRequest is request-only).
- Consequence: even after fixing Defect A, UI cannot assemble a
  server-accepted body. This is a contract gap, not a harness bug.

### Escalation shape that worked
- Worker stops honest, no backend patch, terminal draft
  `BLOCKED_SCOPE_EXPANSION / PENDING_CODEX_DECISION` with reproduction (2
  probes 422 + OpenAPI scan) + owner attribution.
- Manager independently confirmed (code + DB probe + OpenAPI), cleaned owned
  backend uvicorns (exact PID ownership proof: PID 36444 port 8213, PID 31956
  port 8201, bash wrappers 31124/13324/36040), then appended blocker state +
  decision options to the registry so the user can copy-paste to Codex.
- Decision options offered to Codex:
  (a) expose manifest_hash in CheckpointOut/ReskinConfigData (backend change,
      owner to assign — likely T01A/T01C);
  (b) server accepts checkpoint_hash/timebase_fingerprint as manifest
      identity (contract change);
  (c) read-only DB-probe waiver for the harness (T04C precedent).

## Residual flow after Codex decision
Resume T04B-C3 same owner (fix Defect A in scope + rerun 20/20 live) ->
J6-UI (Manager independent rerun, trace evidence for every click) ->
J6-BUILD (production frontend changed -> new BUILD_ID, 7/7 validator) ->
T04C-C5 two fresh current-build vertical runs -> EXIT.

## Related traps re-verified this round
- Build-origin port: current build baked `NEXT_PUBLIC_API_URL=localhost:8201`
  (run-s10.js BUILD_ENV, manifest envContract); suite backend must launch on
  8201 (not 8212) or UI fetch fails.
- Mobile: `devices["iPhone 13"]` maps to WebKit (not installed); use explicit
  Chromium project with viewport 390x844.
- Worker cleanup claims need re-verification: R2 claimed probe killed but
  uvicorn still listening at next preflight — always netstat probe ports
  (8213-style) AND task ports (8201/3015) before dispatch.