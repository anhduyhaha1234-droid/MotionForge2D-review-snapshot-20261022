# S09-C5 final-gate Windows pitfalls — CRLF, basetemp, glob, TSC/ESLint (verified 2026-08-27)

Authority: `docs/pm/prompts/S09_C5_FINAL_CORRECTION_MANAGER_2026-08-27.md` C5-R2 (371 lines) + `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c59f…`. Worktree `s08-integration` HEAD `ee10e55a` `core.autocrlf=true` on Windows. Model `meta` TTFB 900.

## 1. J1-v4 freeze mixed CRLF/LF — max(raw,lf) 13/13

Manifest `renderer_freeze_manifest_v4.json` `ae92247b…` was built from **mixed** encodings: 6 files stored raw CRLF hash, 7 files stored LF-normalized hash. Worktree on Windows checks out CRLF (`core.autocrlf=true`), so a strict raw `sha256(read_bytes())` fails 6/13 or 7/13 depending on normalization. Content is intact — only line endings diverge.

**Correct gate:**
```python
raw = Path(rel).read_bytes()
rh = hashlib.sha256(raw).hexdigest()
lh = hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()
ok = (rh == exp or lh == exp)  # max(raw,lf) per file
# J1-C5: 13/13, J2: 13/13, J3: 13/13 content (not "CRLF drift")
```
Label as "CRLF-only drift, content intact" — never as hard freeze break. Verify via `git hash-object` vs `sha256` to distinguish.

## 2. Basetemp prefix too long — OSError

Using `Path(tempdir)/("L"*120+"_j1c5")/("run1_"+"x"*60)` as `--basetemp` yields:
`OSError: could not create numbered dir with prefix test_c5_frozen_evidence_path_i … after 10 tries` — pytest tries to create `test_*` dirs under the too-long prefix.

**Fix:** short isolated basetemp per suite (`C:/.../Temp/j3c5_T03_focused`), 600s timeout per `pytest -q --basetemp=<short> --cache-clear`. Deep `≥260` path is created *inside* the test via `_win_long_path` contract (T03/T04), not via basetemp.

Split J1/J3 suites sequentially, one `run_one(label, basetemp, tests)` at a time — not 4 suites in one 180s slot (timeout).

## 3. `.codex-review` deep nested path breaks recursive glob

`Path.rglob("*")` / `glob("**/TARGET_PROFILE*")` dies:
`FileNotFoundError: .../.codex-review/.../segment-level-nested-directory-longpath/...` — artifact from long-path test left 3-deep 260-char nesting that exceeds Win32 MAX_PATH.

**Fix:** never `rglob` the worktree root. Use `git status --porcelain` for dirty classification and `os.walk` with `dirs[:] = []` when name in `[".codex-review","node_modules",".git"]`. Same for `j1-c3` manifest walk.

## 4. TSC/ESLint Windows invocation

- `npx tsc --noEmit` alone prints help + exit 1 (no project). Correct: `node frontend/node_modules/typescript/bin/tsc --noEmit --project frontend/tsconfig.json` → exit 0.
- `npx eslint e2e/... --max-warnings 0` exits 2 with "No files matching pattern" (cwd) and v9 `eslint.config.js` migration warning. Correct: `node frontend/node_modules/eslint/bin/eslint.js --max-warnings 0 C:/.../frontend/e2e/s09-t06bc4-*.ts` abs paths → exit 0.

## 5. Prompt heredoc EOF

`cat > prompt.txt << 'PROMPT'` with quotes/apostrophes dies `unexpected EOF while looking for matching ''` — worker never receives prompt. Use `write_file` tool to create `output/<lane>/prompt-*.txt` then dispatch `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner> -z "$(cat .../prompt.txt)" -m meta --yolo` with `background=true, notify_on_complete=true`.

## 6. T06B Chromium x2 production logistics verified

Isolated DB `prod-backend-root/data/motionforge.db` + runtime root + ports sequential (8213→8214 not concurrent) + deterministic Windows launcher `spawn python -m uvicorn shell:false` + `waitForBackendReady` HTTP poll + `finally` cleanup + captured `prod-backend-*.log`/`prod-frontend-*.log` + `.last-run.json {"status":"passed"}`. Run2 may persist only `.last-run.json` — still green but note thinner trace. Transient 504/Network → 5m backoff same session same model, max 3 writers only in P-C5.

J3 final gate sequence proven: 13/13 → T03 40 + T04 24 + T05 19 isolated → Ruff 0 Mypy 0 → TSC 0 ESLint 0 → Alembic 1 head → diff-check 0 → 119 dirty classified (T03 2 + T04 3 + T06B 12 + EVIDENCE 18 + TEMP 2 + SPRINT_BASE_M 82 pre-existing) → owned ports 8201/3115/8212 released, 8099/3014 preserved → `TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`.
