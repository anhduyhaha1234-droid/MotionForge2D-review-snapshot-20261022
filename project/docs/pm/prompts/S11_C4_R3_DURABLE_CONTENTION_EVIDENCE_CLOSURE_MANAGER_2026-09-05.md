# HERMES PROMPT — S11-C4-R3 Durable Contention and Evidence Closure

Đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
trước mọi preflight hoặc dispatch. Bạn là một Hermes Manager mới, gọn; Codex là
reviewer/gate độc lập. Manager không sửa production, test, migration, UI hoặc
config.

## 1. Authority and current verdict

Đọc đầy đủ rules, `AGENTS.md`, `SESSION_PROTOCOL.md`, current
`CODEX_PM_HANDOFF.md`, `ROADMAP.md`, R1/R2 verdicts, binding R2 prompt,
T03G/INT01 LOG+REPORT, both R2 evidence roots, read-only Hermes session state,
and current source/tests. Báo `RULES_LOADED` kèm full path, hash, line count,
actual Git/process/session inventory and every discrepancy before dispatch.

Current authority:

- `S11-C4-R2 = CHANGES_REQUESTED / NOT_APPROVED`.
- `S11 = NOT_CLOSED`; S12/S13 remain blocked.
- Canonical reviewed worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Reviewed canonical branch/HEAD:
  `codex/s11-integration` at
  `11dd50a467f5832ad372ceb1f50a61252e0462ee`, clean and local==remote at
  Codex review. Rediscover it; do not assume it stayed fixed.
- R2 worker commit:
  `938d75905740cb6afa7792eb881c302321b5b268`.
- This file is `PROPOSED_ONLY` while merely stored. If the user pastes/sends
  this prompt into a new Manager chat, that message is explicit authority to
  dispatch exactly this bounded R3; do not request a second confirmation.

## 2. Route and session policy

Use the latest user route for every new Manager turn and for the resumed R2
owner:

- provider `muse`, custom 9Router;
- base URL `http://127.0.0.1:20128/v1`;
- exact model `cmc/meta/muse-spark-1.3-contributor`;
- reasoning max, fallback OFF, TTFB timeout 900 seconds.

Run one zero-write route probe and record the actual model row. Do not use or
fall back to 1.2, DeepSeek, `ocgfree`, `auto` or another alias.

Session ownership is binding:

- exact implementation owner to resume:
  `20260905_192221_6da09b`;
- competing duplicate owner permanently frozen and never resumed:
  `20260905_192249_150b51`;
- old owners remain frozen:
  `20260903_170546_0d42f6`, `20260905_043139_01a91f`;
- Git-only INT01 remains `20260903_112116_35051c` and is resumed only after
  the implementation owner reaches terminal state.

Before resume, use Hermes `state.db` only through
`mode=ro&immutable=1` and prove there is no active writer/process for any owner.
Do not mutate, copy or vacuum the DB. Never create a third implementation
session. Any duplicate writer is immediately `BLOCKED_ROLE_VIOLATION`.

## 3. Dirty-attribution guard

R2 worktree/branch:

- `C:\Users\Admin\MotionForge2D-worktrees\s11-c4-r2`
- `codex/s11/c4-r2` at worker tip `938d759`

The worktree is expected to contain five untracked files created by the frozen
competing session under:

`docs/pm/sessions/S11-T03G/evidence/c4r2/`

They are incident evidence. Before any resume, enumerate each absolute path,
hash, bytes, logical lines and mtime; copy a byte snapshot only into the new
external Manager evidence root. Do not delete, modify, move, stage or commit
those files. Do not call `clean`, `stash`, `reset`, `restore` or reuse them as
new gate output.

Create one fresh immutable external root under
`C:\Users\Admin\MotionForge2D-evidence\s11-c4\` with an `R3-final` suffix.
All new manifests, snapshots and gate logs go there, never inside a Git
worktree.

Baseline-manifest both allowed and protected paths with absolute/relative
path, tracked/untracked/dirty owner attribution, SHA-256, bytes, logical lines
and mtime. Required protected set includes at least:

- `app/workflow/qc_checks_handler.py`
- `app/workflow/job_service.py`
- `app/persistence/qc_check_runs.py`
- `app/services/qc_checks/registry.py`
- `tests/test_s11_t03g_qc_check_job.py`
- `tests/test_s11_t03g_qc_check_api.py`
- the five dirty-attributed untracked R2 evidence files.

Create verified snapshots for the writable test authority and every dirty
untracked file. Run the project write-set guard before resume, after each patch
and at worker terminal; retain complete raw JSON externally.

## 4. Finite correction task

This is another correction round of the same Task ID:

`S11-T03G-C4-R2-RECOVERY`

Resume exact owner `20260905_192221_6da09b`; do not create a new worker.

Exclusive write-set:

- `tests/test_s11_t03g_qc_check_c4r1.py`
- append-only `docs/pm/sessions/S11-T03G/LOG.md`
- append-only `docs/pm/sessions/S11-T03G/REPORT.md`

Production code is frozen. In particular, no changes to handler, registry,
job service, persistence, detectors, migrations, schemas, frontend, T05/T06,
S10, MAIN product bytes, S12 or S13.

Required test correction:

1. Replace/strengthen the current two-thread payload so rendezvous occurs
   inside the real production bootstrap critical section, not before one
   caller waits for the other caller to finish.
2. Caller A must enter the explicit-registration operation while holding
   `_BOOTSTRAP_LOCK`, signal `entered`, and pause on a bounded release event.
3. Start caller B while A is paused. Prove B started but has not returned and
   is blocked by the production transaction lock before releasing A.
4. Release A; A must fail through an injected ordinary `RuntimeError` and
   return stable `RunQcChecksError / QC_RUN_BOOTSTRAP_CONFLICT` with preserved
   cause. B must then succeed with ten exact revisions.
5. Capture and assert both raw outcomes, event wait booleans, bounded joins and
   exact immediate final four-field registry snapshot/order.
6. Absolutely no post-thread call to `ensure_full_band_registered()` or other
   repair/cleanup may occur before the final-state snapshot/assertions.
7. Add one durable clean-subprocess test that exercises both
   `KeyboardInterrupt` and `SystemExit`: each performs a side effect inside
   explicit registration, restores the exact pre-call four-field snapshot,
   propagates the original unwrapped type/message, and cleanly reconverges only
   after the failure assertions are complete.
8. Preserve every existing R1/R2 import, explicit-registration, ghost,
   identity-conflict, clean-process and idempotence assertion.

Expected focused arithmetic after adding one BaseException test function:
the C4R1 module has 6 pytest nodes and all three T03G modules have 152 nodes.
If collection arithmetic differs, stop and explain before claiming green.

## 5. Patch-only safety

Existing files may be edited only with bounded `apply_patch`/patch tool calls
with verified preimages. Prohibit `write_file`, heredoc/direct Python writers,
`Path.write_text`, redirection, full-file replacement, copy-overwrite,
`ruff --fix`, stash, reset, restore, rebase, clean and force-push. The worker
must not create any new evidence or helper file in the worktree. Manager owns
external evidence only.

After every patch, verify hashes/bytes/lines and guard output. Any direct-write,
scope or competing-session recurrence is terminal
`BLOCKED_CONTEXT_HEALTH / BLOCKED_ROLE_VIOLATION`; do not retry with another
owner.

## 6. Verification order

After exact owner terminal and immutable correction commit:

1. Run the corrected true-contention node alone and independently inspect that
   its rendezvous is inside the production operation and final state is read
   before repair.
2. Run the durable BaseException node alone and verify both
   KeyboardInterrupt and SystemExit subrows.
3. Run the four R2/R3 micro functions: import RuntimeError, explicit
   RuntimeError, true contention and BaseException; all green.
4. Run the complete C4R1 module: expected 6 passed.
5. Run all three T03G modules: expected 152 passed, zero skip/xfail/error.
6. Run T05A 14, dedicated T12 #1 and #2 on distinct roots, then full T06 12.
7. Run Ruff `--select F` on test plus binding production paths, two-file mypy
   (`qc_checks_handler.py qc_check_runs.py --follow-imports=skip`), separately
   report whole `job_service.py` known result, and run `git diff --check`.
8. Resume exact Git-only INT01 only after all writers stop. Integrate only the
   verified correction commit. Because the worker branch and canonical docs
   may diverge, one conflict-free `--no-ff` merge is authorized; any conflict
   aborts without manual resolution and routes to the exact owner.
9. On the frozen integrated tree run fresh Alembic upgrade/sole-head, direct
   OpenAPI duplicate-ID scan, T01 serial 64, S10 retained 270, S10 API 71,
   process/port quiescence, clean canonical Git and local==remote after one
   non-force push.

Do not run shared/global gates in parallel. A broad green never waives a red
micro or test-structure row.

## 7. Truthful evidence packet

Every gate log must include before output:

- exact command and working directory;
- start timestamp and isolated DB/basetemp/cache/port roots;
- reviewed HEAD/tree hash;

and after output:

- end timestamp, duration and numeric exit code;
- complete stdout/stderr without tail-only truncation.

Create `REGISTRY.md`, full baseline/postimage manifests, snapshots, raw guard
JSON, `commands.jsonl`, quiescence/final-Git logs and
`NEXT_REVIEW_PACKET.md`. Index every pass and fail, including:

- R2's first matrix run `129 failed, 9 passed, 13 errors`;
- the R2 double-dispatch timeline;
- DB message 176346 at 20:04:12 +07 creating five untracked files after the
  claimed 19:55 freeze;
- both R2 evidence roots and their missing fields;
- intended-owner patch provenance;
- R3 exact node arithmetic and Git ancestry.

Do not rewrite history or claim the competing session made no writes. State
precisely that no tracked production/test byte collision was found, while its
five untracked worktree writes remain preserved incident evidence.

## 8. Terminal condition

Only when every R3 row and artifact is green, report:

`SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Manager never writes `APPROVED` or `CLOSED`, never opens S12/S13 and never
self-dispatches Codex review. Heartbeat every 20 minutes, audit after 8 minutes
without progress, and for temporary connection failure wait 5 minutes then
resume the same exact owner/model.

Start immediately after user dispatch with `RULES_LOADED`, fresh inventory,
dirty-attribution manifest, exact route probe and zero-writer proof. Then resume
only `20260905_192221_6da09b`.
