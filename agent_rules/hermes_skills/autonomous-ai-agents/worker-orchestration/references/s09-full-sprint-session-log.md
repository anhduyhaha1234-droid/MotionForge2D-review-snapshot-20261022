# S09 Full-Sprint Run — Session Log & Gate Evidence (2026-08-23 → 24)

Condensed session-specific record backing `SKILL.md` pitfalls 56, 62–71.
Canonical rules: `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`.

## Sprint shape (full-sprint authority from Codex)

- 11 tasks: T00-I01..I05 (foundation) → T01 resume-owner → T02..T06B serial.
- Wave DAG actually executed:
  - W1: I01 ∥ I04 (disjoint write-sets)
  - W2: I02 ∥ I03
  - W3: I05 measured run
  - T01 = RESUME owner `20260822_232748_b4b2ad` (foundation kept per Codex verdict)
  - T02→T03→T04→T05A→T05B→T06A→T06B serial, one new owning session each.
- Model route for every NEW session: provider custom @ 9Router
  `http://127.0.0.1:20128/v1`, model alpha, reasoning max, fallback disabled.

## Task ledger (owner sessions + corrections)

| Task | Owner session | Corrections | Final gate evidence |
|---|---|---|---|
| T00-I01 structural lock | 20260823_120521_ae2b4f | R1 (crash EXIT=4; ORM missing revision CHECK + dup PK 'rr1') | 20 passed ×2; heads=['d8e9f0a1b2c3']; models.py removed=0 |
| T00-I04 test normalization | 20260823_120528_a26f5c | R1 (EXIT=0 but died before REPORT) | 236 passed ×2; adversarial fake-table/fake-revision FAIL-closed |
| T00-I02 renderer router | 20260823_173054_faaf53 | R1+R2 (2 silent deaths) | 28 passed ×2; real NVENC bench 6.15ms/fr |
| T00-I03 benchmark harness | 20260823_173318_69a813 | R1+R2 (2 silent deaths) | 19 passed ×2; frozen SHA before measure; fixtures byte-identical ×2 |
| T00-I05 measured run | 20260823_233406_8d5b7b | R1 (died pre-REPORT) | frozen SHA match; ref media hash re-verified by manager; core ×2 identical |
| T01 reskin SL completion | 20260822_232748_b4b2ad (RESUME) | none | 41 passed ×2; OpenAPI 221 additive; tsc/eslint 0 |
| T02 pose-swap adaptive | new sess | none | 37 passed ×2; legacy 69 passed; smoke bench overall_pass=True |
| T03 demo loops/jobs | 20260824_031524_a6bb2a | R1 (pre-REPORT death) | 10 passed ×2; NO migration needed; OpenAPI 229 pure additive |
| T04 compare API/UI | 20260824_052859_c6e197 | R1 (E2E capabilities testid) | 9 passed ×2; PW 3p/1skip by-design |
| T05A correction backend | 20260824_072626_645cde | R1 (3 failed tests) | 36 passed ×2; migration b3c4d5e6f7a9 single head |
| T05B correction UI/E2E | 20260824_093602_af7c26 | R1 (early exit on schema read) | 36 backend green; PW 2p/2skip ×2 idempotent |
| T06A approval backend | new sess | none | 30 passed ×2; no migration needed |
| T06B approval UI/E2E | 20260824_131423_423e42 | R1-R4 (model-empty bursts) | 30 backend green; PW ×2 runs 2p/2skip |

## Silent-death epidemic (pitfall 62) — counts

- Hard crash mid-edit: 1 (I01 EXIT=4).
- Wrapper EXIT=0 but died mid-work without REPORT: 7
  (I04, I02, I03, I05, T03, T04, T05B-early).
- Model-empty-content early exits: 3 consecutive on T06B (R1/R2/R3), R4 with
  shorter stepwise prompt finished. `/v1/models` stayed 200 throughout —
  health probes do NOT catch empty-completion bursts.
- Every recovery = state.db first-user-message disambiguation → write a
  resume packet stating DONE-on-disk + exact stopping point + remaining steps
  only → `--resume <sid>` background launch. Zero second-owner violations.

## Final-gate findings (pitfalls 66/69/70)

Run 1 (whole worktree): `4 failed / 238 passed / 1526 errors`.
- FG1: stale expected-tables allowlist in `test_durable_job_persistence.py`
  (missed by I04 allowlist; 6 additive tables incl. 2 that pre-dated sprint).
  Fixed via copy-pattern of normalized sibling; adversarial plant-a-fake-table
  proof retained fail-closed behavior; 47 passed ×2 after fix.
- FG2: stale hard-coded HEAD constants in 4 migration-test files after T05A's
  new revision (`HEAD = "b2c3d4e5f6a7b"` ×2 predating the sprint itself,
  `"d8e9f0a1b2c3"` ×2). Fix = live `get_heads()` discovery preserving each
  assertion's meaning; never weaken single-head checks.
- 1526 errors = Windows WinError-32 tmpdir-rmtree teardown noise (SQLite
  handle lifetime). Judge gates on FAILED list; fresh short basetemp per run;
  engine.dispose() in the offending fixture if it recurs.
- Round-trip note: downgrade-to-base blocked by S06 irreversible migration BY
  DESIGN — prove new revision round-trip against its parent instead.

## User-interaction notes

- ETA requests came repeatedly ("bao giờ xong"); answer format that worked:
  current-wave status table + dated milestone table (FULL DD/MM dates,
  weekday verified via `date`) + explicit "không blocker" line.
- User correction instances this sprint: weekday error in ETA table;
  "làm toàn bộ đi" (full autonomy grant); "có chia subagent được không"
  (answer: parallel writers already at max safe concurrency per rules —
  extra production subagents would violate one-owner-per-task).
- Registry rhythm: append-only rows at wave boundaries and after every
  worker exit; manager errors (ruff-on-.ts false gate) recorded transparently.
