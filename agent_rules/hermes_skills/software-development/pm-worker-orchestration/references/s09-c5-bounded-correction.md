# S09-C5 bounded correction — F1–F6 packet (2026-08-27 Codex review, 282-line prompt)

## Entry conditions
- RULES_LOADED: `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c…` + HEAD `ee10e55…` pinned first.
- J1-v4 authority: `output/s09/20260823_sprint_full/j1-c3/renderer_freeze_manifest_v4.json` `ae92247b8bfd…` 13/13 byte-hash before AND after every wave. Drift → hard stop.
- Starting terminal: `S09-C4 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW` after green 43-test / TSC / ESLint green but 6 findings.
- Combo `meta` (round-robin `cmc/meta`+`ocg/muse-spark-1.2-contributor`), reasoning `max`, fallback disabled, TTFB 900. Manager session `20260827_020702_b17b35`. Sequential DAG `T03 -> J1 -> T04 -> J2 -> T06B -> J3` (one writer in shared worktree).
- `MOTIONFORGE_DATABASE_URL` unset per task; fresh `basetemp`/runtime/output/ports per gate.

## Findings → owner mapping (exact Codex F1–F6)

| Finding | Severity | Owner session | Locus | Shape | Prescribed fix + forbidden alternative |
|---|---|---|---|---|---|
| **F1 Windows long-path** | P1 | T03 `20260824_031524_a6bb2a` | `app/workflow/s09_demo_jobs.py:1871-1877` bind vs `:1306-1310` reader | `final_path.is_file()` without `_win_long_path`; 279-char artifact falsely missing | Use established long-path contract for bind existence/read/hash. Add deterministic targeted regeneration at final artifact path ≥260 chars, d4 only, d1/d2/d3 bound without renderer. |
| **F2 zero-mutation false-green** | P1 | T04 `20260824_052859_c6e197` | `tests/test_s09_t04_demo_compare.py:607-658` + helper `1590-1646` | Helper commits lineage before collision, `after >= before` only | One transaction/savepoint for helper lineage, or preflight mismatch before any commit. Assert exact equality for artifact/project/video/scene/role/segment/correction/job/checkpoint. |
| **F3 path-dependent frozen ID** | P1 | T03+T04+T06B (canonical owned by T03, mirrored by T04, exercised by T06B) | `s09_demo_compare.py:263-268`, `s09_demo_jobs.py:1518-1523`, `s09-t06bc4-…spec.ts:541-598` | Canonical included `decision_path`; byte-identical copy at new path → `c99da8…` vs `bd21ce5…` | Canonical = `decision content SHA + run-A content SHA + run-B content SHA` only. Same bytes/different path → same ID; genuinely different verified content → different ID; stale/tampered → fail before mutation. T06B may not use byte-identical copy as different-evidence case. |
| **F4 non-reproducible E2E** | P1 | T06B `20260824_131423_423e42` | `s09-t06bc4-targeted-regeneration.spec.ts:561-598` | Generic `bash` → WSL on PowerShell/Node, `C:/` paths invisible; logs/evidence JSON absent; second instance on :8211 never starts | Deterministic Windows launcher (PowerShell/Node), per-instance isolated root/DB/output/ports, captured stdout/stderr + exit, readiness assert, `finally` cleanup. Run Chromium ×2 sequential, persist logs/evidence/screenshots. Git Bash alone not acceptable. |
| **F5 backend gates red** | P1 | T03 `031524_a6bb2a` | `app/workflow/s09_demo_jobs.py:558` I001, `:606/:610/:776/:825/:830` E501, `:776` unused-ignore | Scoped Ruff + mypy fail | Fix within T03 write-set, no ignores/skips/relaxed gates. |
| **F6 reconciliation & cleanup** | P2 | Manager `020702_b17b35` | registry + process tree | Registry leaves T05A/T03/T04/T05B/T06B `PENDING`; gate logs/evidence JSON absent at review; old QA uvicorn/Next trees alive; Manager edited QA scripts/fixtures | Resume exact owners for code/test changes, persist all evidence, reconcile registry to one final table (no stale `PENDING`), terminate only attributed QA trees (never unrelated user processes). |

## Write-set discipline for C5
- **T03** owns `app/workflow/s09_demo_jobs.py` + `tests/test_s09_t03_demo_loops.py` (regression only) — F1/F3 long-path+identity + F5.
- **T04** owns `app/api/routes/s09_demo_compare.py` + `app/schemas/s09_demo_compare.py` (if public contract) + `tests/test_s09_t04_demo_compare.py` — mirrors F3 canonical, F2 transaction helper, long-path ≥260 regression, Ruff/mypy.
- **T06B** owns `frontend/e2e/s09-t06bc4-targeted-regeneration.spec.ts` (+ existing Playwright config only if required, launcher under frontend E2E scope) — F3/F4. Forbidden: `app/**` production, backend tests/fixtures, T03/T04/T05A/T05B, J1-v4, MAIN PM docs. Backend defect → report & stop, Manager resumes T03/T04 then reruns T06B.
- Manager = orchestration/review only; no production/fixture/test edits.

## Acceptance shapes (exit needs ALL reproducible)
1. J1-v4 13/13 byte-identical before & after.
2. T04 suite ×2 at final path ≥260 with real unaffected d1/d2/d3 reuse.
3. Collision mismatch → zero durable mutation exact equality.
4. Frozen ID content-addressed + path-independent; tamper/stale fail-closed.
5. Ruff + mypy + TSC + scoped ESLint + focused T03/T04/T05/T06 + full S09 regression pass.
6. Chromium production ×2 from normal Windows surface, isolated fresh state, durable evidence.
7. Final registry no `PENDING`, exact owner/session/commands/artifacts, all task-owned QA stopped.

Even then manager terminal is only `TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`; Codex decides approval/closure. Never write `APPROVED`/`CLOSED`, open S10/S11/S13, or commit/merge/push.
