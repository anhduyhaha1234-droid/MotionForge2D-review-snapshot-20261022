# S10-C4/C4A final exit gates — ESLint scope precedent, basetemp sensitivity, SUPERSEDE pattern (verified 2026-08-30)

Complete C4/C4A arc: PREP → T01C-C6 (J1) → T03-C4 (J2) → T04A-C4 (J3) →
T01A-C4A static unblock (J4) → T04A-R2 lineage-hash fix (J4') → T04A-R3
long-path reader fix (J4'') → T04C-C3 two runs PASS → EXIT gates → terminal
`SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`.

## Exit-gate sequence that worked (run AFTER all writers exit, stable tree)

1. J1-v4 re-hash 13/13 + EOL guard (packaged `scripts/j1v4_rehash.py`).
2. Full `tests/test_s10*.py` **twice** on distinct fresh roots, `-p
   no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>` — final
   counts were **206 passed ×2** (273.5s each), zero fail/skip.
3. Exact Ruff 17-file (9 prod + 8 tests) `All checks passed!`; exact mypy
   9-file literal `Success: no issues found in 9 source files`; `git diff
   --check` 0.
4. Alembic one head `a10b11c12d3e` (run from WORKTREE cwd, never MAIN).
5. OpenAPI materialized: 261 paths / 327 ops / zero duplicate operationIds.
6. Frontend: TSC 0; **scoped Apply ESLint per PRECEDENT (see below)**; fresh
   production build + validator 7/7.
7. DB/file/media truth per run (read-only probes): attempts, reuse,
   publications, structural rows non-empty, SHA/size/ffprobe match.
8. Source sweep 8 patterns = 0 (synthetic staging, input-change bypass,
   fallback authority, perturb, fixed arrays, mirroring, requeue helpers).
9. Ledger audit: exact owners/model `ocg/deepseek-v4-flash` max/OFF,
   no Manager writes, ports free, HEAD unchanged.
10. Append registry + sprint report **after** all gates — write terminal line
    LAST, after cleanup.

## ESLint scope precedent — pre-existing errors vs C4 regressions

The C4A exit gate ran `eslint "src/features/apply/**"` (S09/C2/C3 precedent)
and exited 0. A BROADER probe adding `"src/app/(app)/apply/**"` then failed 1
error: `react-hooks/set-state-in-effect` at
`frontend/src/app/(app)/apply/page.tsx:90` (`setRunId(urlRunId)` inside
`useEffect`). Classification that kept the gate honest:

- **mtime attribution first**: `ls -la --time-style=full-iso` showed
  `page.tsx` mtime **2026-08-29 03:16 — BEFORE C4 started (19:55)** and
  `git status` showed the file untracked (T04B-era). Nothing in C4/C4A ever
  touched it (re-check: `find src/features/apply -newermt <c4-start>`
  empty). → pre-existing, T04B-owned (frozen), NOT a C4 regression.
- **Scope precedent wins**: earlier rounds validated ONLY
  `src/features/apply/**`; the (app)/apply page was never in the scoped
  gate's surface. Report the precedent-scoped run as the gate (exit 0) and
  carry the broader-surface error forward as an explicit
  `Carry-forward P2 (pre-existing, T04B-owned, untouched in C4) — for Codex
  decision` item in registry + sprint report. Do NOT let a broadened lint
  surface retroactively fail an otherwise-green gate, and do NOT self-fix a
  frozen owner's file.
- General rule: whenever an exit-gate lint/static command is broader than
  the precedent scope, classify every failure by mtime vs sprint start +
  git-status ownership before labeling it a regression.

## Basetemp-length sensitivity (Windows path tests)

A path-length test (`test_c4_nested_root_over_260_atomic_zero_orphan`) FAILS
when the pytest basetemp root itself is short (`C:/tmp/tmp.XXX` → nested
target only 250 deep < 260) and PASSES when basetemp is long (deep >260).
This is an ENVIRONMENT precondition, not a code regression — the worker
proved it by re-running the single test with a long basetemp (1 passed) then
the full suite (197 passed). When a worker reports this shape, re-verify the
single test yourself with a long basetemp before accepting the green claim;
never let "fail on short basetemp" abort a gate, and never let "pass on long
basetemp" hide a real MAX_PATH bug (the C4 long-path findings were real —
see `s10-c4a-t04a-longpath-reader-fix.md`).

## SUPERSEDE pattern for false prior claims (registry / sprint report)

The C3 registry entry self-contradicted (`ALL 9 GATES GREEN` while recording
`15 errors in 3 files` and a `fair` waiver). C4 exit did NOT rewrite that
history — it appended a plainly-marked section:

```
## ... C4 FINAL EXIT — SPRINT_SUBMITTED / ...
### ⚠️ SUPERSEDE — C3 exit claim "ALL 9 GATES GREEN" là FALSE ...
```

with the evidence (mypy 15 → 0/0/0 after C4 closed all carry-forwards) and
the new terminal. Rules: append-only, verbatim old claims remain visible,
new section states "this appendix is final truth". Codex audits this exact
pattern (C2/C3 reviews flagged "Registry claim ALL GREEN tự mâu thuẫn").

## BUILD_ID changes on rebuild — expected, not drift

T04C's two accepted runs validated against BUILD_ID `KIWvay6FvLdiWmVFduSMG`
(manifest `output/s10/_build/frontend-build-manifest.json`). The final exit
gate then ran `node output/s10/run-s10.js --build-only` per §7.6 ("fresh
current production build") which produced a NEW BUILD_ID
(`Ypg2OvkwfOy47aKRUCFMk`, scanned 201, validator 7/7). That is correct
behavior — record BOTH ids in the registry with the reason (runs pinned the
pre-exit manifest; exit gate intentionally rebuilds current tree), so a
later reader does not misread the new BUILD_ID as manifest drift or a secret
tree change.

## Worker log truncated by iteration cap → audit disk evidence instead

T04C-C3 dispatch log can end mid-sentence (4 lines, "đang chặn ở har…"
truncated) because the worker exhausted iterations inside its own report
writing. The Manager cannot wait for a re-summary — audit the disk:
`ls -la output/s10/c4/t04c-c3/` for run dirs, `cat
run*/e2e-results/.last-run.json` (failed/partial runs visible), `env.json`
(BUILD_ID/fixtureSha/exitCode), driver logs, and count chunk `.mp4` /
`.evidence.json` files under the runtime root. Even a FAILED run's artifacts
are evidence: run1-attempt1/attempt2 had 25 rendered MP4 + 25 evidence
sidecars before the harness fix — proof the production render path works
while the harness asserts fail. Distinguish "harness/fixture bug"
(fix allowed in T04C scope) from "production defect" (route to owner) —
both surfaced as spec failures; only code-reading + repro classified them.

## Porcelain count +1 after coordination appends

Baseline 45 porcelain entries; after registry + sprint report C4 appends it
read 46. Verify the delta is exactly the coordination files (docs/pm/
sessions + sprints are themselves untracked S10 write-set) and no foreign
path — `git status --porcelain | grep '^??' | grep -vE 'app/|tests/|docs/pm|frontend/|migrations/'` empty proves it. A +1..2 on your own appends is
normal; a +N or a foreign path is an incident.