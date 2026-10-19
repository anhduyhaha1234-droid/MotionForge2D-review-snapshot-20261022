# S09-C7-R1 Reproducible Build Continuation (2026-08-27)

## Codex finding

- `S09-C7 = CHANGES_REQUESTED → S09-C7-R1 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`.
- Retained green: owned lifecycle real (initial proven before `page.goto`, exact PID stop, replacement owns 8201), J1 13/13, T06 43/43, TSC/ESLint.
- P1 blockers: current `.next` `BUILD_ID 3u_L9sIOg7_LPKVJA4dzu` (built 18:59 after runs) has `http://localhost:8888` in 16 files, zero `8201`, zero benchmark `12de1345...` — `run-c7.js:97-105 frontendBuiltOk()` trusted existence. Launcher still has `t06b-c6`/`t06b-c4` fixture candidates (52-54) + `shell:true`/`npx` (108, 152). REPORT claims zero audit but live files don't.

## Continuation scope

- Continuation inside C7, not C8. Resume only owner `20260824_131423_423e42` with `meta`/`max`/TTFB900.
- Exclusive write-set: `frontend/e2e/s09-t06bc4-*`, `frontend/playwright.s09t06bc4.config.ts`, `output/s09/20260823_sprint_full/t06b-c7/**`, LOG/REPORT-C7.
- Preflight 19:23: HEAD `ee10e55a`, `codex/s08-integration`, J1 13/13 `ae92247b8bfd...` 12lf+composite crlf, DB UNSET, `8201/8212/3115` FREE, stale `BUILD_ID 3u_L9...` baseline only.

## Build fix (§5)

- Remove `frontendBuiltOk`; invoke `node <frontend/node_modules/next/dist/bin/next> build` with `shell:false` and env `NEXT_PUBLIC_API_URL`, benchmark rel + SHA `12de1345...`.
- Scan `frontend/.next/server/**` + `frontend/.next/static/**` excluding `dev/`, cache, `.map`; require `8201` + SHA present, forbid `8888`/`8099`; emit `t06b-c7/r1/frontend-build-manifest.json` with timestamps, nodePath, cliPath, envContract, BUILD_ID, scanned/matched/forbidden counts, `chunkHashes: {rel: sha256}`.
- No build after Run1; final re-scan asserts BUILD_ID + chunk hashes match manifest.

## Fixture fix (§6)

- Playwright via `frontend/node_modules/playwright/cli.js` (`lib/cli.js` fallback) `shell:false`; delete all `npx`/`shell:true`.
- Single bundle `t06b-c7/fixtures/s09_demo` copied from passing C7 input, with `manifest.json` + `manifest.sha256` (rel/size/sha256); launcher verifies before run root creation.
- Per-run copy only from bundle; record source/dest manifest SHA; parameterized roots `t06b-c7/r1/run1/` + `r1/run2/`.

## Final order (§9)

`build + validate manifest → Run1 r1/run1 → audit distinct lifecycle/DB → Run2 r1/run2 → audit same BUILD_ID/chunk hashes → direct J1 13/13 + T06 43 basetemp + TSC/ESLint + git diff --check + fixture verify + port/PID audit + re-scan .next`.

Evidence per run: stdout/stderr separated, `.last-run.json`, logs, DB, artifacts, env summary, `lifecycle.json` (18 keys), evidence JSON, build-manifest ref. Reconcile REPORT-C7 with live scans.
