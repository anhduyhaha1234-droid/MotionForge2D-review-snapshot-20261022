# S09-C6 execution addendum — live pitfalls hit after prompt dispatch (verified 2026-08-27 14:36–16:41)

Extends `references/s09-c6-exit-hardening.md`. Captures failures that only surfaced when actually running B1/J1/J2/J3, not in the plan.

## 1. .gitattributes exclusive-owner violation — B1 quiescence caught it

- Wave A: FRZ-C6 owned `.gitattributes` (13 path-specific lines, 12 lf + composite crlf). T06B-C6-PREP prompt said "frontend/e2e/* + t06b-c6/** only" — but did NOT explicitly forbid `.gitattributes`. T06B overwrote it at 15:29:58 with 28 lines (`*.py text eol=lf` + wildcards + `composite eol=lf`).
- Direct hash still 13/13 (disk bytes still CRLF), so freeze looked green. Only `cat -A` + `wc -l` + `git check-attr` per file at B1 revealed 28 vs 13 and `composite lf` vs `crlf`.
- Fix: resume exact owner `20260827_143659_d1c168` single-writer (max 1 after B1) with prompt that rewrites `.gitattributes` to 13 exact lines, LF no BOM, verify `wc -l 13` + `12 lf + 1 crlf` + direct 13/13 + `cat -A 13x $`. Re-TASK_SUBMITTED 15:38, then B1 re-verified 15:41 before J1.
- Lesson: `.gitattributes` is a shared root file — pin its write-set to FRZ only in EVERY lane prompt. Manager B1 must `cat -A` + `wc -l` + per-file `git check-attr` even when direct hash passes. Reference file already lists write-set discipline — this is the concrete example.

## 2. ESLint 9 `eslint.config.mjs` cwd requirement

- Direct `node ./node_modules/eslint/bin/eslint.js --max-warnings 0 e2e/...` from worktree root → `ESLint couldn't find an eslint.config.(js|mjs|cjs) file` exit 2, even though `frontend/eslint.config.mjs` exists. Same via `npx eslint`.
- Fix: run eslint with `cwd = frontend/` (`node ./node_modules/eslint/bin/eslint.js --max-warnings 0 e2e/...` inside frontend) or explicit `--config frontend/eslint.config.mjs`. Then scoped 3-file + 4-file both exit 0.
- J2 initially saved exit 0 log with the wrong launcher (piped through `tee` hid exit 2). Manager must capture exit code directly, not via pipe.
- Add to Windows pitfalls: Next.js eslint uses `.mjs`, not `.js`.

## 3. Terminal 180s cap vs pytest wall time

- J1-C6 ran T03 + T04 in one `python - << 'PY'` block with `subprocess.Popen(..., timeout=300)` but the outer `terminal` tool default is 180s. Combined T03 76s + T03 77s + T04 52s > 180s → outer timeout killed the wrapper at T04 run1 (0 bytes log), not pytest itself.
- Fix: split J1 into two terminal calls (T03 x2 first, then T04 x2) or set `timeout=600` on the terminal call. Use `env -u MOTIONFORGE_DATABASE_URL python -m pytest -p no:cacheprovider -q --basetemp=$(mktemp -d)` with explicit timeout, or `terminal(timeout=600)` for long suites. T04 isolated basetemp 52s each, T03 76s each — budget 600s.
- Lesson: `timeout` param on `terminal` is outer wall time, independent of inner `subprocess` timeout. Long suites must raise outer timeout.

## 4. Windows `npm` vs `npm.cmd` + Next build cwd

- `subprocess.Popen(["npm","run","build"], cwd=frontend)` → `FileNotFoundError: [WinError 2]` on Windows (MSYS `npm` shim not on PATH for raw CreateProcess). Must use `"C:/Program Files/nodejs/npm.cmd"` or `where npm` → `npm.cmd` path. Same for `npx` → `npx.cmd`.
- Next build must run with `cwd=frontend` and `NEXT_PUBLIC_API_URL` env. Build output `✓ Compiled in 4.0s` + `10/10 static` is the gate.

## 5. OpenAPI import — `app` object vs factory

- `from app.api.app import create_app` → `ImportError: cannot import name 'create_app'`. Actual export is `app = FastAPI(...)` singleton at `app/api/app.py:96`; `app/main.py` re-exports `from app.api.app import app`. Correct probe: `from app.api.app import app` + `TestClient(app).get("/openapi.json")` under `MOTIONFORGE_DATABASE_URL=sqlite:///:memory:`.
- 253 paths unique, 44 s09/demo/correction/approval — proves additive, no duplicate.

## 6. Prompt heredoc vs `write_file`

- `cat > prompt.txt << 'PROMPT'` with quotes inside prompt body dies `unexpected EOF while looking for matching ''` on MSYS bash. T06B prep creation failed twice with bash heredoc. Fix: use `write_file` tool for all prompt files containing quotes/backticks, then `hermes --resume <id> -z "$(cat .../prompt.txt)" -m meta --yolo` background.

## 7. T04 not dispatched but still gated

- C6 dispatched only FRZ + T03 + T06B. J1/J3 still required `T04 focused ×2` (24 passed 51.97s/51.88s) and `T05` + `T06` backend gates. Manager re-ran T04 as verification even though no correction — audit expects all suites fresh at J3. Don't skip "not dispatched" lanes in J1/J3.
