# HERMES PROMPT — S11-C4-R4 Deterministic Lock-Attempt and Evidence Closure

Đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
trước mọi preflight hoặc dispatch. Bạn là Hermes Manager hiện hành của S11;
Codex là reviewer/gate độc lập. Manager không sửa production, test, migration,
UI hoặc config.

## 1. Authority and exact continuation

Đọc đầy đủ rules, `AGENTS.md`, `SESSION_PROTOCOL.md`, current
`CODEX_PM_HANDOFF.md`, `ROADMAP.md`, R2/R3 verdicts, binding R3 prompt,
T03G/INT01 LOG+REPORT, R2/R3 evidence roots, read-only Hermes state and current
source/tests. Báo `RULES_LOADED` kèm full path, SHA-256, line count, actual
Git/process/session inventory và mọi discrepancy trước dispatch.

Current authority:

- `S11-C4-R3 = CHANGES_REQUESTED / NOT_APPROVED`.
- `S11 = NOT_CLOSED`; S12/S13 remain blocked.
- Canonical reviewed worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Reviewed canonical branch/HEAD:
  `codex/s11-integration` at
  `4f2c787124001c9f93043669d95b689935281058`, clean and local==remote at
  Codex review. Rediscover it; do not assume it stayed fixed.
- R3 worker commit: `d9c439b6fd9ada3a3d1e39d6c3396e4cc02980cf`.
- R3 INT01 merge/docs: `67b4acf` then `4f2c787`.
- This file is `PROPOSED_ONLY` while stored. User paste/send vào đúng Manager
  chat là explicit authority chạy đúng bounded R4 này, không hỏi xác nhận lần
  hai.

Manager identity is binding:

- Continue exact Manager `20260905_162953_5a5cda` only.
- Nếu prompt này không nằm trong session đó, không dispatch; báo
  `BLOCKED_MANAGER_IDENTITY` để user chuyển prompt về đúng Manager.
- Không tạo Manager khác, watchdog khác hoặc vòng poll nền khác.

## 2. Route and owner policy

Use the latest user route for the Manager and resumed worker:

- provider `muse`, custom 9Router;
- base URL `http://127.0.0.1:20128/v1`;
- exact model `cmc/meta/muse-spark-1.3-contributor`;
- reasoning max, fallback OFF, TTFB timeout 900 seconds.

Record actual Manager and worker model/config rows read-only. Do not use or
fall back to 1.2, DeepSeek, `ocgfree`, `auto` or another alias.

Session ownership:

- exact implementation owner to resume:
  `20260905_192221_6da09b`;
- same Task ID: `S11-T03G-C4-R2-RECOVERY`;
- competing duplicate permanently frozen:
  `20260905_192249_150b51`;
- old owners remain frozen:
  `20260903_170546_0d42f6`, `20260905_043139_01a91f`;
- Git-only INT01 remains `20260903_112116_35051c` and is resumed only after
  implementation terminal.

Use Hermes `state.db` only via `mode=ro&immutable=1`; never copy, vacuum or
mutate it. Reconcile stale `ended_at=NULL` rows against actual process/tool
state. Prove no active writer before resume. Never create a third implementation
session. Duplicate writer is terminal `BLOCKED_ROLE_VIOLATION`.

## 3. Fresh R4 evidence root before resume

R2 worker worktree/branch:

- `C:\Users\Admin\MotionForge2D-worktrees\s11-c4-r2`
- `codex/s11/c4-r2` at R3 tip `d9c439b`

It intentionally retains five untracked incident files under
`docs/pm/sessions/S11-T03G/evidence/c4r2/`. Enumerate each path/hash/bytes/
logical-lines/mtime and preserve them byte-exact. Do not delete, modify, move,
stage or commit them. Never call clean/stash/reset/restore.

Before sending any worker message, create one fresh immutable external root
under `C:\Users\Admin\MotionForge2D-evidence\s11-c4\` with suffix
`R4-final`. Baseline the actual clean R3 tip and capture byte snapshots before
resume for:

- `tests/test_s11_t03g_qc_check_c4r1.py`;
- T03G LOG/REPORT;
- `app/workflow/qc_checks_handler.py`;
- `app/workflow/job_service.py`;
- `app/persistence/qc_check_runs.py`;
- `app/services/qc_checks/registry.py`;
- T03G job/API tests;
- all five untracked incident files.

The R4 baseline must show current committed test hash/bytes/lines before the R4
patch, not an already-patched R4 image. Create `REGISTRY.md`, baseline manifest,
verified snapshots, raw guard JSON and a real append-only `commands.jsonl`
before resume.

Every `commands.jsonl` row must contain sequence number, exact command, cwd,
start/end ISO timestamps, reviewed HEAD/tree, DB/basetemp/cache/port/output
roots, numeric exit and raw stdout/stderr artifact path. Index failed attempts
as well as passes. Do not reconstruct old commands as if they ran in R4.

Also retain raw, read-only provenance:

- selected Hermes session rows and relevant message/tool rows proving exact
  owner, model and patch operations;
- R2 message 176346 and the five incident files;
- the raw R2 first matrix failure `129 failed, 9 passed, 13 errors` and its
  superseding green run, copied byte-exact or indexed by absolute path + hash;
- R3 root inventory proving `commands.jsonl` absent and
  `lanes/r3-resume/` empty;
- a truthful R2→R3→R4 supersession map.

Never edit R2/R3 evidence history.

## 4. Finite test-only correction

Resume exact owner `20260905_192221_6da09b`. No new worker session.

Exclusive write-set:

- `tests/test_s11_t03g_qc_check_c4r1.py`;
- append-only `docs/pm/sessions/S11-T03G/LOG.md`;
- append-only `docs/pm/sessions/S11-T03G/REPORT.md`.

Production is frozen: no edits to handler, registry, job service, persistence,
detectors, migrations, schemas, frontend, T05/T06, S10, S12 or S13.

Correct the existing true-contention node without adding/removing pytest nodes:

1. Keep caller A paused inside the real explicit-registration operation while
   the real production RLock is held.
2. Add deterministic proof that caller B reaches the lock-acquire boundary.
   Preferred test-only mechanism: temporarily replace
   `handler._BOOTSTRAP_LOCK` in the clean subprocess with a context-manager
   probe that delegates acquisition/release to the original real RLock and
   signals `b_lock_attempted` only for the named B thread immediately before
   delegating to the real lock. Restore the original lock in `finally`.
3. Start B while A is paused. Bounded-wait for `b_lock_attempted=True`; while A
   still owns the real lock, assert B has not returned and remains live. Only
   then release A. A fixed sleep, `Thread.is_alive()` alone or a marker set
   before B calls bootstrap is not proof.
4. Make every failure path release events and restore monkeypatches so a failed
   assertion cannot leave a child hanging. Keep all joins bounded.
5. Before clearing the registry for the race, derive/capture the exact expected
   clean revision map and exact ordered four-field snapshot
   `(name, entry_point, version, description)`.
6. Caller B must return its complete revision dictionary, not only its length;
   assert it equals the exact expected ten-entry map.
7. Immediately after both joins and before any repair/bootstrap/cleanup, assert
   the final four-field snapshot equals the exact expected snapshot and names
   equal the exact band order.
8. Preserve A's exact `RunQcChecksError / QC_RUN_BOOTSTRAP_CONFLICT` plus
   `RuntimeError` cause assertions and all existing R1/R2/BaseException rows.
9. No production change and no post-thread repair before final assertions.

Expected arithmetic remains exactly 6 C4R1 nodes and 152 all-T03G nodes. If it
changes, stop and explain; do not alter assertions to chase green.

## 5. Patch-only safety

Existing files may be edited only with bounded patch/apply-patch calls after
verified preimages. Prohibit `write_file`, heredoc/direct Python writers,
`Path.write_text`, redirection, full-file replacement, copy-overwrite,
`ruff --fix`, reset, restore, rebase, clean, stash and force-push. Worker creates
no evidence/helper file inside the worktree. Manager owns external evidence.

After each patch, record hash/bytes/lines and run the write-set guard. Any
direct-write, production drift or competing-session recurrence is terminal;
do not retry with another owner.

## 6. Verification and integration order

Run serially with `PYTHONDONTWRITEBYTECODE=1`, DB unset, cache disabled and new
isolated roots:

1. Collect C4R1: exactly 6 nodes.
2. Run only the corrected true-contention node. Independently inspect source
   structure: B's marker must occur at delegated lock acquire, B must be
   observed after that marker and before A release, full revisions and exact
   final four-field snapshot must be compared.
3. Run the BaseException node alone; verify both KeyboardInterrupt/SystemExit.
4. Run the four R2/R3 micro nodes, then complete C4R1: 4 and 6 pass.
5. Run all three T03G modules: exactly 152 pass, zero skip/xfail/error.
6. Run T05A 14; dedicated T12 twice on distinct roots; full T06 12.
7. Run Ruff `--select F` on the test plus four binding production paths,
   two-file binding mypy, separately record the two known `job_service.py`
   no-any-return findings, and run `git diff --check`.
8. Verify production/protected hashes are byte-identical to R4 baseline. Commit
   only the three allowed files on the existing worker branch.
9. Resume exact INT01 after all writers stop. One conflict-free no-ff merge is
   authorized; conflict aborts without manual resolution.
10. On integrated tree run post-merge T03G 152, Alembic sole-head and direct
    OpenAPI duplicate-ID scan. R3 T01 64/S10 270/S10 API 71 logs may be retained
    only after proving their production/test inputs are byte-identical and
    explicitly labeling them retained rather than fresh.
11. Perform final guard, accurate process/port quiescence, clean canonical Git,
    and one non-force push proving local==remote.

A broad green never waives a red micro, source-structure row or evidence row.

## 7. Final packet contract

Create postimage manifest, raw final guard, raw model/session audit,
`commands.jsonl`, final Git/quiescence log and `NEXT_REVIEW_PACKET.md` under the
new R4 root. The packet must map each Codex R3 finding to exact code lines,
negative-control evidence, raw gate files and final hashes. It must state all
failed attempts and inherited known findings. Do not claim a missing artifact
exists, do not label a scheduler delay as lock contention, and do not say
“exact snapshot/revisions” unless values are compared exactly in the committed
test.

## 8. Terminal condition

Only when every test, provenance and packet row is green, report:

`SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Manager never writes `APPROVED` or `CLOSED`, never opens S12/S13 and never
self-dispatches Codex review. Start immediately after user dispatch with
`RULES_LOADED`, exact Manager identity, fresh R4 preimage root, route/session
audit and zero-writer proof; then resume only `20260905_192221_6da09b`.

