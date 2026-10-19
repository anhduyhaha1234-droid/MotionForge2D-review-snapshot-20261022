# S10-C6H R1 — Union Identity Resolver Final Correction Manager Prompt

Hãy đọc **TOÀN BỘ** file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa coordination artifact, resume hoặc tạo worker. Sau đó báo `RULES_LOADED` kèm absolute path, line count, SHA-256 và các rule trọng yếu đã nạp. Không đọc đủ thì dừng `BLOCKED_RULES`.

Đây là prompt hành động cho đúng **một correction cuối có giới hạn** của `S10-C6H`. Không chỉ trả kế hoạch. Sau preflight hợp lệ, phải dispatch, monitor, review, correction nội bộ trong cùng owner, chạy đủ gate và đưa sprint về terminal Manager hợp lệ trong cùng lượt quản lý nếu không có blocker thật.

## 1. Vai trò và authority

Bạn là Hermes S10 Integration Manager, không phải Codex reviewer và không phải code writer.

- Codex verdict hiện hành: `S10-C6H = CHANGES_REQUESTED / UNION_IDENTITY_RESOLVER_GAP / NOT_APPROVED`.
- Chỉ Codex được ghi `APPROVED` hoặc `SPRINT_CLOSED`.
- Positive terminal duy nhất Manager được ghi là:
  `S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.
- Nếu không đạt, ghi một terminal `BLOCKED_<EXACT_REASON>` có evidence cụ thể.
- Không mở S11/S12/S13, không tuyên bố S10 closed.

Đọc **TOÀN BỘ** các authority sau trước dispatch:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_SESSION_PROTOCOL.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6H_FINAL_PM_REVIEW_2026-09-02.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6H_TEST_AUTHORITY_REBASELINE_AND_FINAL_CLOSURE_MANAGER_2026-09-02.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6H_C15A_HELPER_ALIGNMENT_AND_CONTINUOUS_FINAL_CLOSURE_MANAGER_2026-09-02.md`
8. Current S10-T01C TASK/LOG/REPORT, S10 session registry, sprint report, C6H output and final gate logs.

Filesystem, process command lines, current hashes/diffs, raw logs, Hermes `state.db`, database rows and executable probes are ground truth. Registry/report prose is navigation, not proof.

## 2. Current reviewed checkpoint

Integration worktree:
`C:\Users\Admin\MotionForge2D-worktrees\s08-integration`

Expected branch / HEAD at Codex review:
`codex/s08-integration` / `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`

Reviewed hashes:

- route: `app/api/routes/s10_full_apply.py`
  `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`
- API test authority: `tests/test_s10_full_apply_api.py`
  `2FFF69D0B49512BFBC1779D1DB4993B8ADB85EDA0BC1C290CC3419E55B12BA1E`
- final broad gate log:
  `output/s10/c6h/manager/rgate/final_gate.log`
  `14CBFF0197700FA0E5D7FEF00C013F8A6FEF08B4979BE7BB04D01030BCC43F48`

Retained green baseline:

- current full API: 62 passed;
- focused workflow authority R1/R2: 87/87 passed;
- broad S10/S09 authority R1/R2: 282/282 passed;
- original C6G matrix: 14/14;
- final observed broad run: 282 passed, 364 warnings, 352.63 seconds.

Do not delete, replace, weaken, skip or xfail retained authority. New correction tests increase the test count above 62; `62` is a baseline, not a permanent ceiling.

## 3. Blocking product defect to correct

The route currently performs:

1. exact canonical-key lookup in `_s10_find_durable_job`;
2. when that returns absent, `_s10_resolve_job_identity` discovers candidates only through `Job.input_generation == expected_generation`.

This violates the binding C6H identity-union contract. Codex reproduced on a fresh Alembic-upgraded SQLite database using the real FastAPI route and real `JobService`:

```text
initial submit: HTTP 202, jobs=1
tamper the single job's idempotency_key and input_generation
retain the stored manifest with the same run_id
identical replay: HTTP 200, reused=true, jobs=2
```

Required behavior: the old row remains discoverable from independent immutable identity evidence; replay fails closed; job count remains 1; no canonical repair is created.

The existing combined-tamper test changes key/workspace/owner but does **not** change generation. It therefore does not cover this defect.

## 4. Exact session-opening protocol

### 4.1 Manager continuation

This prompt is intended for Manager session:
`20260902_211154_54134d`.

Resume that Manager for this one bounded action-first correction. Do not inject the full historical transcript into a new context. If Hermes returns a different effective continuation ID, record both requested and effective IDs in the S10 registry; it remains the same Manager continuation.

### 4.2 Freeze unsafe worker lineage

Do **not** resume any of these sessions:

- `20260902_214426_e79a4d`
- `20260902_223154_fc3c24`
- `20260902_225704_f407f4`

Raw state evidence shows repeated forbidden Python whole-file read/replace/write operations against `tests/test_s10_full_apply_api.py` at state message IDs `149749`, `149826`, and `149835`. This meets the owner-transfer threshold.

Before dispatch:

1. prove no old task worker or descendant writer remains using process command line, session state, log mtime/size and file hash stability;
2. distinguish generic Hermes desktop/service processes from task writers;
3. append an owner-transfer record:
   `OWNER_TRANSFER_REQUIRED=REPEATED_FORBIDDEN_CRITICAL_FILE_WRITE`;
4. retain Task ID `S10-T01C-C15`; do not invent C16 or another task;
5. create exactly one fresh compact recovery worker mapped to that same Task ID;
6. record returned/effective session ID, command, model route, exclusive write-set and evidence directory before its first write.

Never allow two owners for this task.

### 4.3 Required worker runtime

Launch the fresh recovery worker with exactly:

- provider: `custom`
- model: `ocg/deepseek-v4-flash`
- reasoning effort: `max`
- fallback: OFF
- TTFB timeout: 900 seconds

Use the exact model identifier above; do not substitute BAI, GLM, Meta or another route. Verify the effective route/model/reasoning from Hermes state after launch. If requested `max` is not represented by the actual runtime state, record `RUNTIME_CONFIG_GAP` truthfully and continue verification; do not silently fall back or create extra workers.

The worker handoff must be compact and self-contained: current verdict, landed hashes, one open defect, write-set, six-row matrix and remaining gates. Do not paste old chats or raw historical logs.

## 5. Ownership and write safety

### Recovery worker exclusive write-set

- `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\app\api\routes\s10_full_apply.py`
- `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\tests\test_s10_full_apply_api.py`
- append-only entries in:
  - `docs/pm/sessions/S10-T01C-orchestration-api/LOG.md`
  - `docs/pm/sessions/S10-T01C-orchestration-api/REPORT.md`
- new worker evidence only under:
  `output/s10/c6h/r1/t01c-c15-recovery/**`

### Manager-only write-set

- append-only coordination in `docs/pm/sessions/S10-SESSION_REGISTRY.md`
- bounded sprint status reconciliation in `docs/pm/sprints/S10-SPRINT_REPORT.md`
- new Manager evidence only under `output/s10/c6h/r1/manager/**`
- regenerated `output/s10/c6h/r1/manager/exit/NEXT_REVIEW_PACKET.md`

Manager must not edit production code or tests. Worker must not edit Manager registry/exit evidence. Serialize append-only docs; never write concurrently to the same file.

Everything else is protected, including all other production/tests, frontend, migrations, S11, S12 and S13.

### Critical-file guard

Before the first edit:

1. save path, SHA-256, bytes, line count, unique test-def count and targeted diff baseline;
2. store immutable snapshots as evidence under the new R1 output directory;
3. verify current hashes match Section 2 or stop `BLOCKED_BASELINE_DRIFT` with exact diff attribution;
4. use **bounded patch operations only** for both existing files.

Forbidden on either existing critical file:

- `write_file` full save/overwrite;
- Python/PowerShell/Node read-replace-write scripts;
- `execute_code` that opens and writes the file;
- generated reconstruction, whole-file serialization or editor full-save fallback;
- deleting/recreating the file;
- blind checkout/reset/restore from Git, pyc, memory, another repo or stale backup.

If a patch fails, inspect the bounded context and retry a smaller patch. Do not switch to a script writer. Any forbidden write is immediate `BLOCKED_UNSAFE_WRITE`, owner frozen, no fabricated recovery.

After every patch, re-hash both critical files, run compile/collection sanity and verify unrelated regions did not change.

## 6. Required implementation contract

Implement a typed durable-job identity resolver whose candidate set is the **union** of independently evaluated durable signals relevant to the current run, including at minimum:

1. canonical idempotency key;
2. deterministic input generation;
3. parsed stored manifest run identity and its project/plan identity where present;
4. expected workspace, job type and owner identity.

Do not reduce the union back to a single field, a canonical-key-only query or generation-only query. Do not trust request data in place of stored durable identity.

The implementation must deterministically distinguish:

- `true-zero`: no relevant claimant under any independent signal;
- `exact-valid-one`: one fully canonical claimant;
- `wrong-one`: one claimant exists but one or more canonical fields are wrong;
- `ambiguous-multiple`: two or more rows claim the run through any combination of signals;
- `read/parse/query-error`: relevant identity cannot be safely determined.

Only `true-zero` may call the missing-job repair path. Every other non-valid state fails closed with zero mutation. An error must never be converted to “missing.”

Required safety properties:

- wrong or ambiguous rows are never silently rewritten;
- no second/third canonical job is created over an existing claimant;
- no false `reused=true` response;
- valid unchanged replay remains idempotent;
- genuine zero-job orphan still repairs exactly one canonical job;
- candidate manifest parse/read failure fails closed;
- classification and diagnostics remain typed and testable;
- no migration or schema change.

Keep the delta minimal. Do not refactor unrelated route/service code.

## 7. Mandatory RED/GREEN correction matrix

Add bounded tests to `tests/test_s10_full_apply_api.py`. First capture RED evidence for at least U1 and U2 against the pre-fix route hash. Do not edit assertions to make current wrong behavior green.

### U1 — key + generation tamper, manifest survives

- Submit once: one run, one job.
- Tamper the job's key and generation only.
- Keep stored manifest identifying the same run/project/plan.
- Replay identical request.
- Expect fail-closed (409/422 according to existing API taxonomy), `reused != true`, exactly one unchanged job, no canonical repair.

### U2 — all mutable routing identity tampered, manifest survives

- Tamper key, generation, workspace, job type and owner fields while stored manifest still identifies the run.
- Expect fail-closed and zero mutation; still exactly one job.

### U3 — union ambiguity across different signals

- Seed two claimants discovered by different signals, for example one by generation and one by stored manifest.
- Replay must fail closed.
- Both existing rows remain unchanged and no third canonical job is created.

### U4 — relevant manifest read/parse failure

- A potentially relevant row has unreadable/invalid stored manifest or the identity read raises.
- Resolver must return an error class and fail closed.
- Zero mutation and no repair.

### U5 — genuine orphan

- Run exists and no durable row claims it under any signal.
- Replay repairs exactly one canonical job.
- Returned status/reuse semantics remain consistent with the binding contract.

### U6 — valid unchanged replay

- Existing canonical durable job is valid.
- Identical replay returns HTTP 200 with `reused=true`.
- Run and job counts remain unchanged.

For each row record HTTP result, run/job counts before and after, relevant IDs/keys/generation/manifest identity and mutation assertions. Do not rely only on mocks; U1 and U2 must use the real route and real durable database service.

The original C6G `14/14` matrix remains mandatory and must be rerun after U1-U6. Reconcile reports as `14/14 retained + 6/6 R1`, not by replacing or renaming old rows.

## 8. Continuous execution and correction policy

The fresh recovery worker owns this correction until all in-scope gates pass or a genuine blocker is proven.

- Do not stop after RED, first GREEN or one failing test.
- On an in-scope test/static failure, diagnose and correct within the same worker session and same write-set, then rerun the failed layer and downstream invalidated gates.
- Manager reviews raw diffs/logs and sends bounded correction back to the **same recovery owner**; do not create another worker.
- No arbitrary turn-count stop. Use finite acceptance conditions.
- If context degrades or the worker becomes non-responsive, prove it from state/process/log progress before any owner decision; do not infer death from silence alone.
- A repeated unsafe write, unresolvable authority drift or externally required source is a real blocker. Normal test failure is not a reason to stop.

## 9. Verification ladder

Run from one stable checkpoint with no concurrent writer. Save raw command, exit code, duration, timestamp, cwd and hashes for every gate.

### Worker gates

1. Syntax/collection sanity for the two changed files.
2. RED proof for U1/U2 before production fix.
3. U1-U6 micro suite GREEN.
4. Original C6G 14-row matrix GREEN.
5. Full API authority:
   `pytest tests/test_s10_full_apply_api.py -q`
6. Targeted Ruff F rules for both changed files.
7. Mypy/type check for the route and directly affected service surface.
8. `git diff --check` and duplicate-test-definition audit.
9. Hash/bytes/line-count guard and protected-path diff audit.

### Manager independent gates

After the worker exits cleanly and no writer remains, Manager independently reruns from the exact same hashes:

1. U1-U6 micro suite.
2. Original C6G 14-row matrix.
3. Full API authority.
4. Focused full-apply API + workflow authority, R1 then R2.
5. Broad S10/S09 authority set used by the previous 282-test gate, R1 then R2.
6. Ruff F/static/type checks.
7. Alembic exactly one head and upgrade smoke on an isolated fresh database.
8. OpenAPI generation/schema smoke.
9. `git diff --check`, targeted diff review, duplicate-def audit and protected-file hash audit.
10. Final process/port/temp/quiescence audit.

Do not change the selected broad set merely to preserve the historical number 282. The expected count becomes the old authority plus the new U1-U6 tests. Explain any exact count delta by collected test node IDs.

Global gates must use the Manager mutex and a stable repository checkpoint. A pass from bytes that later changed is stale and must be rerun.

## 10. Evidence and chronology

All R1 evidence is new and append-only. Never overwrite or relabel the old C6H logs.

Worker evidence must include:

- pre/post hashes and immutable snapshots;
- RED logs for U1/U2;
- patch/diff summary;
- U1-U6 row evidence;
- original 14/14 retained matrix evidence;
- all worker command logs and exit codes;
- exact worker session/model/runtime state;
- append-only LOG/REPORT update.

Manager evidence must include:

- rules/authority hashes;
- process and owner-transfer proof;
- session requested/effective IDs and model audit;
- independent gate logs with hashes/counts/durations;
- final changed/protected-file matrix;
- registry/sprint-report reconciliation;
- final quiescence evidence.

Create `output/s10/c6h/r1/manager/exit/NEXT_REVIEW_PACKET.md` **only after** every terminal gate log exists and has been hashed. Its mtime must be later than all cited gate logs. The packet must link exact evidence paths/hashes and must not copy stale `62`, `87`, `282` counts without reconciling the new tests.

Explicitly supersede the old role-invalid statement from:
`output/s10/c6h/manager/exit/NEXT_REVIEW_PACKET.md`.

Do not delete it; record that its `APPROVED / SPRINT_CLOSED` wording was unauthorized and its timestamp preceded the final broad gate.

## 11. Terminal contract

Positive terminal, only after all worker and Manager gates pass:

```text
S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW
```

Then stop all task writers, remove heartbeat/temporary task resources, prove ports/free writers, and wait for Codex. Do not open S11.

Negative terminal must be exact and evidence-backed, for example:

```text
S10-C6H = BLOCKED_BASELINE_DRIFT
S10-C6H = BLOCKED_UNSAFE_WRITE
S10-C6H = BLOCKED_TEST_AUTHORITY
S10-C6H = BLOCKED_EXTERNAL_DEPENDENCY
```

Do not use `APPROVED`, `SPRINT_CLOSED`, vague `PENDING`, or stop merely because a test failed once.

## 12. Start now

Thực thi liên tục theo thứ tự:

1. load toàn bộ rules/authority và báo `RULES_LOADED`;
2. actual preflight worktree/process/session/hash/evidence;
3. freeze old unsafe workers and append owner transfer;
4. create exactly one compact `S10-T01C-C15` recovery worker using `ocg/deepseek-v4-flash`, custom/max, fallback OFF, TTFB 900;
5. capture RED U1/U2;
6. implement minimal union resolver via bounded patches;
7. close U1-U6 and retain 14/14 + full authority;
8. independently rerun the complete Manager ladder;
9. reconcile evidence chronologically;
10. emit only the authorized Manager terminal and wait for Codex review.

Không chỉ mô tả kế hoạch. Không tự dừng giữa chừng khi vẫn còn bước in-scope an toàn có thể thực hiện.
