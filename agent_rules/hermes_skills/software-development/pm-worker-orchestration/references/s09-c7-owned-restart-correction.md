# S09-C7 Owned Restart Correction — Evidence Schema Completion (2026-08-27)

Scope: §6 machine-checkable evidence x2 runs + §5 lifecycle design. Follow-up to C6 exit hardening where discriminating Chromium was green but evidence schema was incomplete.

## Timeline

- **PREP 17:58 VERIFIED**: TSC 0, scoped ESLint 0, `--list 1 test` (fix: `playwright.s09t06bc4.config.ts` allows default worktree only when `process.argv.includes('--list')`), grep 0 active `t06b-c4/kill-by-port/shell:true`, J1 13/13 `ae92247b8bfd...`, ports `8201/8212/3115` released, `8099+3014` preserved, DB UNSET. Exclusive write-set `frontend/e2e/s09-t06bc4-*.ts + playwright.s09t06bc4.config.ts + output/s09/.../t06b-c7/**` (untracked `??`, not `M` — `git diff HEAD --name-only` correctly empty, `SPRINT_BASE_M 34` pre-existing).
- **Run1 18:08 FAIL → 18:15 PASS**: first Chromium failed `expect(locator).toBeEnabled()` on `getByTestId('demo-submit')` disabled 60s (60000ms) — fixture/decision staging pointed at stale `t06b-c4` path, selector precondition not met. Worker corrected internally within same hermes session `20260824_131423_423e42` (no Manager re-dispatch): fixed `frontend/e2e/s09-t06bc4-helpers.ts` + `output/s09/.../t06b-c7/run-c7.js` staging, reran `run-c7.js --run run1` → **1 passed (37.2s, spec 35.5s)**.
- **Run2 18:16 PASS**: sequential `run-c7.js --run run2` → **1 passed (37.1s, spec 35.6s)**. Both raw `playwright-stdout.log` 1038B, `stderr` 0B, `.last-run.json` `{"status":"passed","failedTests":[]}`, `env.json` `pwExit 0`.
- **J3 audit 18:35 — schema incomplete**: lifecycle had 10 keys, missing `listenerOwnerBeforeRestart, listenerOwnerAfterReplacement, replacementListenerPid, initialStopTimestamp, replacementLaunchTimestamp, finalExited, portReleased, checkpoint ordering timestamps, rendererAttemptCount`. Discriminating logic stayed green; evidence hygiene was the gap per §6 binary gate.

## Fix Pack (wire within one owner session)

- **Spec `frontend/e2e/s09-t06bc4-targeted-regeneration.spec.ts` line ~1282 `path.join(RUN_ROOT, "lifecycle-" + runTag + ".json")`**: extend from 10 → 16+ keys capturing `listenerOwnerPid(BACKEND_PORT)` before `stopLaunched(initial)` (expect `initialPid`) and after `waitForPortListenerOwnedBy(replacement)` (expect `replacementPid`), `Date.now()` at stop completion vs launch return, `isPidAlive` + `listenerOwnerPid(8201/8212/3115)===null` after `finally` stop sequence, `checkpointHashBeforeRestart` timestamp before `stopLaunched` vs `cpAfter` read after replacement owns 8201. Assert `initialPid !== replacementPid`, `replacementListenerPid === replacementPid`, `initialStop < replacementLaunch`, all `finalExited/portReleased` true before `writeFileSync` — fail closed otherwise.
- **Evidence JSON `path.join(RUN_ROOT, "evidence-" + runTag + ".json")`**: add `checkpointId, checkpointHash, checkpointCreatedBeforeInitialExit, checkpointReadAfterReplacement, rendererAttemptCount, renderedLoops, affectedLoopIds, baseArtifactIds, regenArtifactIds` sourced from `checkpointId/hashText/checkpointHashBeforeRestart` and `regenAttempts/renderedLoops`.
- **Helpers `frontend/e2e/s09-t06bc4-helpers.ts:63`**: `env.MOTIONFORGE_S09_DECISION_DIR = path.join(runtimeRoot, "frozen-c3")` — without it backend `_c3_decision_path` falls back to `_repo_root` = `worktree/output/...` which is not the isolated runtime's staged decision.
- **Launcher `output/s09/.../t06b-c7/run-c7.js`**: stage decision at BOTH `runtime/frozen-c3/` (primary via env override) AND `runtime/output/s09/.../t00-i05-c3/` (fallback for `_repo_root`); benchmark at `BENCH_REL = output/s09/.../t00-i03-c3/run_A/benchmark_results_seed20260823.json`; fixtures priority `t06b-c6/run1/runtime/tests/fixtures/s09_demo` → `t06b-c4/...` → `t06b-c4/prod-backend-root/...`; `spawnSync("npx", ["next","build"], {shell:true})` required on Windows because `npx` is a `.cmd` shim (`ENOENT` without), while `spawn("python", [...uvicorn...], {shell:false})` and `spawn("node", [nextCliPath,...], {shell:false})` stay so `C:/` paths aren't WSL-translated.
- **Dispatch 18:36**: `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume 20260824_131423_423e42 -z "$(cat manager-c7/prompt-t06b-c7-lifecycle-fix.txt)" -m meta --yolo` (reasoning max, fallback OFF). Fresh `run1|run2` sequential via same parameterized `run-c7.js --run <run>` for new runTag/PID/DB — never copy `t06b-c6` evidence.

## Evidence Paths & Hashes (pre-fix x2, 18:15-18:16)

- `t06b-c7/run1/runtime/lifecycle-1787829279430-698103333.json`: `initialPid 29080, replacementPid 29740, alternatePid 27484, frontendPid 12948` (initial!=replacement true)
- `t06b-c7/run2/runtime/lifecycle-1787829326581-25053512.json`: `initialPid 4652, replacementPid 32580, alternatePid 31988, frontendPid 29608`
- `t06b-c7/run1/runtime/evidence-1787829279430-698103333.json`: `base 1629eccf regen d807f707 frozen 653d6d6c...` — missing checkpoint/attempt fields
- `t06b-c7/run2/runtime/evidence-1787829326581-25053512.json`: `base c1f3f1f0 regen 317b0d34 frozen 653d6d6c...` — same gap
- DB isolation: `run1/runtime/data/motionforge.db` 954368B `1ff454fa...`, `run2` 954368B `a9217ef0...` distinct; each `alt-backend-*/data/motionforge.db` 835584B distinct from its main (`run1 alt d940f316 vs main 1ff4...`, `run2 alt f4f3a795 vs main a921...`).
- Port audit after both: `8201/8212/3115` released (no `LISTENING`), `8099+3014` preserved — no `kill-by-port` path exists (`grep Get-NetTCPConnection|taskkill` 0 hits, `grep shell.*true` lifecycle 0 hits beyond documented `npx` case, `grep unref` 0 hits).

## Discriminating Assertions Staying Green (owned restart)

Only `d4_group_occlusion` affected, `d1/d2/d3` `regenerated=false` + no render timing + verbatim base identity; DB `renderer attempt count` 1; exact `404` zero mutation for altered `C3` evidence; five correction kinds never false-success; same bytes/different path identity; checkpoint created before initial exit and read after replacement owns `8201`, publications survive owned restart (verified via `regenAfterRestart.published.length==4` + `generation_evidence.frozen_evidence_sha256` unchanged + `d4AfterRestart.sha256==d4a.sha256`).
