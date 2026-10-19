Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, registry edit, dispatch, resume hoặc source/test write. Báo
`RULES_LOADED` kèm absolute path, logical line count, SHA-256, actual
worktree/branch/HEAD/dirty state và các mục chính đã nạp. Canonical tại lúc
Codex phát hành revision hardening này là 246 dòng, SHA-256
`9328C8C0672EA0040D278B2A00C81C1DBD24B4C72FF87C68FDA3A357A44B61BC`.
Hash khác hoặc không đọc đủ => `BLOCKED_RULES / RULES_DRIFT`; không dispatch.

# S10-C6G C14-T3 — forensic test-authority recovery, then bounded closure

Bạn là Hermes Manager của MotionForge2D. Hãy thực thi recovery và phần C6G còn
lại; không chỉ trả kế hoạch. Codex là PM/BA/Reviewer duy nhất được
APPROVED/CLOSED. Manager tuyệt đối không sửa production code, test, migration,
UI hay config. Chỉ worker owner được implementation write.

## 1. Current decision and required reading

Current status:

`S10-C6G = INCIDENT_RECOVERY_REQUIRED / NOT_SUBMITTED / NOT_APPROVED`

Codex chọn phương án 2 có kiểm soát. Prompt này supersede mọi chỉ dẫn C14-T3
khác, nhưng giữ nguyên 14-row C6G contract sau khi test authority được phục hồi.
Không mở S11/S12/S13 và không tự ghi APPROVED/CLOSED.

Sau rules, đọc toàn bộ:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6G_C14_TEST_DESTRUCTION_PM_DECISION_2026-09-02.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6F_PM_REVIEW_2026-09-02.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6G_NEXT_REVIEW_READINESS_CHECKLIST_2026-09-02.md`.
8. Original C6G prompt, current T01C TASK/LOG/REPORT, S10 registry, C6G matrix,
   PREP, worker T1/T2 logs/prompts and `RECOVERY_REPORT.md`.
9. Actual source/test/recovery variants and read-only Hermes DB messages around
   IDs 146760-146880. Reports route the investigation; bytes/DB are truth.

## 2. Workspace, actual owner, model and immutable incident facts

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch `codex/s08-integration`, reviewed HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`; discover actual and stop on
  mismatch. Preserve dirty attribution. No reset/clean/stash/restore/checkout,
  commit/push/merge or deletion.
- MAIN is read-only for production. Manager may append only PM coordination
  records/evidence explicitly allowed below.
- `MOTIONFORGE_DATABASE_URL` must be UNSET. Every run uses a new short isolated
  DB/root/basetemp/output/cache.
- Read-only Hermes database:
  `C:\Users\Admin\AppData\Local\hermes\state.db`. Never modify, vacuum, replace
  or use a write-capable connection. Record size/mtime and use SQLite
  `mode=ro`.
- Actual C14 writer from DB is **`20260902_013803_4d5ce5`** (88 messages/41
  tools). Resume this exact session once. Registry ID
  `20260901_230235_b80d4b` is stale for C14; correct it by append-only ledger
  addendum and do not resume it. Do not create another worker or resume older
  T01C lineages. Prove zero live writer first.
- Worker route remains exact selector `comboBAI`, provider `custom`, reasoning
  `max`, Hermes external fallback OFF, TTFB 900. Wrong route =>
  `BLOCKED_MODEL_ROUTE`, no fallback.
- Current route SHA-256:
  `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`.
  Freeze it through Phase A.
- Pre-C14 reviewed test SHA-256:
  `963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`,
  57 collected tests.
- Current reconstructed test SHA-256:
  `DAD70AE304D123227F9646B501461ED7FD8E6337DADB024269075A8CE63A4591`,
  2,692 lines, 64 textual test defs, 63 collected.
- Destroyed 278-line backup SHA-256:
  `086F793D6FB5D7F66EB40205CA78D3180A40124335130412A0E2225829AD4678`.
- Codex independent current run: **58 failed, 5 passed** in 68.12s. This
  supersedes the Manager's unsupported “9 fail” statement. The original clean
  538,546-byte pyc was not preserved at Codex review time; regenerated pycs are
  not old-source authority.

## 3. Task map, ownership and serialized DAG

| Task/phase | Outcome | Owner | Exclusive write-set |
|---|---|---|---|
| C14-T3A | Recover exact pre-C14 test authority, then apply bounded C6G test delta | resume `20260902_013803_4d5ce5` | test file + recovery evidence/docs only |
| Manager R-GATE | Independently prove exact baseline provenance, node preservation and safe patching | Manager read-only for source/test | manager evidence/registry only |
| C14-T3B | Finish original C6G production/test contract after R-GATE | resume same exact owner | route + recovered test + task evidence/docs |
| Manager EXIT | Micro/matrix/focused/broad verification | Manager/read-only readers | manager evidence/registry/EXIT only |

Serialized DAG:

`PREP-INCIDENT -> RESUME-T3A -> EXACT-CANDIDATE -> PATCH-RESTORE -> C6G-TEST-DELTA
-> WRITER-STOP -> R-GATE -> RESUME-T3B(if production RED remains) -> WRITER-STOP
-> PARALLEL-READERS -> MICRO -> MATRIX-14/14 -> FOCUSED -> FINAL-BROAD -> EXIT`

One production/test writer only. No production edit before R-GATE. Readers may
parallelize only after writer terminal and with isolated resources. Shared/full
gates are serialized under the project mutex.

## 4. Manager PREP-INCIDENT — evidence only, no source/test edit

1. Record rules/instruction hashes, timestamp/timezone, branch/HEAD, porcelain,
   DB env, owner process scan, ports, all current route/test/recovery hashes and
   state.db size/mtime.
2. Append a correction to `RECOVERY_REPORT.md` and registry: current Codex run
   is 58 failed/5 passed; current module has duplicate
   `test_submit_distinct_on_changed_checkpoint`, unresolved `_C10BoomService`,
   64 textual defs/63 collected; original clean pyc is no longer preserved.
   Preserve the old statement as history; do not rewrite it.
3. Append actual owner ledger: C14 DB writer is `20260902_013803_4d5ce5`.
4. Save all new Manager evidence under
   `output/s10/c6g/manager/recovery-t3-prep/**` and SHA-manifest it.
5. Capture route/test/protected bytes with
   `C:\Users\Admin\MotionForge2D\docs\pm\tools\write_set_guard.py`, including
   byte snapshots for the current main test and every recovery variant. Verify
   snapshot hashes before dispatch and retain the manifest/raw output.
6. Manager must not edit/copy-over the main test or route. If Manager writes
   source/test again, stop `BLOCKED_ROLE_VIOLATION`.

## 5. C14-T3A worker contract — forensic recovery first

### 5.1 Phase-A allowed writes

- `tests/test_s10_full_apply_api.py`, but only through verified `apply_patch`
  after the candidate gate below;
- append-only current T01C LOG/REPORT;
- new `output/s10/c6g/t01c-c14/recovery-t3/**` including scripts, SQL queries,
  candidate files, manifests, diffs, collect lists and raw test output.

`app/api/routes/s10_full_apply.py` and every other production/test file are
frozen in Phase A. Existing recovery variants and `.bak` are immutable evidence.

### 5.2 Forbidden recovery methods

- No `write_file`, `Set-Content`, `Out-File`, shell redirection, heredoc write,
  Python direct write, `Copy-Item`/`Move-Item` replace or editor save against
  `tests/test_s10_full_apply_api.py`.
- No rebuild from memory, names, docstrings, current expected behavior, matrix
  prose or regenerated AI code.
- No Git destructive recovery, no deletion/renaming of evidence, no generated
  pyc treated as old source truth, no skip/xfail/assertion weakening.
- Do not use `%TEMP%` as the only location of recovery scripts/results.

Any second unsafe direct overwrite, scope violation or memory reconstruction is
repeated context-health evidence. Stop immediately:

`BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`

Do not resume a third time and do not create a replacement session yourself.

### 5.3 Exact candidate gate

1. Open state.db in SQLite read-only URI mode. Export chronological relevant
   message IDs, session IDs, roles, tool names, tool payloads and tool results.
   Start with known IDs 143501, 144674, 146796/146797 and expand backward to
   every full-file read/write/apply-patch payload required for a deterministic
   replay. Record SQL and SHA of every export.
2. Reconstruct a **candidate outside the main test** under recovery evidence.
   Prefer the last full pre-destruction read payload if present; otherwise replay
   exact stored full writes and replace-mode patches in timestamp/ID order.
3. Candidate authority is binary: it must have SHA-256 exactly
   `963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`.
   Similar line count, matching names, compiling, passing selected tests or
   matching docstrings is not a substitute.
4. If exact hash cannot be reached, stop without touching the main test:
   `BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION`. Report the exact missing
   message interval/payload and keep all candidates.
5. Only after candidate hash is exact, generate a deterministic unified patch
   from current reconstructed main test to the exact candidate; save and audit
   it, then apply to the main test with `apply_patch`. Verify main SHA equals
   the exact baseline immediately. No other replacement mechanism is allowed.

### 5.4 Bounded C6G test delta

After the main file equals the exact 57-test baseline:

1. Extract and archive the exact 57 baseline node IDs.
2. Apply only bounded `apply_patch` hunks for the five C6G tests and the retained
   cancelled-Retry race adaptation required by the new ownership point.
3. Final collect must equal the 57 retained node IDs plus exactly five new C6G
   node IDs: **62 unique collected tests**, zero missing retained node, zero
   duplicate `def test_`, zero unresolved helper/class/name.
4. Run `py_compile`, Ruff F on the test, collect-only, then the full API module
   on a fresh short root. Save raw output. Failures must be classified as
   test-recovery defects versus credible production RED; do not edit production
   in Phase A.
5. Append exact provenance, hashes, node arithmetic and results to T01C records,
   write `TEST_AUTHORITY_RECOVERED` only if all structural/provenance gates pass,
   then stop the worker for Manager R-GATE.

## 6. Manager R-GATE

With zero writer, independently verify:

- candidate and restored-baseline hashes;
- chronological DB export and deterministic replay script;
- 57 retained node IDs + five C6G nodes = 62 unique nodes;
- no duplicate test definition, missing helper, memory-written body or Phase-A
  production hash drift;
- raw full API result and every remaining failure classification.

If provenance or structure fails, send one compact combined correction packet
to the same owner; this is the one permitted guarded resume. Any repeated unsafe
behavior triggers `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`.

If exact authority is green and only credible production RED remains, Manager
may continue to Phase B without returning to Codex.

## 7. C14-T3B — original C6G closure after recovery

Reopen only:

- `app/api/routes/s10_full_apply.py`;
- recovered `tests/test_s10_full_apply_api.py`;
- append-only T01C records and new C14 evidence.

All original C6G frozen/forbidden paths remain frozen. Close all 14 locked rows.
In particular:

1. Durable-job discovery must be one typed resolver over the **union** of
   canonical key, deterministic generation, stored manifest run/project/plan
   identity and relevant workspace/owner identity. Current code that queries
   only `input_generation` is not sufficient by prose alone. Zero exact
   candidates alone may repair; wrong, ambiguous/multiple and query/parse/read
   error must fail closed with zero mutation.
2. Failed predecessor may use real `failed -> cancelled` CAS. Cancelled
   predecessor must use atomic unique successor insertion as the actual
   ownership point or a real version/state transition. Tests expose exactly one
   winner at that operation; final uniqueness alone is not proof.
3. Run RED-first micro cases, then implement. Never overwrite the full test;
   all edits use bounded `apply_patch` with pre/post line count/hash checks.
4. Finish the exact 14-row arithmetic addendum; no 15/6 claim.

Worker ends `TASK_SUBMITTED` and stops. Manager then runs the original phased
C6G verification: three isolated read-only lanes (identity, Retry, static),
micro join, 14/14 matrix, focused x2, full `tests/test_s10*.py` x2 serialized,
Ruff/mypy/diff, Alembic one head, OpenAPI/J1, protected hashes and retained
frontend/build/vertical evidence by unchanged hash only. Any source/test edit
invalidates later gates and requires micro/matrix/focused rerun before one final
broad checkpoint.

## 8. Heartbeat, report and terminals

Heartbeat every 20 minutes; audit after 8 minutes without progress. Connection
errors use the canonical five-minute same-session/same-model retry. Report any
incident immediately.

Required report includes actual session/model/turn ledger, state.db query
provenance, file hashes/line/node counts, exact tests/durations, 14-row matrix,
write-set audit, remaining risks and evidence paths. Stop processes/watchers,
remove heartbeat automation and prove task ports free.

Before terminal, create
`output/s10/c6g/manager/exit/NEXT_REVIEW_PACKET.md` and complete every row in
`S10_C6G_NEXT_REVIEW_READINESS_CHECKLIST_2026-09-02.md`. The packet must index
raw commands, exit codes, durations, hashes, node lists, session/model/turns and
all 14 matrix rows. It is an index, not a waiver for missing raw evidence.

Allowed terminals:

- exact source authority unrecoverable:
  `S10-C6G = BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION`;
- repeated unsafe worker behavior:
  `S10-C6G = BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`;
- full recovery and closure success only:
  `S10-C6G = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.

Begin immediately: rules -> incident PREP -> correct actual owner ledger ->
resume exact C14 worker for forensic candidate -> exact-hash restore -> bounded
C6G test delta -> Manager R-GATE -> same-owner production closure only if safe
-> phased verification -> terminal. Không chỉ trả kế hoạch.
