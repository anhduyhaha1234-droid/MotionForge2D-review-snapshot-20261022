# Playwright harness correction patterns (S07 round-2, 2026-08-22)

Session-specific detail behind worker-orchestration pitfalls 43/44/48: the
S07-T03 real-vertical Playwright harness needed a correction wave that
touched ONLY harness files, with manager-independent verification.

## Canonical config first

Before diagnosing any e2e failure:
1. Identify the sprint's authoritative config — for S07 it was
   `frontend/playwright.s07t03.config.ts` (webServer array wiring
   `python frontend/e2e/s07-t03-boot-backend.py` on :8004 + `next dev`
   on :3014, projects desktop + mobile-390).
2. Read it fresh (`git status` mtime + content). A stale sibling
   (`playwright.s07t03-real-vertical.config.ts`, no boot wrapper) produced
   a WRONG "harness never seeds" diagnosis and a wasted correction.
3. Reproduce findings against the canonical file only.

## F2 — os.execv orphan (Windows)

Failure chain per run: wrapper seeds DB → `os.execv(python, [python,
"-m", "uvicorn", ...])` → Windows spawns NEW python PID, wrapper exits →
Playwright kills the dead wrapper PID → uvicorn orphaned, LISTENING :8004 →
runner never exits.

Verified fix shape (writer applied):
```python
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", ...])
try:
    proc.wait()
except (SIGTERM/SIGINT):
    proc.terminate()
```
Manager gates after each run: `netstat -ano | grep :8004` EMPTY +
runner self-exit (log shows shell prompt back / EXIT marker).

## F1 — dual-project state bleed

Config runs 4 tests = 2 scenarios × 2 viewports over ONE seeded temp DB.
Scenario I creates natural-key mappings; second execution → 409
idempotency-key-bound-to-different-payload (after repin to V2) or
already-exists. Single-project runs pass — that asymmetry IS the tell.

Fix (writer): at scenario start, list+delete existing mapping for target
project/role AND project C (cross-project row); publish block handles
already-published (reuse draftId instead of failing). Trace toggled to
"on" temporarily for diagnosis, reverted to on-first-retry.

## Correction dispatch prompts (what landed first-try)

Each correction = resume owner session via
`hermes chat --resume <sid> --provider muse --model ocg/muse-spark-1.2-contributor -q "$PROMPT" --yolo --pass-session-id --max-turns 200 --source tool`,
prompt written to Temp file, dispatched in background with notify.
Prompt structure: preflight pins (HEAD/dirty/env) → findings WITH manager
reproduction evidence (DOM snapshot, netstat PIDs) → expected behavior →
EXCLUSIVE write-set (explicitly listing sibling writer's files as
forbidden when parallel) → resource split (T02 got 8014/3024, T03 kept
8004/3014) → gates with literal expected outputs (4 passed ×2, different
seed UUIDs, empty netstat) → report contract (LOG/REPORT append,
TASK_SUBMITTED not APPROVED).

## Manager verification battery (order matters)

After BOTH writers stop (mutex):
1. Read writer evidence from disk; diff claims vs reality (pitfall 46).
2. Global static: ruff app+tests, mypy, tsc, eslint ., next build.
3. pytest full nine-file suite + regression cluster (background, isolated
   basetemp, env -u MOTIONFORGE_DATABASE_URL).
4. Playwright both configs sequentially in one background lane, then
   netstat check.
5. Alembic single head + upgrade-head on temp SQLite + PRAGMA
   foreign_key_check (needs mkdir of the temp root FIRST — SQLite cannot
   create the file if the directory is missing; alembic also needs
   MOTIONFORGE_DATABASE_URL exported for THIS probe while pytest used env -u).
6. Protected hashes: MAIN HEAD + data/motionforge.db size/mtime.
7. models.py / migrations mtimes must predate the run window (writers must
   not have touched schema).

## Dependency-blocked parallel pattern (pitfall 47)

T03's new UI-repin test depends on T02's picker fix. Sequence that worked:
T03 writes test + runs PW once capturing the expected failure as
BLOCKED_DEPENDENCY_T02 evidence (0/4 at submit-success with the exact 409
symptom) → T02 lands fix → manager re-runs T03 suite → 0/4 → 4/4 PASSED is
end-to-end proof through production UI. Never let the dependent writer fake
green or touch production to unblock itself.

## Residual risks observed

- Writer smoke script failed (`deps._job_service` None outside FastAPI
  lifespan) but REPORT claimed pass — coverage replaced by independent
  manager gates (pitfall 46).
- ESLint warnings (9, pre-existing img-element etc.) are acceptable;
  errors are not.
