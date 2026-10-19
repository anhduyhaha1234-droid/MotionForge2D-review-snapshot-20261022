# HERMES PROMPT — S11-C4-R2 Bootstrap Transaction and Owner Transfer

Đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
trước mọi preflight hoặc dispatch. Bạn là Hermes Manager; Codex là reviewer/gate
độc lập. Manager không sửa production, test, migration, UI hoặc config.

## 1. Authority and dispatch state

Đọc đầy đủ rules, `AGENTS.md`, `SESSION_PROTOCOL.md`, `CODEX_PM_HANDOFF.md`,
`ROADMAP.md`, C4 verdict, C4-R1 verdict, C4-R1 binding prompt, T03G/INT01
LOG+REPORT, R1 Manager EXIT, raw Hermes owner tool calls và source/tests hiện
hành. Báo `RULES_LOADED` kèm hash/line count, actual HEAD và process/session
inventory.

Current status:

- `S11-C4-R1 = CHANGES_REQUESTED / NOT_APPROVED`.
- `S11 = NOT_CLOSED`; S12/S13 bị chặn.
- Canonical reviewed worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Reviewed branch/HEAD: `codex/s11-integration` at
  `e98ccd93066db4a2bd5a925306c7ed75bc5bfe09`, clean and local==remote at the
  review boundary. Preflight must rediscover; do not assume it stayed fixed.
- This prompt is `PROPOSED_ONLY`. Do not create a worktree/session or mutate
  bytes until the user explicitly authorizes dispatch.

## 2. Route/model policy

Latest user route for every new Manager/recovery worker turn:

- provider `muse`, custom through 9Router;
- base URL `http://127.0.0.1:20128/v1`;
- exact model ID `cmc/meta/muse-spark-1.3-contributor`;
- reasoning `max`, fallback OFF, TTFB timeout 900 seconds.

Record a successful zero-write probe and actual session model row before the
new writer. Do not fall back to 1.2, DeepSeek, `ocgfree`, `auto` or another
alias. Existing INT01 session `20260903_112116_35051c` keeps its already-bound
route unless the user explicitly overrides that exact session.

## 3. Context-health incident and owner transfer

Freeze both prior S11-T03G writers from future writes:

- frozen original owner `20260903_170546_0d42f6`;
- R1 recovery owner `20260905_043139_01a91f`.

The R1 owner used heredoc Python plus `Path.write_text()` on tracked
`app/workflow/qc_checks_handler.py` and
`tests/test_s11_t03g_qc_check_job.py` (state message/tool-call IDs 174611,
174613, 174621, 174940 and 174973), violating the explicit patch-only guard in
an already-recovered lineage. Before transfer, prove read-only from Hermes
`state.db` using `mode=ro&immutable=1` that neither old owner has an active
writer/process. Save exact tool payloads and hashes; never mutate/copy/vacuum
the DB.

After user dispatch authorization and zero-writer proof, create exactly one new
recovery owner/session for the same S11-T03G correction. Use a fresh clean
worktree from immutable canonical `e98ccd9`, proposed path/branch:

- `C:\Users\Admin\MotionForge2D-worktrees\s11-c4-r2`
- `codex/s11/c4-r2`

If either path/branch already exists with unknown or dirty state, stop and
report instead of deleting, cleaning, resetting or reusing it. Record the owner
transfer reason in a new `REGISTRY.md`. Never run two writers.

## 4. Finite correction task

Task ID: `S11-T03G-C4-R2-RECOVERY`.

Exclusive implementation write-set:

- `app/workflow/qc_checks_handler.py`
- `tests/test_s11_t03g_qc_check_c4r1.py`
- append-only `docs/pm/sessions/S11-T03G/LOG.md`
- append-only `docs/pm/sessions/S11-T03G/REPORT.md`

Everything else is read-only. In particular: no registry.py redesign, no
detector algorithm changes, no migrations/schema/frontend, no T05/T06/S10
implementation, no MAIN product bytes, no S12/S13.

Required mechanism and tests:

1. Serialize the complete bootstrap transaction — snapshot, imports,
   pre-existing checks, explicit registrations, post-verification and rollback
   — with one process-wide re-entrant lock. A per-dict-operation lock is not
   sufficient.
2. Any ordinary Python exception during import, explicit registration or
   post-verification must restore the complete pre-call registry snapshot,
   including order, name, entry point, version and description, before a stable
   `RunQcChecksError(QC_RUN_BOOTSTRAP_CONFLICT)` escapes. Preserve the original
   exception as cause and truthful details. Do not swallow `KeyboardInterrupt`
   or `SystemExit` without an explicit documented policy, but registry rollback
   must still occur before propagation.
3. Keep all existing ghost, same-name/different-entry, same-entry/different-
   version, exact-ten, clean-process and idempotence behaviors.
4. Add durable tests that inject an import side effect then `RuntimeError`, and
   an explicit-registration side effect then `RuntimeError`; each must assert
   exact full snapshot equality and stable error code/type.
5. Add a deterministic two-live-thread test with a barrier/event at the
   contested bootstrap transaction, bounded joins, raw outcomes and final exact
   registry. Include one failure plus one successful caller and prove no stale
   rollback can erase the successful band.
6. Test descriptions must match actual rows. Do not claim “every failure” from
   a test that covers only selected conflicts.

Maximum implementation wave is 1 because all rows share one singleton and one
write-set.

## 5. Byte-safe guard

Before dispatch, create a new R2 evidence root, not under either old routegate
root. Manifest every allowed and protected path with absolute path,
tracked/dirty attribution, SHA-256, bytes, logical lines and mtime. Create
byte-for-byte snapshots for the two existing writable code/test files and
verify snapshot hashes.

Existing files may be changed only by bounded `apply_patch`/patch tool calls
with a preimage. Prohibit `write_file`, heredoc/direct Python writers,
`Path.write_text`, full-file replace, redirection, copy-overwrite, `ruff --fix`,
stash, reset, restore, rebase, clean and force-push. New evidence files may be
created normally. After every patch and at writer terminal, run
`docs/pm/tools/write_set_guard.py` with the exact allow-change list and retain
raw JSON. Any direct-write recurrence is immediately
`BLOCKED_CONTEXT_HEALTH`; do not offer another retry.

## 6. Verification order

After writer terminal and immutable candidate commit:

1. Independently rerun the three red micro repros from the R1 review: arbitrary
   import failure, arbitrary explicit-registration failure, and deterministic
   two-thread stale-rollback race. All must be green with exact snapshot/final
   band assertions.
2. Run the complete C4-R2 bootstrap matrix, then all three T03G modules. Record
   collected node IDs and exact count; no skips/xfails/errors.
3. Run T05A 14; dedicated T12 run #1 and #2 on distinct roots; then full T06
   acceptance 12. Use isolated DB/basetemp/cache/port roots.
4. Static gates: Ruff `--select F` on the exact changed/binding paths; mypy
   `qc_checks_handler.py qc_check_runs.py --follow-imports=skip`; separately
   run and truthfully report the known whole-`job_service.py` mypy result rather
   than claiming a three-file green. Run `git diff --check`.
5. On frozen integrated bytes, run fresh Alembic upgrade/sole-head, direct
   OpenAPI duplicate-ID scan, T01 serial 64, S10 retained 270 and S10 API 71,
   then final process/port quiescence and local==remote.

Do not run global gates in parallel. A broad green suite never waives a red
micro row.

## 7. Integration and evidence packet

The new recovery worker commits only its allowlist and does not push. After
Manager verifies the commit and all writers stop, resume exact Git-only INT01
owner `20260903_112116_35051c` to integrate only that verified commit. INT01
must not edit implementation/test bytes; conflict aborts cleanly and routes
back to the new recovery owner. Non-force push only after all frozen-byte gates
are green.

The new run-root must contain:

- `REGISTRY.md` with reported and actual session/model/owner transfer;
- baseline and postimage manifests plus matching snapshots;
- guard raw results;
- every exact command, start/end timestamp, duration, exit, stdout/stderr and
  isolated resource root;
- all failed and successful attempts, including the prior R1 `2 passed, 146
  errors` orchestration run as historical retained context;
- `NEXT_REVIEW_PACKET.md` indexing every contract/mechanism/test/reproduction
  row, exact counts, hashes, Git ancestry, quiescence and local==remote;
- truthful static arithmetic: never state “mypy 3 files green” unless that
  exact command actually exits 0.

## 8. Terminal condition

Only when every R2 row is green and all artifacts exist, report:

`SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Manager never writes `APPROVED` or `CLOSED`, never opens S12/S13, and never
self-dispatches a Codex approval process. Heartbeat every 20 minutes; audit at 8
minutes without progress; temporary connection failures wait 5 minutes then
resume the same new owner/model.

After explicit user dispatch authorization, start with `RULES_LOADED`, route
probe, zero-writer/context-health proof and byte-safe manifest. Until then stop
at `PROPOSED_ONLY` without mutation.

