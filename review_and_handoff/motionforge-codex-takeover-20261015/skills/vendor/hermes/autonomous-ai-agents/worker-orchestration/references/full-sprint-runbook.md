# Full-Sprint Manager Runbook — S09 pattern (2026-08-23/24)

One manager session running an ENTIRE sprint (T00-I01..I05 → T01 → T02 →
T03 → T04 → T05A/B → T06A/B) under full-sprint authority from the external
reviewer. What actually happened, with timings, for reuse.

## Wave DAG as executed

| Wave | Tasks | Mode | Duration | Resumes needed |
|---|---|---|---|---|
| 0 | preflight/registry/packets | manager-only | ~10 min | — |
| 1 | I01 ∥ I04 | parallel writers | 2.5–3 h | 1 each |
| 2 | I02 ∥ I03 | parallel writers | 4–5 h | 2 each |
| 3 | I05 measured run | single writer | 40 min | 1 |
| 4+ | T01 resume-owner → T02 → T03 → T04 → T05A → T05B → T06A → T06B | serial | 1h16–2h30 each | ~50% |

Actual: dispatch→T04 verified in ~19.5 h continuous; silent worker deaths
consumed ~5 of those hours across 6 resume rounds.

## TASK.md packet template that worked (per task)

Sections in this order:
1. **Role** — provider/endpoint/model/reasoning/fallback pinned verbatim.
2. **Bước 0** — rules file read (RULES_LOADED marker), overlay read,
   worktree guard, MOTIONFORGE_DATABASE_URL UNSET, per-lane basetemp +
   `-p no:cacheprovider`.
3. **Context đã verified** — what prior tasks delivered, with the exact
   symbols/files to import (never line numbers), current alembic head
   labeled "discover live, don't hard-code".
4. **Outcome bắt buộc** — numbered deliverables with fail-closed semantics.
5. **Acceptance gate** — binary checks ×2 runs, ruff/mypy/tsc/eslint scoped
   to the right file types, OpenAPI removed=0, self-audit write-set.
6. **Write allowlist (NGHIÊM)** — explicit NEW vs existing-file-additive.
7. **FORBIDDEN** — MAIN, data/**, other lanes' files, network, git history.
8. Close: "STATUS: TASK_SUBMITTED rồi STOP" (never self-APPROVED).

Frozen thresholds go IN the packet before any measurement; add "không tune
threshold sau khi thấy kết quả".

## Registry rhythm

Append one row per event BETWEEN waves or after writer exit only:
dispatch / early-death + evidence / resume dispatched / DONE + manager
verify numbers. Rows carry: local time +07, UTC, bold verdict vocabulary
(TASK_MANAGER_VERIFIED_PENDING_CODEX_REVIEW), and the exact gate numbers
(41 passed ×2, OpenAPI 221→229). This registry is the Codex handoff spine.

## Silent-death/resume loop (epidemic rate: 50%)

Triage signature: log size frozen over two spaced samples + tasklist
python.exe = 0 + no wrapper EXIT= line. Wrapper EXIT=0 ≠ done.

Resume packet structure (landed first-try every time):
```
RESUME — <TASK ID> (session của bạn là <sid>).
TRẠNG THÁI ĐÃ CÓ (Manager verify bằng disk): ...what's on disk...
VIỆC CÒN LẠI: 1..n (exact remaining steps)
KHÔNG sửa gì ngoài: ...
```
Then `--resume <sid>` background launch. Never a new session for the Task ID.

## ETA reporting to the user

User asks "bao giờ xong" repeatedly. Give a dated table (wave → start →
finish estimates), total window, best/expected/worst case, and top risks.
Re-anchor after every slip (silent deaths pushed S09 ~4 h) — update the
table rather than repeating the old date. Use FULL dates (CN 23/08 not
"25/08 Chủ nhật") — one wrong weekday erodes trust.

## Manager verification battery per task

1. REPORT.md STATUS=TASK_SUBMITTED + cited evidence files exist.
2. Run focused suite yourself ×2 (different basetemp, no:cacheprovider).
3. Legacy/prior-task suites re-run (regression proof).
4. ruff/mypy on Python write-set ONLY; tsc/eslint on TS write-set ONLY
   (ruff-on-.ts = false-failed gate, 561 noise errors).
5. OpenAPI path count delta (removed must be 0; additive expected).
6. Write-set audit: `find app tests -newermt "<task window>"` outside
   allowlist = finding; build artifacts (tsconfig.tsbuildinfo) acceptable.
7. For migrations: heads via ScriptDirectory, round-trip byte-identical,
   models.py difflib zero-removed vs pinned baseline hash.
8. Registry append with verdict BEFORE dispatching next wave.

## What consumed time (so future estimates are honest)

- Worker silent deaths + resumes: ~5 h across 6 rounds (biggest cost).
- Manager independent verification: 15–25 min/task (worth it — caught
  7/9 suite, missing CHECK constraint, dup-PK seed, E2E testid bug).
- Parallel waves saved ~3 h vs serial for I01∥I04 and I02∥I03.
