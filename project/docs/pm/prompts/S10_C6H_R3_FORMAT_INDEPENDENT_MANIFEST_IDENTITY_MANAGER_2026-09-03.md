# S10-C6H R3 — Format-Independent Manifest Identity Final Correction

## 0. Mandatory first action

**BẮT BUỘC:** trước mọi preflight, state change hoặc dispatch, đọc TOÀN BỘ:

`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`

Sau đó đọc TOÀN BỘ:

- `C:\Users\Admin\MotionForge2D\AGENTS.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6H_R2_PM_REVIEW_2026-09-03.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6H_R2_RELEVANT_MANIFEST_SCOPE_AND_WRITE_SAFETY_MANAGER_2026-09-03.md`
- current S10-T01C TASK/LOG/REPORT, S10 registry and `output/s10/c6h/r2/manager/exit/NEXT_REVIEW_PACKET.md`.

Ghi `RULES_LOADED` chính xác:

- MAIN canonical: 246 lines, SHA-256 `9328C8C0672EA0040D278B2A00C81C1DBD24B4C72FF87C68FDA3A357A44B61BC`;
- stale worktree copy: 37 lines, SHA-256 `29EA6B6035E981793F389B211469D537DA14FCD4F0AC1B2912B7EFEB31D11770`.

Nếu facts hiện tại khác, ghi actual facts và dừng `BLOCKED_RULES_DRIFT`; không gộp SHA của một file với line count của file kia.

Đây là execution prompt. Sau preflight hợp lệ phải thực thi correction, không chỉ trả kế hoạch.

## 1. Role and dispatch boundary

Bạn phải là một **Hermes Manager chat/session hoàn toàn MỚI** cho bounded `S10-C6H R3`.

Manager cũ `20260902_211154_54134d` đã bị Codex retire do context dài và hai lần không tuân thủ routing/review contract. Nếu current Manager session ID chính là ID đó hoặc là resume của chat đó:

`BLOCKED_CONTEXT_HEALTH / NEW_MANAGER_SESSION_REQUIRED`

Không dispatch worker trong chat cũ. Prompt này chỉ có authority trong Manager chat mới.

Manager mới chỉ preflight, resume đúng worker owner, monitor, review, chạy gate và ghi evidence/docs. Manager không sửa production code/test.

Authority:

`AUTHORIZED_TO_DISPATCH` duy nhất cho `S10-C6H R3`.

Không được mở S11, S12, S13; không commit/merge/push/reset/clean/stash; không ghi `APPROVED` hoặc `CLOSED`.

## 2. Current verdict and finite finding

Current Codex verdict:

`S10-C6H = CHANGES_REQUESTED / R3_AUTHORIZED / NOT_APPROVED / S10_NOT_CLOSED`

R2 đã đóng:

- unrelated malformed/valid manifests không chứa target run ID không còn block true-zero repair;
- stale `sig_manifest` loop state;
- R1 unsafe worker lineage bằng một safe recovery worker.

Finding còn mở duy nhất:

`P1 FORMAT_DEPENDENT_MANIFEST_DISCOVERY`

Current route chỉ nhận hai literal forms:

- `"run_id":"<id>"`
- `"run_id": "<id>"`

Valid JSON `"run_id"\t:\t"<id>"` hoặc newline quanh `:` bị bỏ qua. Khi key + generation cũng tampered, replay hiện trả `200 reused=true` và tạo job canonical thứ hai. R3 phải sửa invariant, không thêm tiếp danh sách whitespace examples.

## 3. Workspace and preimage authority

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch: `codex/s08-integration`
- HEAD: `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`
- Expected porcelain count: `66`; không clean shared dirty tree.
- Route preimage:
  - `app/api/routes/s10_full_apply.py`
  - SHA `BA97FB24AF371EEFCFC4EC7C7A89E4E5783D5C5B42EE565906405496A1A8069D`
  - 2,595 lines by the established R2 counting convention.
- Test preimage:
  - `tests/test_s10_full_apply_api.py`
  - SHA `EF5F93A3C7D434F8DF8D980D75AF8A9972A4EC982DBF77193C8F7CDEE77DB532`
  - 3,369 lines, 70 unique test defs.
- R2 packet SHA `6193EF17B0E3FD4E8C08780FD8712FEAD697DF7A3A1E417390DE1899DD5FF706`.

Preflight must confirm exact branch/HEAD/hashes, DB env unset, zero relevant writer/test process, free task ports and stable tree. Any mismatch: `BLOCKED_PREIMAGE_DRIFT`, no restore or dispatch.

Create Manager-owned byte snapshots and write-set manifest under `output/s10/c6h/r3/manager/guard/**`; verify snapshot hashes. State DB access is read-only only.

## 4. Session ownership

Task ID remains `S10-T01C-C15`; this is a correction, not a new task.

- Resume exact safe owner: `20260903_012248_d29911`.
- Do not resume frozen R1 or earlier C15/C14 owners.
- Do not create a second independent worker owner.
- Before resume, prove owner is terminal `agent_close` and no process/child remains.
- If `hermes --resume 20260903_012248_d29911` creates a new effective state row, record requested ID, effective ID and parent/resume evidence in registry. It remains the same logical owner lineage.
- Maximum concurrent writer: `1`.

## 5. Model contract

Preserve the owner's model:

- provider: custom;
- exact model: `ocg/deepseek-v4-flash`;
- requested reasoning: max;
- fallback disabled;
- TTFB timeout `900s`.

Wrong provider/model/fallback is `BLOCKED_MODEL_ROUTE`. If state still records `reasoning_config=null`, record `RUNTIME_CONFIG_GAP`, do not claim max was proven, and continue the bounded correction. Connection errors follow canonical five-minute same-owner retry policy.

## 6. Exclusive write-set

Worker may modify only:

1. `app/api/routes/s10_full_apply.py`
2. `tests/test_s10_full_apply_api.py`
3. new evidence under `output/s10/c6h/r3/worker/**`
4. bounded append-only S10-T01C LOG/REPORT entries explicitly required by this prompt.

Manager may write only R3 coordination/evidence/registry/packet artifacts. Everything else is protected, including migrations, models, services, workflow, frontend and all S11/S13 production paths.

## 7. Critical-file write safety

Existing route/test files are unified-patch-only:

- exact preimage;
- one small hunk per patch call;
- no `mode=replace`, `write_file`, whole-file rewrite, redirection, direct-write script, formatter sweep, copy/move/restore/delete/recreate;
- after every successful hunk: SHA/bytes/lines, `py_compile`, targeted collect/test;
- a rejected patch that modifies zero bytes may be retried with a corrected exact preimage;
- any patch that changes wrong bytes/path, breaks compile, shrinks unexpectedly or damages indentation is terminal `BLOCKED_UNSAFE_WRITE`; do not restore or continue.

New evidence files may be generated normally in the new R3 evidence directory. Do not overwrite historical evidence.

## 8. Product mechanism required

Inside `_s10_resolve_job_identity`, preserve the union of:

1. exact canonical idempotency key;
2. exact deterministic generation;
3. stored manifest text containing the exact target run ID, independent of JSON whitespace/pretty-print formatting.

The manifest prefilter must not enumerate compact/single-space/tab/newline variants. Use one bounded exact target-run literal containment with correct wildcard escaping, or an equivalent representation-independent mechanism.

After the prefilter:

- parse JSON;
- exact-match manifest `run_id`, `project_id` and `plan_id` for claimant classification;
- malformed candidate text containing target run ID fails closed;
- unrelated malformed text without target run ID is not selected;
- valid row containing target ID only in a non-identity field may be parsed then ignored if exact manifest identity does not match;
- key/gen claimant parse/read errors remain fail-closed;
- only true zero may repair;
- per-row signal fix from R2 must remain intact.

Do not parse every manifest globally and do not weaken wrong-one/ambiguous/exact-valid classifications.

## 9. Locked RED/GREEN representation matrix

Patch tests before production and capture RED on current R2 route.

### R3-A — Valid tab-formatted target claimant

Add one real-stack test named:

`test_r3_valid_json_whitespace_does_not_erase_manifest_claimant`

Required setup:

1. real FastAPI route, real `JobService`, fresh Alembic SQLite;
2. normal submit creates one run and one job;
3. parse the actual stored manifest, preserve all values, then serialize valid JSON whose target token is `"run_id"\t:\t"<exact-run-id>"`;
4. verify `json.loads()` accepts it and exact run/project/plan values remain;
5. tamper only key and generation;
6. replay identical payload.

Required expected result after fix:

- `409/422`, `reused != true`;
- exactly one job remains;
- same job ID, tampered key/gen and tab-formatted manifest remain unchanged;
- no canonical replacement job;
- run count unchanged.

Current R2 must RED as `200 reused=true`, jobs `1 -> 2`.

### R3-B — Malformed newline-formatted target candidate

Modify U4's malformed manifest so exact target run ID is separated from the key/colon using legal JSON whitespace such as CRLF/tab before truncation. Current R2 must RED by misclassifying true-zero/repair; after fix it must return parse-error fail-closed with zero mutation.

### R3-C — Retained boundaries

Retain and rerun:

- R2 unrelated malformed without target run ID: repairs target exactly once;
- R2 unrelated valid foreign manifest: does not block;
- U1-U6;
- 14/14 C6G closure matrix;
- ambiguous multiple, exact replay and combined tamper rows;
- F2 per-row classification mechanism.

Expected structural count after one new test: `71` unique defs, zero duplicates, all 70 prior defs retained. Record actual pytest node count separately; do not confuse parameterized nodes with defs.

## 10. Gate order

Worker:

1. preimage/guard;
2. patch R3-A and R3-B test changes;
3. RED both R3-A/R3-B on unchanged route;
4. patch the route mechanism once;
5. compile/collect;
6. GREEN R3-A/R3-B plus R2-A/R2-C/U4;
7. U1-U6 + all R2/R3 rows;
8. C6G 14/14 matrix;
9. full API module;
10. Ruff F, retained mypy command, diff-check, duplicate/lost-def/shrink audit;
11. submit evidence and exit.

After worker terminal, Manager independently:

1. audits exact diff and proves there is no whitespace-variant enumeration;
2. reruns R3-A/R3-B and R2 boundary rows on a fresh temp DB;
3. runs an additional read-only adversarial probe with a different legal whitespace combination not copied from the worker test;
4. reruns C6G matrix and full API;
5. focused gate twice and broad gate twice on frozen bytes/global mutex;
6. Ruff/mypy/diff/Alembic/OpenAPI;
7. raw worker session tool-call audit.

Do not run broad before micro/matrix are 100% green. Green broad cannot waive a failed representation row.

## 11. Raw-session audit

Manager must inspect the resumed worker's raw session state read-only and report:

- all patch calls and whether rejected calls changed bytes;
- any `write_file`, replace mode, direct write, redirection, copy/move/restore touching critical files;
- provider/model/config;
- requested/effective resume IDs;
- zero concurrent writer.

Any forbidden critical write is `BLOCKED_UNSAFE_WRITE`, even if tests pass.

## 12. Liveness and parallelism

- one active writer only;
- read-only isolated gates may parallelize only after writer exit;
- shared/global gates use mutex;
- heartbeat every 20 minutes;
- audit after 8 minutes without progress;
- connection retry waits five minutes and resumes the same owner/model;
- Manager continues until a valid terminal packet, not merely until worker response.

## 13. Required report and terminal

Append truthful R3 entries to S10 TASK records/registry and create:

`output/s10/c6h/r3/manager/exit/NEXT_REVIEW_PACKET.md`

Packet must include:

- exact Manager session ID proving it is new;
- requested/effective worker resume IDs;
- pre/post hashes/sizes/lines;
- exact RED and GREEN output;
- representation matrix;
- raw commands, exits, counts, durations and evidence paths;
- raw tool-call audit;
- corrected MAIN/worktree rules hash arithmetic;
- quiescence/ports/DB guard;
- no commit and no S11 dispatch.

Positive terminal vocabulary only:

`S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Negative terminals include `BLOCKED_CONTEXT_HEALTH`, `BLOCKED_PREIMAGE_DRIFT`, `BLOCKED_MODEL_ROUTE`, `BLOCKED_UNSAFE_WRITE`, `BLOCKED_TEST_AUTHORITY` and `CHANGES_REQUIRED / MANAGER_VERIFICATION_FAILED`.

Never write `APPROVED`, `CLOSED` or open S11. Codex owns the sprint gate.

## 14. Start now

In this new Manager chat:

1. load canonical authority;
2. prove old Manager and worker are quiescent;
3. capture R3 guards;
4. resume exact worker `20260903_012248_d29911`;
5. execute the finite RED/GREEN matrix;
6. independently verify and audit raw session writes;
7. emit one truthful R3 review packet and stop for Codex rereview.

