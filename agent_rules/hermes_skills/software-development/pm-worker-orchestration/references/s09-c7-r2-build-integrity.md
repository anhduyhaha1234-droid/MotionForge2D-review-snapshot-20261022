# S09-C7-R2 build integrity & explicit roots (2026-08-27)

Provenance: R1 review F1-F4 `S09_C7_R1_PM_REVIEW` → packet `S09_C7_R2_FINAL_CONFIG_BUILD_INTEGRITY_MANAGER`.

## F1 — env-driven rewrite default (8888, not 8201)

- `frontend/next.config.ts`: `const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8888"` + `destination: `${apiUrl}/api/:path*``. No-env serving proxies to normal app `8888`; `app/config.py`, `frontend/src/lib/api.ts`, `frontend/src/features/{demo,reskin}/index.ts` all use `8888`.
- C7 build injects `NEXT_PUBLIC_API_URL=http://localhost:8201` (+ benchmark `output/s09/20260823_sprint_full/t00-i03-c3/run_A/benchmark_results_seed20260823.json` SHA `12de1345...`) so baked `.next/server` + `.next/static` contain `8201` + SHA, no `8888/8099`. Scan must include `routes-manifest.json` + `required-server-files.*` plus server/static JS/JSON; exclude `.map`, `dev`, `cache`.

## F2 — build-manifest validator (7 checks, fail-closed)

`frontend-build-manifest.json` `{buildStartAt, buildEndAt, nodePath, cliPath, envContract, buildExitCode:0, BUILD_ID, scannedFileCount, matched8201Count, matchedBenchmarkCount, forbidden8888Count, forbidden8099Count, chunkHashes:{rel:sha256}, inputHashes:{rel:sha256}}` + `.sha256` companion.

`scanBuild()` walks `frontend/.next/server/**` + `static/**` + top-level `BUILD_ID, routes-manifest.json, required-server-files.*` (exclude `.map`, `dev/`, `cache/`), SHA256 each, count `8201/bench/8888/8099` byte substrings.

`validateBuildManifest()` before any process:
1. manifest + `.sha256` exist, `sha256(raw)==expected`
2. `buildExitCode==0`, `envContract` exactly `8201`+`benchmark rel/SHA`
3. `fs.readFileSync("frontend/.next/BUILD_ID").trim() == manifest.BUILD_ID`
4. `Object.keys(scan.chunkHashes).sort() == Object.keys(manifest.chunkHashes).sort()`
5. every `scan.chunkHashes[rel]==manifest.chunkHashes[rel]`
6. `scan.matched8201Count==manifest.matched8201Count && >=1`, `scan.matchedBenchmarkCount==manifest.matchedBenchmarkCount && >=1`, `scan.forbidden8888Count==0`, `scan.forbidden8099Count==0`
7. `collectInputHashes()` includes `frontend/next.config.ts` + S09 `frontend/src/lib/api.ts`/`frontend/src/features/demo/**` etc and equals `manifest.inputHashes`

`--build-only`: `spawnSync(process.execPath, [nextCli, "build"], {cwd: frontendDir, env: {...process.env, ...BUILD_ENV}, shell:false, timeout:300000})` → `writeBuildManifest` atomically (temp+rename for both files). `--verify-build-only` runs only `validateBuildManifest`.

Negative control: copy manifest to tmp, corrupt one `chunkHashes[rel]`, `validateBuildManifest` on copy must throw nonzero while `BUILD_ID` unchanged; canonical must still pass after.

## F3 — explicit safe roots

`parseArgs()` known set `{--build-only, --verify-build-only, --run-label, --runtime-root, --output-root}`; unknown → fail. Require all three on normal runs; reject relative/duplicate. Sanitize label `[A-Za-z0-9_-]{1,32}`.

`assertFreshRoot(p, flag)`: `path.isAbsolute`, no `..` traversal, not `MAIN C:/Users/Admin/MotionForge2D`, not `WORKTREE` root, not repo root, not `C:/`/`D:/` drive root, not `HOME`; must start with `output/s09/.../t06b-c7/r2/` or allowed reviewer tmp (explicit whitelist); must be nonexistent or existing empty dir; never `rm -rf` supplied or prior evidence; `runtimeRoot` and `outputRoot` distinct and non-overlapping (`pathsOverlap`).

Stage: verify `t06b-c7/fixtures/s09_demo` 21/21 before write; `cp -r` bundle into `runtimeRoot`; record `sourceManifestSha`/`destManifestSha` + `manifestSha`/`BUILD_ID` in `env.json`+summary.

Negative PREP: `node run-c7.js` (no args) fails before write; `node run-c7.js --run-label bad --runtime-root C:/Users/Admin/MotionForge2D --output-root ...` rejected as protected MAIN; dry `--run-label r2test --runtime-root ... --output-root ...` with parse-only flag does not spawn uvicorn/playwright.

## Timeline anchors

- Preflight 20:27 R2: HEAD `ee10e55a`, J1 13/13 `ae92247b8bfd`, `8201/8212/3115` FREE, DB UNSET, `R1 r1/run1 068b47c3 + r1/run2 217bd12a` BUILD_ID `atcxDWpHgTN3FmPD3oNt0` immutable, `r2` fresh.
- R1 build 21:05 `cyuTQUYw9Ue3lDSLgH1IN` → 21:14 `dm7D7QTAc52eVVVHqU09Y` (185/7/2/0/0) — PREP rebuild then FINAL `--build-only` per §10.1; `r2/run1|run2` not yet at 21:13 — worker still on `PREP: --verify-build-only + bad-hash + missing-roots/protected-MAIN` before Chromium, per Manager 21:10/21:15 audits.

## Gates (R2 §9-10)

PREP: `8888` fallback exactly + env override active, `node --check`, TSC `node frontend/node_modules/typescript/bin/tsc --noEmit --project frontend/tsconfig.json`, ESLint `node frontend/node_modules/eslint/bin/eslint.js --config ./eslint.config.mjs --max-warnings 0`, `playwright --list` 1, zero `BUILD_ID-only/npx/shell:true/C4/C6 fallback/kill-by-port`, fixture 21/21, canonical manifest + bad-hash + explicit-root negatives, J1 13/13.

FINAL: `--build-only` → `--verify-build-only` (record BUILD_ID/manifest SHA/counts) → `Run1 r2/run1/{runtime,e2e-results}` with explicit absolute roots → audit → `Run2 r2/run2/**` distinct explicit roots → audit → no build after Run1, both runs same manifest SHA/BUILD_ID/hashes → J1 13/13+EOL + T06 43 basetemp outside MAIN + TSC/ESLint/`--list`/fixture/`git diff --check`+write-set (fix blank EOF `S09-SESSION_REGISTRY.md:120`) + port/PID + re-run `--verify-build-only` same identity; DB query `regenerated=true` only `d4_group_occlusion`, `d1-d3 false` distinct DBs/tags/PIDs.
