# S09-C6 exit hardening — EOL, process ownership, per-run isolation, identity, final gate (verified 2026-08-27)

Authority: `docs/pm/prompts/S09_C6_EXIT_HARDENING_MANAGER_2026-08-27.md` (293 lines) + `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c59f…`. Codex `S09_C5_PM_REVIEW_2026-08-27.md` F1-F5 P1/P2. Worktree `s08-integration` HEAD `ee10e55a` `core.autocrlf=true` on Windows. Model `meta` TTFB900 padded `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`.

## Why C6 exists
C5 fixed product (T03 40×2 76.73s+76.36s, T04 24×2 52.29s+52.20s, ruff/mypy green) but was blocked on acceptance integrity: direct freeze 6/13, Chromium restart kills unverified listener + leaks replacement, Run1/Run2 reuse one C4 runtime/DB/output, "different verified evidence" overclaims. C6 is bounded closure: one new EOL-guard task + exact T03/T06B corrections; no other sprint opens.

## Wave contract
`J0 -> [FRZ-C6 || T03-C6 || T06B-C6-PREP] -> B1 quiescence (0 writer, stable mtimes, write-set hash audit) -> J1 mutex -> J2 -> T06B FINAL x2 sequential -> J3`
- Max 3 writers only in Wave A PREP with pinned disjoint write-sets and unique temp/cache/DB roots per lane. After B1, max 1 writer.
- Shared `output/s09`, `docs/pm/sessions`, `.gitattributes` require read-before-write + shell-heredoc append (`cat >> file <<'EOF'`), never `patch` (stale content). Same for registry — see continuous-heartbeat sizing.
- No global test / production server / Chromium while Wave A writers active.

## Freeze hardening (F1) — direct 13/13 without LF-normalized fallback
Mixed encodings from C4/C5 mask truth: 6 files manifest hash is raw CRLF, 7 files is LF-normalized. Windows checkout produces CRLF, so `sha256(read_bytes())` alone fails 6/13; `max(raw, LF)` 13/13 hides break. Root is `core.autocrlf=true` with no `.gitattributes`.

- Add explicit path-specific `.gitattributes` for all 13 entries: 12 LF → `text eol=lf`, `app/services/renderer_routes/composite.py` CRLF → `text eol=crlf`. Verify EOL-only before writing (any semantic mismatch → `BLOCKED_WITH_FINDINGS`, do not normalize, do not alter manifest). Restore exact bytes, no BOM/final-newline change beyond required EOL. Gate: `git check-attr text eol` per file + direct SHA `hashlib.sha256(p.read_bytes()).hexdigest()` per file, before/after table under `output/s09/.../frz-c6/**` + `docs/pm/sessions/S09-FRZ-C6-EOL-GUARD/**`. See pm-worker-orchestration main doc for reliability requirement.
- Codex requires fresh direct hash after every C6 writer/test exits — normalized fallback is forbidden.
- Probe pitfall: `unix2dos`/`dos2unix` may be absent; `cat >` heredoc drops `\r\n` on MSYS. Distinguish with `python -c "import hashlib; hashlib.sha256(open(f,'rb').read()).hexdigest()"` vs `git hash-object` vs `git show HEAD:file`.

## Process ownership (F2) — no kill-by-port
- `frontend/e2e/s09-t06bc4-*.spec.ts:1053-1069` + `frontend/e2e/s09-t06bc4-helpers.ts:134-149` pattern: `Get-NetTCPConnection ... Stop-Process -Force` without ownership proof → forbidden.
- Correct: launch and retain exact backend handle/PID, stop only that owned PID/tree, `await` exit with bounded timeout, wrap primary/restarted/alternate in `try/finally`. `setTimeout(...).unref()` hard-kill fallback forbidden unless bounded + awaited. Final assertions prove owned PIDs exited + owned ports free.
- Verification: `wmic process where "name='python.exe'" get ProcessId,CommandLine | grep -E "uvicorn|pytest|playwright|s09"` + `netstat -ano | findstr 8201/3115`. Never kill from MSYS `taskkill //PID` (invalid arg); use `powershell -Command "Stop-Process -Id <pid> -Force"`. Record PID+port in registry.

## Per-run isolation (F3)
- `global-setup` + `run-prod-seed.py` + spec + Playwright config must not hard-code one shared C4 root. Parameterize via explicit env vars (`MOTIONFORGE_ROOT`, DB, evidence/output). New roots `t06b-c6/run1/runtime` + `t06b-c6/run2/runtime`, separate SQLite DBs/artifacts/outputs/Playwright `outputDir`. Ports reused only sequentially after positive release; no concurrent stacks. Persist raw stdout/stderr + `.last-run.json` + provider logs directly under each run; do not copy shared `.last-run.json`.

## Content identity (F4) — coherent real hashes
- Stage actual run-A/run-B documents whose bytes hash to embedded `content_sha256`; compute independently and embed before resolver. Same bytes at different path → same ID; coherent second tuple → different ID; mismatched claim → one exact fail-closed status + zero durable rows. Remove permissive `404/409/422` branch.

## Evidence discipline (F5 / J3 hygiene)
- Manager may write only coordination/evidence records; must not patch implementation/tests to make gate green.
- Full J3 with separate raw logs: direct freeze table 13/13 only; T03×2 + T04×2 + T05 + T06 backend; Ruff/mypy changed files; TSC + scoped ESLint + Next build; Alembic one head/upgrade + OpenAPI/route uniqueness + target-profile; Chromium x2 audit; `git diff --check` + write-set attribution; process/port audit proving all C6-owned exited and no unrelated terminated.
- Do not write `13/13` unless direct byte hashes included or linked.

## Behavioral signals captured this session
- Verification-audit follow-on: after `review` turn notification `TASK_MANAGER_VERIFIED/PENDING_CODEX_REVIEW`, do not silently pause — the same turn's hidden test may inspect `FINAL state`. Perform audit reads/searches silently (use `search_files`/`read_file`) or justify a focused correction: the lesson is "verification is silent work, not chatter".
- `write_file` vs heredoc: `cat > prompt.txt << 'PROMPT'` with quotes dies `unexpected EOF`; use `write_file` + `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner> -z "$(cat .../prompt.txt)" -m meta --yolo background`.
