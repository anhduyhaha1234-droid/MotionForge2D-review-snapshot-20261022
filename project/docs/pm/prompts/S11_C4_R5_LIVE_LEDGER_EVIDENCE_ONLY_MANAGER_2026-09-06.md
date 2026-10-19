# HERMES PROMPT — S11-C4-R5 Live-Ledger Evidence-Only Closure

Đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
trước mọi preflight hoặc command. Bạn là exact Hermes Manager hiện hành của
S11; Codex là reviewer/gate độc lập. Đây là vòng evidence-only hữu hạn. Không
resume worker và không sửa code.

## 1. Authority and exact continuation

Đọc đầy đủ rules, `AGENTS.md`, `SESSION_PROTOCOL.md`, current
`CODEX_PM_HANDOFF.md`, `ROADMAP.md`, R4 review, binding prompt này, R4 packet
và current canonical tree. Báo `RULES_LOADED` với full path, SHA-256, line
count, actual Git/process/session inventory và mọi discrepancy trước gate.

Current authority:

- `S11-C4-R4 = CHANGES_REQUESTED / NOT_APPROVED`.
- `S11 = NOT_CLOSED`; S12/S13 remain blocked.
- All product-mechanism and durable-test findings are closed. The only open
  finding is truthful live evidence provenance.
- Canonical reviewed worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Reviewed branch/HEAD: `codex/s11-integration` at
  `1f5936d1167a55a583e8849ca67032e61297fe85`, clean and local==remote at
  Codex review. Rediscover it and fail closed if it changed or is dirty.
- Worker R4 commit `7c58c37e786f4b3fdf6b4a37800829bd0359bfda` is already integrated by
  `7e474d4`; INT01 docs commit is `1f5936d`.
- R4 root is immutable history:
  `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260906-210700-R4-final`.

Manager identity is binding:

- Continue exact Manager `20260905_162953_5a5cda` only.
- Nếu prompt này không nằm trong session đó, không chạy gate; báo
  `BLOCKED_MANAGER_IDENTITY` để user chuyển prompt về đúng Manager.
- Do not create another Manager, watchdog or worker.

This file is `PROPOSED_ONLY` while stored. User paste/send vào exact Manager
chat là explicit authority chạy đúng bounded R5 này, không hỏi xác nhận lần hai.

## 2. Route, session and zero-write policy

Keep the user's route:

- provider `muse`, custom 9Router;
- base URL `http://127.0.0.1:20128/v1`;
- exact model `cmc/meta/muse-spark-1.3-contributor`;
- reasoning max, fallback OFF, TTFB timeout 900 seconds.

Record the actual Manager row read-only. Also audit the known implementation
rows read-only:

- owner `20260905_192221_6da09b`;
- competing frozen duplicate `20260905_192249_150b51`;
- frozen old owners `20260903_170546_0d42f6`,
  `20260905_043139_01a91f`;
- Git-only INT01 `20260903_112116_35051c`.

Use Hermes `state.db` only through `mode=ro&immutable=1`. Reconcile stale
`ended_at=NULL` rows against actual process/tool state. There must be no active
implementation writer. Do not send any message to an implementation owner or
INT01. Do not create or resume a session.

Hard zero-write scope inside every repository/worktree:

- no production, test, migration, schema, UI, config or script edit;
- no T03G LOG/REPORT or other PM-session edit;
- no stage, commit, merge, cherry-pick, rebase, reset, restore, clean, stash,
  branch update, tag or push;
- no formatter/fixer, generated source, bytecode or pytest cache;
- no database, fixture, `channels.json`, `data/` or user-data mutation.

The only authorized writes are under the one new external R5 evidence root and
fresh isolated temp/database/output roots named in the ledger.

## 3. Exact R4 evidence defect to supersede

Do not edit or relabel R2/R3/R4 evidence. Copy/index it read-only with hashes.
R5 must state these R4 facts verbatim and close them prospectively:

1. R4 `commands.jsonl` rows 5-21 use the same start and end timestamp
   `2026-09-06T14:33:30+00:00`, including commands reported to take 172.63,
   14.63, 385.62 and 172.85 seconds and later integration/OpenAPI actions.
2. Raw gate mtimes span 14:33:47-15:10:15 UTC; the ledger was last written at
   15:10:33 UTC. Most gate files contain output/exit only, not exact command,
   CWD, timestamps, HEAD and isolated roots.
3. `guard_preresume.json` is a failed missing-script invocation. The failure is
   absent from the old ledger. `g11-guard-postpatch.log` contains only
   `GUARD_EXIT:0` rather than raw verification output.

Never reconstruct R4 timestamps. R5 runs fresh commands and records only their
real R5 times.

## 4. Fresh R5 root and live recorder before the first gate

Before any quality gate, create exactly one new immutable-intent external root
under `C:\Users\Admin\MotionForge2D-evidence\s11-c4\` with suffix
`R5-live-ledger-final`. Record its absolute path once and use no second final
root.

Create these before the first gate:

- `REGISTRY.md`;
- `baseline_manifest.csv` plus byte snapshots for the C4R1 test, T03G
  LOG/REPORT and four protected production files;
- `ledger-runner.ps1` or an equivalent external-root-only runner;
- the runner's SHA-256 and full source;
- empty append-only `command-events.jsonl` and `commands.jsonl`;
- raw Git/process/session preflight artifacts.

The runner, not a later manual summary, must execute every gate. For each gate
it must:

1. append and flush a `START` event before process launch;
2. record monotonic sequence, exact argv/command without secrets, absolute CWD,
   ISO UTC start, reviewed HEAD/tree and all DB/basetemp/cache/port/output roots;
3. capture raw stdout and stderr separately or in one lossless raw artifact;
4. record numeric exit from the actual process;
5. in `finally`, append and flush an `END` event and one final
   `commands.jsonl` row with real ISO UTC end and measured non-negative
   duration;
6. include raw artifact path, SHA-256 and bytes in the final row;
7. preserve failed attempts exactly like passes and never overwrite a prior
   raw file or row.

Prove the recorder with one harmless command whose real duration is at least
two seconds. Its end must be later than start, duration must agree within a
small clock tolerance, and the raw output hash must verify. If this self-test
fails, stop before the closure gates and fix only the external runner.

No ledger row may use a summary label such as `matrix 152` in place of the
exact command. Do not batch multiple shell actions into one indistinguishable
row. Never backfill a start event or invent a timestamp.

## 5. Fresh finite closure ladder

Run serially from the unchanged canonical worktree. For every pytest command
set `PYTHONDONTWRITEBYTECODE=1`, remove repository DB overrides, use
`-p no:cacheprovider`, and assign a fresh unique basetemp/database/output root
that is recorded in the same ledger row.

Required fresh gates:

1. Collect `tests/test_s11_t03g_qc_check_c4r1.py`; exactly 6 nodes.
2. Run the true-contention node alone; exactly 1 pass.
3. Run the BaseException node alone; exactly 1 pass and retain both
   KeyboardInterrupt/SystemExit assertions by source inspection.
4. Run complete C4R1; exactly 6 pass.
5. Run all three T03G files together; exactly 152 pass, zero
   skip/xfail/error:
   - `tests/test_s11_t03g_qc_check_job.py`
   - `tests/test_s11_t03g_qc_check_api.py`
   - `tests/test_s11_t03g_qc_check_c4r1.py`
6. Run both T05A files; exactly 14 pass.
7. Run
   `tests/test_s11_t02_t06_acceptance.py::test_t12_targeted_correction_recompute_restart`
   twice on two distinct roots; 1 plus 1 pass.
8. Run full `tests/test_s11_t02_t06_acceptance.py`; exactly 12 pass.
9. Ruff `--select F` on:
   - `tests/test_s11_t03g_qc_check_c4r1.py`
   - `app/workflow/qc_checks_handler.py`
   - `app/workflow/job_service.py`
   - `app/persistence/qc_check_runs.py`
   - `app/services/qc_checks/registry.py`
10. Mypy on `qc_checks_handler.py` plus `registry.py`; zero errors. Run
    `job_service.py` separately and truthfully retain its two known inherited
    `no-any-return` findings at lines 542 and 727 unless actual source moved.
11. `git diff --check`, Alembic sole-head and direct OpenAPI duplicate-ID scan;
    expect head `f9a0b1c2d3e4`, 274 paths, 340 operations, zero duplicate IDs
    and nine QC operations. Record the exact OpenAPI command/helper hash.

Use the already-integrated test exactly as committed. Node arithmetic changes,
red focused gates, source drift or a different canonical HEAD are fail-closed;
do not patch or ask a worker to make green.

## 6. Actual-test negative controls

Create any helper only in the R5 evidence root and hash it before execution.
It must import the committed C4R1 test module and mutate its payload in memory;
it must not copy over or write a repository file.

Prove both:

- delay caller B before its thread-id/lock-attempt path, shorten the in-memory
  marker wait for a bounded run, and require the committed test function to
  raise `AssertionError` because `b_lock_attempted_wait` is false;
- corrupt entry point, version and description in the in-memory final snapshot
  while retaining names/order, and require the committed test function to
  raise `AssertionError` on exact snapshot comparison.

The helper exits 0 only if both mutants are rejected. Preserve its source,
exact command and raw output through the live runner.

## 7. Truthful zero-write guard

Because R5 has no repository write phase, do not claim a missing
`write_set_guard.py` invocation passed. Capture absolute path/hash/bytes/lines
for these files before and after all gates and compare them exactly:

- `tests/test_s11_t03g_qc_check_c4r1.py`;
- T03G LOG/REPORT;
- `app/workflow/qc_checks_handler.py`;
- `app/workflow/job_service.py`;
- `app/persistence/qc_check_runs.py`;
- `app/services/qc_checks/registry.py`.

Store raw baseline, raw postimage and a machine-readable comparison listing
every row. Also record full `git status --porcelain=v1`, HEAD, local remote ref
and tree hash before and after. Success means exact hash equality, empty
porcelain and local==remote. Any drift is terminal; do not repair it.

Index the R4 manifests and old raw gate files by absolute path, hash and bytes.
The R4 packet remains historical and must not be edited.

## 8. Final packet contract

Under the same R5 root create:

- postimage manifest and exact baseline/post comparison;
- complete `command-events.jsonl` and `commands.jsonl`;
- runner source/hash and recorder self-test;
- raw session/process audit;
- raw outputs for every fresh pass and failure;
- actual-test negative-control source/output;
- Alembic/OpenAPI artifacts;
- final Git/local-remote/quiescence artifact;
- `NEXT_REVIEW_PACKET.md`.

Before submission, validate mechanically:

- sequence numbers are unique, contiguous and monotonic;
- every final row has one earlier START and one END event;
- every end is later than or equal to start and every non-trivial gate has
  positive duration;
- rows follow actual artifact mtimes/order within normal filesystem tolerance;
- every raw path exists and its hash/bytes match;
- every failed attempt is present;
- no repository/worktree file changed.

The packet must state that R4's false timestamps are superseded, not corrected
in place. It must not claim Manager approval or sprint closure.

## 9. Terminal condition

Only when every live-ledger, gate, provenance and zero-write row is green,
report exactly:

`SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Otherwise report one bounded `BLOCKED_*` state with exact raw evidence. Do not
resume a worker, modify the repository, open S12/S13 or self-dispatch Codex
review. Start immediately after user dispatch with `RULES_LOADED`, exact
Manager identity, canonical HEAD and the new R5 root.
