# S10-C6H R2 — Relevant Manifest Scope + Write-Safety Recovery Manager Prompt

## 0. Mandatory first action

**BẮT BUỘC:** trước mọi preflight, state change hoặc dispatch, đọc TOÀN BỘ file:

`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`

Sau đó đọc TOÀN BỘ các authority sau:

- `C:\Users\Admin\MotionForge2D\AGENTS.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6H_R1_PM_REVIEW_2026-09-03.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6H_R1_UNION_IDENTITY_RESOLVER_FINAL_CORRECTION_MANAGER_2026-09-02.md`
- current S10-C6H `TASK.md`, `LOG.md`, `REPORT.md`, registry and R1 exit packet under `output/s10/c6h/r1/`.

Ghi evidence `RULES_LOADED` gồm path, line count, SHA-256 và mtime cho từng file. File protocol đúng là `docs/pm/SESSION_PROTOCOL.md`; không được dừng vì tên cũ `HERMES_SESSION_PROTOCOL.md` không tồn tại.

Đây là execution prompt. Bắt đầu preflight và dispatch ngay khi đủ gate; không chỉ trả kế hoạch.

## 1. Role and authority

Bạn là một **Hermes Manager session MỚI, gọn** cho đúng correction `S10-C6H R2`. Manager chỉ preflight, tạo đúng một recovery worker, monitor, review, chạy verification và ghi tài liệu/evidence. Manager **không tự sửa production code hoặc test**.

Authority của prompt này:

`AUTHORIZED_TO_DISPATCH` duy nhất cho `S10-C6H R2`.

Không có quyền:

- ghi `APPROVED`, `SPRINT_CLOSED` hoặc mở S11;
- commit, merge, push, rebase hoặc clean/reset;
- sửa schema/migration/UI/renderer/queue/config ngoài allowlist;
- chạy backlog khác hoặc cross-sprint work;
- dùng nhiều writer.

## 2. Current verdict

Codex verdict hiện hành:

`S10-C6H = CHANGES_REQUESTED / R2_AUTHORIZED / NOT_APPROVED / S10_NOT_CLOSED`

R1 đã đóng phần lớn lỗi union identity ban đầu và có gate xanh, nhưng còn hai finding bắt buộc:

1. `P1 RELEVANT_MANIFEST_SCOPE`: query hiện chọn mọi manifest có field name `"run_id"`, nên một malformed manifest hoàn toàn không liên quan có thể làm target true-zero replay trả `409` và không repair.
2. `P2 PER_ROW_SIGNAL`: `canonical_complete` dùng `sig_manifest` còn sót từ vòng lặp thay vì signal của claimant đang phân loại.

Ngoài ra worker R1 vi phạm write-safety lặp lại; R2 bắt buộc owner transfer và unified-patch-only.

## 3. Pinned workspace and preimage authority

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch: `codex/s08-integration`
- HEAD: `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`
- Expected dirty baseline count: `66` porcelain entries; đây là shared dirty authority, không được clean.
- Critical route:
  - `app/api/routes/s10_full_apply.py`
  - expected SHA-256 `BBF55D285C5B0A8B7BC5A519912E7D5C10F6481A2F74950F7FDD804A7F378A31`
- Critical test authority:
  - `tests/test_s10_full_apply_api.py`
  - expected SHA-256 `6978D2BEC61117FB7E0E875301BBCEB5BFF679C94641F5D32F967FCC5A40BF19`
  - expected unique test defs before R2: `68`
- R1 packet SHA-256: `0C5D65E0298D30C7B021553DA1BF62D499A59280083C710C57047406E41CA870`

Nếu branch, HEAD hoặc một trong hai critical SHA không khớp: không dispatch; ghi `BLOCKED_PREIMAGE_DRIFT` kèm actual hashes và dừng để Codex review. Không tự restore.

Preflight còn phải xác nhận:

- không có S10-C6H worker/pytest/process writer còn chạy;
- các port dùng cho focused/broad gates đang free;
- các biến DB/runtime production như `MOTIONFORGE_DATABASE_URL` không bị trỏ vào dữ liệu thật;
- mọi DB test dùng temp directory mới và fresh Alembic SQLite;
- `C:\Users\Admin\AppData\Local\hermes\state.db` chỉ được mở read-only;
- ghi SHA/byte-size/line-count/tracked-dirty attribution và tạo Manager-owned byte snapshots trong `output/s10/c6h/r2/manager/guard/`; verify snapshot hashes.

Snapshot chỉ là authority/evidence cho Manager/Codex. Worker không có quyền copy snapshot đè lại file chính.

## 4. Context-health and owner transfer

### Manager

Manager cũ `20260902_211154_54134d` không được resume cho R2. Evidence: state record còn mở, `284` messages, `160` tool calls, `605015` input tokens, và đã bỏ sót ba forbidden copy-overwrites. Trước dispatch, xác nhận không còn process/child/writer của Manager cũ; ghi `OLD_MANAGER_QUIESCENT`. Nếu còn writer, dừng `BLOCKED_CONCURRENT_WRITER`.

### Worker

Freeze vĩnh viễn các owner cũ, đặc biệt:

- `20260903_001126_2a17f4` — ended `agent_close`, đã lặp lại forbidden copy-overwrite sau recovery transfer.

Không resume session này. Tạo **đúng một** fresh recovery worker cho cùng Task ID:

- Task ID: `S10-T01C-C15`
- Recovery reason: `REPEATED_FORBIDDEN_COPY_OVERWRITE_AFTER_RECOVERY_TRANSFER`
- Handoff chỉ gồm current verdict, hai current SHA, findings còn mở, allowlist, acceptance và gates; không nhồi full lịch sử.
- Registry phải ghi owner transfer trước khi worker write.
- Max concurrent writer: `1`.

## 5. Model policy

Manager và fresh worker dùng:

- provider: custom route;
- exact model ID: `ocg/deepseek-v4-flash`;
- requested reasoning: `max`;
- fallback: disabled;
- TTFB timeout: `900` seconds;
- worker iteration/token budget đủ cho một bounded pass; không tự đổi model để né lỗi.

Sau API call đầu tiên, audit read-only session state và ghi resolved provider/model/config.

- Wrong provider/model hoặc fallback route: `BLOCKED_MODEL_ROUTE`.
- Nếu exact model đúng nhưng runtime không lưu/expose reasoning max, ghi `RUNTIME_CONFIG_GAP`; không được tuyên bố reasoning max đã được chứng minh. Prompt này cho phép tiếp tục bounded R2 trong trường hợp đó.
- Connection/502/503/504 dùng đúng retry policy trong canonical rules: wait đủ 5 phút, liveness audit, resume exact same new worker; không tạo worker thứ hai.

## 6. Exclusive write-set

Fresh worker chỉ được sửa bằng bounded unified patch:

1. `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\app\api\routes\s10_full_apply.py`
2. `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\tests\test_s10_full_apply_api.py`
3. tạo evidence mới dưới `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s10\c6h\r2\worker\**`

Manager có thể append/chỉnh tài liệu điều phối R2 trong đúng S10 registry/TASK/LOG/REPORT và tạo evidence dưới `output/s10/c6h/r2/manager/**`; Manager không sửa hai implementation/test files.

Mọi path khác forbidden, kể cả migration, model, service, config, UI, S11 docs/code và historical evidence.

## 7. Absolute write-safety contract

Đối với hai critical files hiện hữu, worker chỉ được dùng **V4A/unified patch mode** với exact, nhỏ, một hunk mỗi lần. Sau từng hunk phải chạy ngay:

- hash/line-count/size delta;
- `python -m py_compile` cho file Python vừa đổi;
- targeted collect/test phù hợp.

Nghiêm cấm:

- patch `mode=replace` hoặc fuzzy whole-string replacement;
- `write_file` trên file hiện hữu;
- `cp`, `copy`, `Copy-Item`, `move`, `Move-Item`, rename-overwrite;
- delete/recreate, truncate, whole-file regeneration;
- shell redirection hoặc script/Python mở file chính để ghi;
- restore/copy snapshot, `.bak`, Git blob hoặc evidence đè lên file chính;
- sửa indentation/file bằng formatter diện rộng;
- tiếp tục sau patch sai path, indentation drift, unexpected shrink hoặc compile failure.

Nếu một patch làm hỏng file hoặc tool trả diff bất thường:

1. dừng writer ngay;
2. không restore và không thử patch lần hai;
3. bảo toàn raw tool payload, current broken bytes và hashes ngoài path chính nếu có thể làm read-only/copy-out mà không ghi đè authority;
4. báo `BLOCKED_UNSAFE_WRITE / CODEX_DECISION_REQUIRED`.

Đây là terminal negative gate. Green tests không waive được vi phạm này.

## 8. Required product correction

### F1 — Candidate relevance boundary

Sửa `_s10_resolve_job_identity` để candidate discovery vẫn là union độc lập của:

- exact canonical idempotency key;
- exact deterministic input generation;
- manifest text plausibly carrying **exact target `run_id`**, không phải mọi row chỉ có field name `"run_id"`.

Sau bounded prefilter, parse và validate exact run/project/plan as needed. Semantics bắt buộc:

| Scenario | Required result |
|---|---|
| Không có exact key/gen và không manifest nào nhắc exact target run | `true-zero`, repair được |
| Unrelated malformed manifest không chứa target run ID | không phải candidate, không block target repair |
| Unrelated valid manifest cho run/project khác | không phải claimant, không block target repair |
| Malformed manifest text có exact target run ID, key/gen đã tamper | `read/parse/query-error`, fail closed, zero mutation |
| Một claimant theo manifest target hoặc gen nhưng identity không complete | `wrong-one`, fail closed |
| Hai hay nhiều claimant theo union signals | `ambiguous-multiple`, fail closed |
| Exact valid existing job | retained replay behavior, không duplicate |

Không được nới thành prefix-only lookup, không broad table parse, không catch parse error của row ngoài target candidate, không biến read error thành true-zero.

### F2 — Per-row signal correctness

Không dùng `sig_manifest`/signal variable tồn dư từ loop để phân loại claimant khác. Lưu signal theo candidate hoặc recompute trực tiếp cho `claims[0]`. Manager phải review exact diff và chứng minh classification dùng đúng row.

### F3 — Minimality

Không refactor ngoài resolver/call-site cần thiết. Không đổi API contract ngoài việc unrelated rows không còn gây false `409`. Preserve C6G/C6H retained semantics.

## 9. Required tests — RED first

Worker phải patch test authority trước, bằng unified patch duy nhất từng hunk, rồi chạy RED trên current R1 route trước khi sửa production.

### R2-A — New real-stack regression

Thêm `test_r2_unrelated_malformed_manifest_does_not_block_true_zero_repair`:

1. real FastAPI route + real `JobService` + fresh isolated Alembic SQLite;
2. force target enqueue failure để run `failed`, target có zero jobs;
3. insert một unrelated durable job có unrelated type/workspace/owner/key/generation và malformed manifest không chứa target run ID;
4. replay target;
5. RED hiện tại phải chứng minh actual `409` và zero target repair;
6. GREEN sau fix phải chứng minh success/reuse contract của true-zero repair, đúng một target canonical job được tạo, unrelated row giữ nguyên, tổng job count tăng đúng một, run count không đổi.

### R2-B — Repair U4 authority

Sửa `test_r1_u4_invalid_manifest_parse_fails_closed` để malformed JSON text chứa **exact runtime `run_id` của target** trước điểm truncate. Test vẫn phải chứng minh fail closed, zero mutation, no second canonical job.

### R2-C — Unrelated valid row

Thêm một real-stack row chứng minh unrelated well-formed manifest/run/project không block target true-zero repair. Có thể là test riêng hoặc cùng fixture nhưng assertions phải độc lập và rõ.

### R2-D — Retained rows

Retain và rerun:

- U1-U6;
- C6G manager matrix 14/14;
- exact valid replay;
- ambiguous multiple claimants;
- relevant malformed claimant;
- combined key/gen/manifest tamper cases.

Sau test additions, unique test defs dự kiến `70` (68 + 2). Nếu count khác, Manager phải giải thích exact additions/removals; zero duplicate defs, zero lost retained defs.

## 10. Gate order

Mọi command, exit code, duration, SHA và stdout/stderr phải lưu trong `output/s10/c6h/r2/**`.

### Worker gates

1. Preimage/guard gate.
2. Patch R2-A/R2-B/R2-C tests only.
3. RED gate: R2-A phải fail trên current route vì unrelated malformed row gây false block. Không sửa assertion để giả RED.
4. Patch resolver production bằng unified patch.
5. Immediate compile/collect.
6. GREEN micro: R2-A/B/C.
7. U1-U6 + all R2 rows.
8. Retained C6G 14/14 matrix.
9. Full `tests/test_s10_full_apply_api.py`.
10. Ruff `--select F` trên hai changed files.
11. Mypy retained command trên ba prior files.
12. `git diff --check`, duplicate-def audit, retained-symbol audit, destructive-shrink guard.
13. Worker submits evidence only, exits, zero writer.

### Manager independent gates after worker exit

1. Verify actual bytes/hashes and diff minimality.
2. Independently rerun R2 micro + U1-U6.
3. Independently rerun C6G 14/14 matrix.
4. Full API module.
5. Focused S10 command twice in isolated resources.
6. Final broad gate twice under global mutex, no writer.
7. Ruff/mypy/diff/duplicate-def/Alembic/OpenAPI gates from R1 contract.
8. Raw state DB tool-call audit for forbidden writes.

Không dùng broad xanh để waive một binary row hoặc write-safety incident.

## 11. Raw session audit gate

Trước positive submission, Manager phải mở worker session data read-only và inspect raw tool calls/messages. Search/report ít nhất:

- `write_file` targeting critical files;
- patch mode `replace`;
- `cp`, `copy`, `Copy-Item`, `move`, delete/recreate;
- shell redirection/direct-write scripts targeting critical files;
- wrong provider/model/fallback;
- duplicate/concurrent writers.

Positive gate yêu cầu zero forbidden critical-file write. Nếu có một lần: freeze worker và terminal `BLOCKED_UNSAFE_WRITE`; không tự chữa và không nộp green packet.

## 12. Parallelism and liveness

- Maximum active writer wave: `1` vì route và test authority chung.
- Test parallelism chỉ được dùng khi DB/temp/ports tách biệt; final broad qua mutex.
- Heartbeat ít nhất mỗi 20 phút khi còn active task.
- Nếu 8 phút không có progress/log mới: audit process, session input wait, tail log, connection, lock, port và current file hashes.
- Báo incident ngay, không chờ heartbeat.
- Manager tiếp tục `monitor -> review -> correction/resume same new owner -> verify -> report` cho tới terminal state được cấp quyền.

Không dừng chỉ vì worker trả lời hoặc một gate xanh. Không hỏi Codex về quyết định đã được prompt này giải đáp.

## 13. Registry and required report

Registry/REPORT/LOG phải ghi trung thực:

- old Manager retirement evidence;
- frozen R1 worker and recovery reason;
- new worker session ID/model/config/start/end;
- exact write-set and pre/post hashes, sizes, lines;
- RED and GREEN commands/results;
- full focused/broad counts/durations;
- raw tool-call safety audit result;
- files changed;
- remaining risk/blocker;
- no commit/merge/push;
- no S11 authorization.

Packet terminal positive duy nhất được phép:

`S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Packet phải được ghi **sau** final broad R2 log và raw session audit, với timestamp thật `+07:00`. Sau đó remove active heartbeat, confirm zero writer/free ports, và Manager dừng để Codex review.

Negative terminal hợp lệ gồm:

- `BLOCKED_PREIMAGE_DRIFT`
- `BLOCKED_CONCURRENT_WRITER`
- `BLOCKED_MODEL_ROUTE`
- `BLOCKED_UNSAFE_WRITE / CODEX_DECISION_REQUIRED`
- `BLOCKED_TEST_AUTHORITY`
- `CHANGES_REQUIRED / MANAGER_VERIFICATION_FAILED`

Không được tự ghi `APPROVED`, `CLOSED` hoặc mở S11.

## 14. Start now

Thực hiện ngay theo thứ tự:

1. `RULES_LOADED` + authority hashes;
2. workspace/session/process/DB preflight;
3. retire/freeze old lineage and update registry;
4. create exactly one fresh `S10-T01C-C15` recovery worker with exact OCG route;
5. monitor continuously;
6. enforce unified-patch-only and raw session audit;
7. run all independent gates;
8. emit one truthful terminal packet and stop for Codex rereview.
