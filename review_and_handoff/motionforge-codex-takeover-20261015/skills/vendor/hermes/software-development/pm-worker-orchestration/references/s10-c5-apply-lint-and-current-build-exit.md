# S10-C5 — Apply lint correction + current-build final exit (verified 2026-08-30)

C4 backend was already Codex-green; the only blocker was the frontend lint gate.
C5 was a bounded two-owner round: `T04B-C2 -> J5 -> T04C-C4 -> EXIT`.

## Codex verdict & scope

- `S10-C4 = CHANGES_REQUESTED / NOT_APPROVED` (review
  `docs/pm/reviews/S10_C4_FINAL_PM_REVIEW_2026-08-30.md`).
- F1 (P1): `frontend/src/app/(app)/apply/page.tsx:90` — effect synchronously
  calls `setRunId(urlRunId)` / `setProjectIdForStatus(urlProject)` →
  `react-hooks/set-state-in-effect`, exit 1. The page is UNTRACKED S10 code in
  the explicit T04B write-set — NOT pre-existing product debt. T04B's recorded
  lint command had checked only `src/features/apply/**`, omitting the owned
  route page, while the sprint exit claimed scoped Apply ESLint green.
- Folded-in warnings (same exact scoped lint set): 1 unused-variable in
  `frontend/e2e/s10-apply-ui.spec.ts` (T04B-owned) + 3 in
  `frontend/e2e/s10-full-apply.spec.ts` (T04C-owned).
- Backend FROZEN in C5 — any backend defect = `BLOCKED_SCOPE_EXPANSION` with
  reproduction + owner attribution, NO silent T01C/T03/T04A resume.

## Manager preflight (#5/#6 as prompt-mandated)

- Backend no-write baseline (aggregate): `sha256sum <18 backend prod+test
  files> | sha256sum` → `312ea89c95ec…` — re-run at every gate, equality =
  zero drift. This is the frozen-lane drift proof.
- Frontend baseline: `sha256sum` applied to apply page + features/apply +
  both E2E specs (aggregate `9468dbe0…`).
- ESLint exact baseline BEFORE dispatch (must match Codex's one-error +
  four-warnings exactly; any EXTRA error -> classify owner and stop):
  `npm exec eslint -- 'src/features/apply/**/*.{ts,tsx}'
  'src/app/(app)/apply/page.tsx' 'e2e/s10-apply-ui.spec.ts'
  'e2e/s10-full-apply.spec.ts' --max-warnings 0`
  → 1 error @ page.tsx:90 + warnings `apply-ui:187 helper`,
  `full-apply:380 fixtureTruth / 751 status / 993 evidenceHashes`.
- J1-v4 rehash 13/13 + EOL PASS; alembic `a10b11c12d3e` single; DB UNSET;
  ports 8201/3015 free; MAIN `f0ee4bd` (82 dirty foreign, untouched).
- Workers check: ONLY hermes desktop (5628=self) + serve (5280) — zero S10
  writer. But **a stray uvicorn probe was still alive**: PID 25956
  `python -m uvicorn app.api.app:app --port 8399` created 14:57 (inside the
  T04C R7 window) despite dispatch-r7 claiming "probe trên 8399 đã kill".
  Lesson: worker cleanup claims are NOT evidence — netstat probe ports at
  every preflight; kill by exact PID with ownership proof (cmdline + port +
  dispatch-log reference), then verify port free.

## T04B-C2 (owner 20260828_020206_b1f8af) — render-phase adjust fix

Allowed writes: `apply/page.tsx` ONLY + `s10-apply-ui.spec.ts` ONLY +
task docs + `output/s10/c5/t04b-c2/**`. `features/apply/**`, `api.ts`,
navigation = read-only. Forbidden: eslint-disable, config weakening, async
timeout hack, hidden state copy, deleting/weakening behavior assertions.

Landed fix (structural, React official "adjust state during render"):

```tsx
const [prevUrlRunId, setPrevUrlRunId] = useState<string | null>(urlRunId);
const [prevUrlProject, setPrevUrlProject] = useState<string | null>(urlProject);
if (urlRunId !== prevUrlRunId || urlProject !== prevUrlProject) {
  setPrevUrlRunId(urlRunId); setPrevUrlProject(urlProject);
  if (urlRunId) setRunId(urlRunId);
  if (urlProject) setProjectIdForStatus(urlProject);
}
useEffect(() => { writeStorage(runId, projectIdForStatus); }, [runId, projectIdForStatus]); // storage write ONLY — never setState, never rewrites URL (back/forward must not fight a replace loop)
```

- `helper` warning resolved by using it in a truthful assertion (helper text
  check) or deleting the genuinely dead binding — worker chose correctly.
- Worker self-verified: exact eslint 0/0, TSC 0, fresh build
  `rbYCsFU8q82gvOvcRhJSA` validator 7/7, UI spec 5 passed / 1 skipped
  (mobile), back-forward probe 5/5, pytest api+workflow 32 passed, no
  `.tmp` files, zero `eslint-disable` grep, git diff --check 0.

## J5 — Manager independent UI join gate

1. eslint EXACT full set from `frontend/` → **exit 0, 0/0** (Manager re-ran).
2. grep `eslint-disable` in both files → 0.
3. `npm exec tsc -- --noEmit` → 0.
4. Fresh Next build → BUILD_ID `rbYCsFU8q82gvOvcRhJSA` (201 files),
   `node output/s10/run-s10.js --verify-build-only` → 7/7;
   `frontend/.next/BUILD_ID` matches manifest.
5. UI spec log: `5 passed, 1 skipped`; back-forward probe log real.
6. Backend aggregate SHA unchanged (`312ea89c…`) — zero backend drift.
7. J1-v4 13/13, alembic single head, `git diff --check` 0, 46 porcelain
   = allowlist + pre-existing (porcelain +1 vs C4 exit = the C5 prompt/docs
   appends — attributed, not foreign).

Only then `J5 = MANAGER_VERIFIED` and T04C-C4 resumed.

## T04C-C4 (owner 20260828_023122_76b87e) — warning cleanup + new-build runs

Allowed: `s10-full-apply.spec.ts` + bounded global-setup/config +
`tests/fixtures/s10_full_apply/**` (fixture enlargement only if needed) +
task docs + `output/s10/c5/t04c-c4/**`. Forbidden: all production frontend,
all `app/**`, migration/model/reconciler, backend tests, C0-C4 evidence.

Key requirements:
- Full eslint set (features/apply + page + T04B E2E + T04C E2E) green
  `--max-warnings 0` — 3 T04C-owned unused bindings fixed by USING them in
  truthful assertions or deleting genuinely dead bindings, never weakening
  assertions.
- Two fresh strict vertical runs with the NEW BUILD_ID
  `rbYCsFU8q82gvOvcRhJSA` (never reuse `KIWvay6FvLdiWmVFduSMG` as
  current-build proof), distinct nested roots/DBs/ports/PIDs/job/run/
  correction IDs. Fixture initial authority may use canonical persistence
  helpers; active run/job/manifest/lease/correction truth MUST flow through
  product handlers/APIs; DB after launch = read-only probe only (zero
  INSERT/UPDATE/DELETE, manifest patch, staged synthetic truth, direct lease
  expiry/requeue, grace=0, direct reconciler). Restart: real
  `0 < verified < total`, stop exact owned PID, prove old owner gone,
  distinct replacement PID, production lease/reconciler resumes same DB/run
  after real expiry. Media: DB-bound paths, SHA/size/timebase/frame range
  match, ffprobe decode, at least one path >260, zero `.bin/.partial/
  .staging`, affected +1/new media, unaffected exact, replay dedupes.
  Structural: empty/caller-truth-free request → `REVIEW_REQUIRED` from
  non-empty measured authority; real tamper → `BLOCKED`; missing authority
  fails closed. Evidence incl. PID/listener timeline, API request/response,
  immutable manifest/fingerprint, correction before/after, adapter requests,
  read-only DB probes, ffprobe/SHA/size, structural methods/values,
  screenshots/traces, cleanup + port release.

## Exit-gate notes

- Full C5 exit gates recorded under `output/s10/c5/exit/**`; backend aggregate
  SHA re-run (frozen proof), J1-v4 13/13, full 8-file S10 backend suite once
  on a unique short isolated basetemp (retained 206/206 ×2 from C4 may be
  cited, but at least ONE current-tree final run required), exact Ruff zero,
  exact nine-file mypy literal zero, `git diff --check` zero, Alembic one head
  `a10b11c12d3e`, OpenAPI 261 paths/327 ops/0 dup, TSC green, full Apply/UI/
  E2E ESLint green `--max-warnings 0`, fresh build + validator 7/7, no
  forbidden QA origin, focused Apply UI suite green, both C5 vertical bundles
  on the SAME corrected BUILD_ID with distinct runtime identities, source
  sweep zero, ledger clean, registry/sprint-report appended (never rewritten).
- Supersede note (gate 10): C4's claim that "frontend exit was green" while
  the route page was omitted from lint is explicitly superseded by C5 truth.

## ETA trigger typo variants seen this session

`bao giờ thi xong` / `bao gio thi xong` / `sắp xoiong chưa` — instant
date-anchored wall table, run `date` first, lead with status.