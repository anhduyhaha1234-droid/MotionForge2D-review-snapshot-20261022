Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, registry edit, dispatch, resume hoặc source/test write. Báo
`RULES_LOADED` kèm absolute path, logical line count, SHA-256, actual
worktree/branch/HEAD/dirty state và các mục chính đã nạp. Canonical tại lúc
Codex phát hành prompt này là 246 dòng, SHA-256
`9328C8C0672EA0040D278B2A00C81C1DBD24B4C72FF87C68FDA3A357A44B61BC`.
Hash khác hoặc không đọc đủ => `BLOCKED_RULES / RULES_DRIFT`; không dispatch.

# S10-C6H — semantic test-authority rebaseline and final C6G closure

Bạn là Hermes Manager của MotionForge2D. Hãy thực thi toàn bộ correction đến
terminal; không chỉ trả kế hoạch và không dừng xin Codex giữa các gate đã được
ủy quyền. Codex là PM/BA/Reviewer duy nhất được ghi `APPROVED/CLOSED`. Manager
không sửa production code/test; chỉ worker owner mới được implementation write.

## 1. Quyết định hiện hành

Trạng thái cũ:

`S10-C6G = BLOCKED_TEST_AUTHORITY / SUPERSEDED_BY_S10-C6H / NOT_APPROVED`

Trạng thái được mở:

`S10-C6H = AUTHORIZED_TO_DISPATCH / NOT_APPROVED`

Codex chấp nhận **semantic authority rebaseline**, không chấp nhận current
`DAD70AE3...` như test authority và không tuyên bố byte-exact restore. Đây là
new correction task/session vì C14 đã gây destructive overwrite và continuation
đã chạm tool/context limit. Prompt này supersede C14-T3 cho công việc tiếp theo,
nhưng giữ nguyên incident history và C6G locked 14-row contract.

Không mở S11/S12/S13 production. Không commit/push/merge/deploy.

## 2. Required reading — đọc đầy đủ

Sau rules, đọc toàn bộ:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6G_BLOCKED_AUTHORITY_C6H_REBASELINE_PM_DECISION_2026-09-02.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6H_REBASELINE_REVIEW_CHECKLIST_2026-09-02.md`
7. C6F review, C6G incident decision, C6G readiness checklist, original C6G
   prompt, C14-T3 prompt, current T01C TASK/LOG/REPORT and S10 registry.
8. Toàn bộ `output/s10/c6g/**`, đặc biệt `RECOVERY_REPORT.md`, locked 14-row
   matrix, recovery-t3 scripts/manifests/candidates và Manager verify.
9. Actual route/test bytes and read-only Hermes DB chronology. Report chỉ định
   hướng; filesystem, DB read-only và raw commands mới là nguồn sự thật.

## 3. Workspace, immutable facts and model

- Worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch `codex/s08-integration`, reviewed HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`; discover actual và dừng nếu
  mismatch. Preserve dirty attribution. Cấm reset/clean/stash/restore/checkout,
  delete, commit/push/merge.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi test dùng DB/root/basetemp/output/
  cache mới, ngắn và cô lập.
- Read-only Hermes DB:
  `C:\Users\Admin\AppData\Local\hermes\state.db`; chỉ SQLite URI `mode=ro`.
- Old destructive owner `20260902_013803_4d5ce5` và effective T3 continuation
  `20260902_102609_ee5195` đều terminal/frozen. Không resume hai session này và
  không resume bất kỳ lineage T01C cũ nào.
- Tạo đúng một Task ID mới: `S10-T01C-C15`; tạo đúng một fresh compact worker
  session, ghi session ID trả về vào registry trước write đầu tiên.
- Worker model bắt buộc exact selector `comboBAI`, provider `custom`, reasoning
  `max`, Hermes fallback OFF, TTFB 900. Probe route trước dispatch; sai route
  => `BLOCKED_MODEL_ROUTE`, không tự đổi model/fallback.
- Current test:
  `DAD70AE304D123227F9646B501461ED7FD8E6337DADB024269075A8CE63A4591`,
  2,692 lines, 64 textual defs/63 unique nodes, duplicate
  `test_submit_distinct_on_changed_checkpoint`, unresolved `_C10BoomService`,
  Codex run 58 failed/5 passed. Đây chỉ là candidate evidence.
- Current route Phase-A frozen SHA:
  `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`.
- Lost pre-C14 target SHA:
  `963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`,
  57 collected tests. Không được ghi rằng SHA này đã restore.
- VSS 30/08 có ba snapshot 13:03:18/25/33. Cả ba chứa exact ancestor
  `5B312719C7D7349670C9E17DCA87682820ED5A885C55122B8335D923E5FCD6F6`,
  24,542 bytes, 444 lines, 13 tests tại relative path
  `Users\Admin\MotionForge2D-worktrees\s08-integration\tests\test_s10_full_apply_api.py`.

## 4. Session Opening Proposal và bounded execution

Manager giữ vai trò điều phối/read-only. Worker C15 là writer duy nhất.

| Phase | Outcome | Writer scope |
|---|---|---|
| PREP-R | preserve sources, build finite authority map, guards | Manager evidence/registry only |
| C15-A | repair/rebaseline test authority with route frozen | API test + C15 evidence/docs |
| R-GATE | independent semantic/structural authority audit | Manager/read-only |
| C15-B | close exact C6G production REDs | route + API test + evidence/docs |
| EXIT | parallel readers, matrix/focused/broad gates | Manager/read-only evidence |

Serialized writer DAG:

`PREP-R -> C15-A -> WRITER_STOP -> R-GATE -> C15-B(if RED) -> WRITER_STOP
-> PARALLEL_READERS -> MICRO -> MATRIX-14/14 -> FOCUSED -> BROAD -> EXIT`

Normal continuation C15-A -> C15-B sau R-GATE PASS phải resume đúng fresh C15
session và không tính là correction. Ngoài continuation đó, cho phép tối đa
**một combined correction resume** tại gate đầu tiên phát hiện source/test
finding. Manager phải gom mọi finding hữu hạn thành một packet; cấm dispatch
nhiều vòng nhỏ. Nếu combined correction vẫn không qua hoặc worker vi phạm write
safety, dừng blocker thật, không tiếp tục đoán.

Không poll liên tục. Heartbeat 20 phút; audit khi 8 phút không có tiến triển
thực. Manager tự đi tiếp qua các gate được ủy quyền và chỉ dừng ở terminal hoặc
blocker ngoài scope/authority.

## 5. PREP-R — Manager evidence only

1. Ghi timestamp/timezone, rules hash, instruction hashes, branch/HEAD,
   porcelain with attribution, DB env, process/cmdline scan, task ports and all
   current source/test/evidence hashes. Prove zero old writer.
2. Dùng VSS read-only; hash cả ba copies. Preserve đúng bytes của một ancestor
   vào new evidence `output/s10/c6h/manager/prep/vss-ancestor/**`; ghi source
   device path, snapshot time, byte count, SHA and extraction command. Không
   copy vào `tests/`.
3. Hash-index immutable DAD reconstruction, destroyed 278-line backup,
   recovered variants, T3 candidates, read-page coverage and DB exports. Không
   sửa/xóa/rename evidence cũ.
4. Capture guards bằng
   `C:\Users\Admin\MotionForge2D\docs\pm\tools\write_set_guard.py` cho route,
   main test và critical dirty/untracked files. Snapshot bytes trước dispatch;
   verify guard sau mỗi writer stop.
5. Tạo finite `AUTHORITY_SOURCE_LEDGER.md/json` từ:
   - exact 13-test VSS ancestor;
   - 57 collected-node evidence trước C14;
   - accepted C6D/C6E/C6F review contracts;
   - C6G locked 14 rows;
   - successful chronological patch/read evidence;
   - production-independent API/domain invariants.
6. Tạo `RETAINED_57_MATRIX.md/json`: mỗi row có node/contract ID, provenance,
   setup, action, expected HTTP/domain result, exact Job/Run all-row state,
   mutation count, concurrency requirement và stronger replacement nếu có.
   Current route code không được dùng làm oracle để đổi expectation.
7. Reconcile 64 current defs against `57 retained + 5 C6G = 62`. Xác định rõ
   duplicate và mọi surplus/missing definition. Nếu không lập được mapping
   57/57 hữu hạn thì dừng `BLOCKED_REBASELINE_SPEC`, không dispatch worker.
8. Tạo một worker prompt ngắn, tự chứa toàn bộ finding/matrix/scope. Probe exact
   comboBAI, dispatch một fresh C15 session và ghi ledger.

Manager không được sửa/copy-over route hoặc test.

## 6. C15-A — test-authority rebaseline, route frozen

### Allowed writes

- `tests/test_s10_full_apply_api.py` bằng bounded `apply_patch` only;
- append-only T01C LOG/REPORT với mục C15 rõ ràng;
- new `output/s10/c6h/t01c-c15/**`.

`app/api/routes/s10_full_apply.py` và mọi production/test file khác frozen.

### Forbidden

- Cấm `write_file`, whole-file generation vào existing test, `Set-Content`,
  `Out-File`, redirection/heredoc write, Python direct write, editor full-save,
  Copy/Move replace, delete/rename hoặc script-generated overwrite main test.
- Cấm giảm assertion, đổi exact status thành broad success set, skip/xfail,
  swallow exception, conditional pass, mock away real route/DB, hoặc viết test
  theo current implementation để biến defect thành expected behavior.
- Cấm sửa production trong Phase A.

Mỗi patch phải ghi pre/post SHA, line count, affected symbol và guard result.
Shrink ngoài bounded hunk hoặc thay đổi lớn bất thường => dừng ngay
`BLOCKED_DESTRUCTIVE_WRITE / OWNER_TRANSFER_REQUIRED`; không resume worker đó.

### Required result

1. Sửa helper generation/order/import/class mismatch bằng contract và exact
   evidence; không rebuild từ memory. Giữ test qua real FastAPI route và fresh
   isolated SQLite.
2. Giữ đủ 13 VSS-ancestor behavior rows và 57/57 retained matrix rows; stronger
   replacement phải chứng minh không yếu hơn row cũ.
3. Loại duplicate/surplus chỉ khi matrix ledger chỉ rõ disposition. Final là
   đúng 62 textual/unique/collected nodes: 57 retained + 5 C6G.
4. Zero unresolved symbol, duplicate name, collection error, skip/xfail,
   tautology và harness-generation failure.
5. Race tests phải có hai participant sống đồng thời, barrier tại contested
   operation, bounded joins, rendezvous proof, raw outcomes và exact all-row
   lifecycle assertions. Sequential control phải ghi đúng là sequential.
6. Chạy theo thứ tự: `py_compile -> Ruff F -> collect-only -> 13 ancestor
   behaviors -> retained authority matrix -> full API module`, tất cả fresh
   short roots. Route SHA phải giữ nguyên.
7. Phân loại mọi fail còn lại thành `HARNESS/AUTHORITY` hoặc
   `CREDIBLE_PRODUCTION_RED`, kèm raw traceback và exact matrix row. Không sửa
   production để che harness failure.
8. Freeze final Phase-A test SHA/node manifest, append LOG/REPORT, ghi
   `C15_A_SUBMITTED`, dừng writer để Manager R-GATE.

## 7. Manager R-GATE — independent, no source write

Manager verify trực tiếp, không tin riêng REPORT:

- guards, scope, route hash frozen, C14 evidence immutable;
- 57/57 retained map + 5 C6G = 62 unique nodes;
- exact 13 VSS behavior coverage;
- no duplicate/unresolved/skip/xfail/weak assertion/current-code oracle;
- fresh collect, structural AST audit, helper audit and full API run;
- direct source audit của mọi concurrency and all-row assertion;
- each remaining failure is a reproducible production RED, not harness drift.

Nếu có finding, tạo **một combined correction packet duy nhất**, resume đúng
fresh C15 session, sửa toàn bộ rồi rerun R-GATE. Không mở C16 và không chia
finding thành nhiều lượt. Nếu vẫn fail, dừng
`BLOCKED_REBASELINE_QUALITY / PENDING_CODEX_DECISION`.

Chỉ khi R-GATE PASS mới được mở route cho Phase B.

## 8. C15-B — close original C6G contract

Allowed implementation files:

- `app/api/routes/s10_full_apply.py`;
- rebaselined `tests/test_s10_full_apply_api.py`;
- append-only C15 records/evidence.

Mọi edit existing file vẫn patch-only và guarded.

Close đúng 14 locked rows:

1. Một typed durable-job resolver phải xét union của canonical key,
   deterministic generation, stored manifest run/project/plan identity và
   workspace/job/owner identity. Outcomes tối thiểu: true-zero, exact-one,
   wrong-one, ambiguous/multiple và query/read/parse error.
2. Chỉ true-zero được repair. Wrong/ambiguous/error đều fail closed với zero
   mutation, không tạo canonical third job và không trả `reused=true`.
3. Failed predecessor ownership dùng real state/version transition. Cancelled
   predecessor ownership là atomic unique successor insertion hoặc real
   version/state transition; `cancelled -> cancelled` rowcount không phải claim.
4. Race chứng minh winner tại ownership operation, không dùng downstream unique
   constraint/final row count làm bằng chứng duy nhất.
5. Giữ nguyên valid replay, true orphan repair, immutable manifest, lifecycle,
   replay-vs-Retry, worker-claim-vs-Retry và enqueue-compensation controls.
6. Matrix/report/registry thống nhất đúng 14/14; cấm stale 15/6 arithmetic.

Chạy RED micro trước fix, patch tối thiểu, rồi micro + exact 14-row matrix.
Freeze source/test hashes và kết thúc worker `TASK_SUBMITTED`.

## 9. Manager EXIT — nhanh nhưng không giảm chất lượng

Sau zero writer, chạy ba lane read-only song song, mỗi lane dùng resources riêng:

- Lane A: authority provenance, 62-node/AST/helper/scope/guard audit.
- Lane B: identity resolver + Retry ownership/concurrency micro và 14-row matrix.
- Lane C: Ruff F, literal mypy, diff-check, Alembic one-head, OpenAPI op-ID, J1,
  protected-data/hash checks.

Join cả ba PASS trước broad gate. Không chạy broad sớm để rồi lặp lại.

Sau join:

1. focused API/workflow hai lần trên distinct short roots;
2. full `tests/test_s10*.py` hai lần, serialized, distinct short roots;
3. verify final source/test hashes không đổi giữa các run;
4. chỉ retain frontend/build/live/vertical evidence nếu exact relevant hashes
   unchanged; nếu changed thì rerun đúng gate bị ảnh hưởng, không rerun vô ích;
5. complete checklist
   `S10_C6H_REBASELINE_REVIEW_CHECKLIST_2026-09-02.md`;
6. create `output/s10/c6h/manager/exit/NEXT_REVIEW_PACKET.md` indexing raw
   commands, exits, durations, hashes, node/matrix rows, session/model/turns,
   corrections, remaining risks and evidence SHA manifest.

Manager không implementation write. Bất kỳ source/test change sau freeze làm
invalid mọi downstream result và phải quay lại micro/matrix/focused trước một
broad checkpoint cuối.

## 10. Reporting, cleanup and allowed terminals

Append-only registry/T01C records; giữ nguyên lịch sử sai và thêm correction,
không rewrite. Báo rõ `REBASELINED_AFTER_SOURCE_LOSS`, tuyệt đối không dùng từ
`RESTORED_EXACT` cho file mới.

Trước terminal: stop owned worker/readers/watchers, remove heartbeat, prove task
ports free, DB env UNSET, HEAD unchanged, protected hashes intact và no
commit/push/merge.

Allowed terminals:

- success:
  `S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`
- finite spec unavailable:
  `S10-C6H = BLOCKED_REBASELINE_SPEC / PENDING_CODEX_DECISION`
- one combined correction still fails:
  `S10-C6H = BLOCKED_REBASELINE_QUALITY / PENDING_CODEX_DECISION`
- unsafe write:
  `S10-C6H = BLOCKED_DESTRUCTIVE_WRITE / OWNER_TRANSFER_REQUIRED`
- true new scope/model/rules blocker: exact truthful `BLOCKED_*` with evidence.

Không ghi `APPROVED`, `CLOSED`, không mở sprint tiếp theo. Khi success, dừng và
yêu cầu người dùng gọi Codex review một lần tại sprint exit.
