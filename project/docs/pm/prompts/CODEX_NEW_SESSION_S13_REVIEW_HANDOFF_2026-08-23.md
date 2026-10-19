Bắt buộc đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, review, sửa tài liệu hoặc soạn prompt downstream. Báo `RULES_LOADED` kèm đường dẫn, HEAD thực tế và các mục rules chính đã nạp. Nếu file thiếu/không đọc được hoặc có mâu thuẫn chưa giải quyết được, dừng `BLOCKED_RULES`; không làm theo trí nhớ hay bản tóm tắt chat cũ.

Hãy làm việc trong workspace `C:\Users\Admin\MotionForge2D`. Ngay sau khi nạp rules và vẫn trước preflight, hãy đọc và tuân thủ toàn bộ project/workspace instructions mà Codex Settings đã nạp cho task này; tự mở `C:\Users\Admin\MotionForge2D\AGENTS.md` và mọi `AGENTS.md` áp dụng cho các path sẽ đọc/ghi. Báo `WORKSPACE_INSTRUCTIONS_LOADED` kèm các file instruction đã đọc. Nếu instruction trong Settings không hiện hoặc file không đọc được, dừng `BLOCKED_RULES`.

Tiếp theo đọc TOÀN BỘ:

- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\README.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`

Các file trên là nguồn định hướng, nhưng filesystem, process, Git và artifact hiện tại mới là nguồn sự thật. Báo mọi snapshot stale hoặc mâu thuẫn trước khi quyết định gate.

# 1. Authority, vai trò và mục tiêu

Bạn là **CODEX REVIEWER/PM/BA độc lập** tiếp quản MotionForge2D trong một Codex session mới. Bạn không phải Hermes Manager và không phải production writer. Không tự sửa production code/test/migration/UI/config, không tự khởi chạy hay giao tiếp với Hermes; người dùng sẽ tự copy prompt cuối sang Hermes.

Mục tiêu duy nhất của session này:

1. Review độc lập toàn bộ **S13-P00 correction C3** từ artifact/code/filesystem thật, không tin riêng REPORT hoặc kết luận Manager.
2. Kết luận đúng một verdict: `APPROVED` hoặc `CHANGES_REQUESTED`.
3. Ngay sau verdict, viết **một prompt Hermes Manager hoàn chỉnh, copy-paste được**:
   - nếu `CHANGES_REQUESTED`: prompt correction hữu hạn, resume đúng owner S13-P00D cũ;
   - nếu `APPROVED`: Codex/BA tự chốt decomposition và viết prompt điều phối sprint S13 tiếp theo theo rules, với worktree/dependency/concurrency thực tế đã được chứng minh an toàn.

Không dừng sau khi chỉ nêu findings; phải luôn giao prompt downstream tương ứng verdict. Không giao việc planning/phân rã cho Hermes: decomposition, dependency DAG, acceptance và quyền parallel là trách nhiệm của chính Codex/BA session này.

# 2. Trạng thái handoff phải xác minh lại

Quan sát cuối từ session trước, chỉ là mốc để audit chứ không phải sự thật vĩnh viễn:

- Review target: `S13-P00D correction C3`.
- Run root: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s13-p00-readiness\20260823-0045-r1`.
- Synthesis owner phải giữ lineage: `20260823_033031_3a5082`.
- Manager ghi lúc `2026-08-23 16:35 +07`: `S13-P00 = TASK_MANAGER_VERIFIED -> PENDING_CODEX_REVIEW`; S13 production chưa được phép mở.
- Worktree quan sát: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch `codex/s08-integration`, HEAD `a43b20da742996bafcb2f9d1ac57b10d3f1a5204`, dirty count 273, `MOTIONFORGE_DATABASE_URL=[UNSET]`.
- Không quan sát thấy process command line khớp `s13-p00`, `033031_3a5082` hoặc `dispatch-d-c3` tại handoff; phải kiểm tra lại và chỉ review khi writer đã exit, mtime ổn định.
- `CODEX_PM_HANDOFF.md` còn snapshot cũ nói S13 ở correction sớm hơn; artifact C3 thực tế mới hơn và phải được reconcile.
- S13-T01..T08 cùng mọi production subtask vẫn `BLOCKED_ON_S13_P00_REVIEW` cho tới verdict của bạn.

# 3. Protected workspace và preflight bắt buộc

- MAIN: `C:\Users\Admin\MotionForge2D` — protected/reference; chỉ Codex được phép cập nhật đúng review/prompt PM do session này tạo, tuyệt đối không chạm production/data.
- Integration review worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Candidate S13 preparation worktree tồn tại tại `C:\Users\Admin\MotionForge2D-worktrees\prepare-s13-t01`, nhưng không được chọn làm implementation workspace chỉ vì nó sạch hơn: phải kiểm tra nó có đủ uncommitted/integration dependencies hiện hành hay không. Không copy/merge/reset/stash để ép khớp.
- Khám phá lại `git worktree list`, branch, HEAD, complete dirty set, active processes, session/log liveness, last-write stability và DB guard. Phân biệt thay đổi S09/S11/S13 theo path/time/evidence; không quy toàn bộ dirty tree cho S13.
- Không `commit/push/merge/reset/restore/checkout/clean/stash/delete`; không sửa/xóa user data, `channels.json`, `data/**`, DB, fixture hoặc evidence cũ.
- Không chạy test trên production/user DB. P00 là documentation review; mọi kiểm tra phải read-only, trừ file PM review/prompt được cấp quyền rõ ở Mục 8.

# 4. Evidence bắt buộc phải đọc trực tiếp

Đọc toàn bộ, không chỉ grep/tail:

1. Review cũ:
   `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S13_P00_PM_REVIEW_2026-08-23.md`.
2. Manager evidence:
   `...\20260823-0045-r1\manager\MANAGER_LOG.md`, `C3_hash_baseline.txt`, và log C3 cần thiết để xác minh lineage/exit/write scope.
3. Toàn bộ 17 file lane A/B/C dưới `lane-a\`, `lane-b\`, `lane-c\`.
4. Toàn bộ 9 file hiện hữu dưới `synthesis\`, đặc biệt:
   - `READINESS_REPORT.md`
   - `DEPENDENCY_DAG.md`
   - `WRITESET_MATRIX.md`
   - `TASK_MAP_T01_T08_DRAFT.md`
   - `ACCEPTANCE_GATES.md`
   - `RISK_REGISTER.md`
   - `OPEN_PRODUCT_DECISIONS.md`
   - `LOG.md`
   - `REPORT.md`
5. Các code/schema/migration/route/UI contracts mà synthesis viện dẫn. Mọi load-bearing claim phải được spot-check từ source thật; không mặc nhiên coi lane audit đúng.
6. Trạng thái S06/S07/S08 và S09/S11 hiện hành đủ để xác định S13 dependency và write-set conflict. Không review lại sprint khác ngoài mức cần để chứng minh dependency/concurrency.

# 5. Review checklist độc lập cho C3

Phải kiểm tra ít nhất các điểm sau bằng nội dung/diff/hash thực tế:

1. A/B/C byte-identical với baseline; chỉ đúng 9 synthesis files được C3 sửa; MAIN, HEAD và protected data không bị S13 làm đổi.
2. Migration plan chỉ dùng `migrations/versions/**`, discover live single head tại thời điểm task chạy và không hard-code revision.
3. Có đúng 19 active production Task IDs `S13-T01A..T08B`; từng task thực sự đủ nhỏ cho một worker session và có outcome, dependency, exclusive write allowlist, forbidden paths, binary acceptance, evidence và new-session rule.
4. DAG không cycle; mọi parallel wave có bằng chứng dependency-ready, stable contract, disjoint write-set và isolated DB/temp/output/port/cache. Shared schema/API/migration/frontend pressure phải serialize rõ.
5. Không có production `qa_stub.py`; fake transport chỉ dưới `tests/**`; production resolver fail closed.
6. DB guard đồng thời cấm production/user DB và bắt buộc isolated temporary DB cho migration round-trip/FK/parity tests.
7. Toàn S13 không có live network/provider/localhost probe authority; chỉ fake transports. Không còn câu chữ mở cửa ngầm bằng “PM permission”, deviation hoặc exception.
8. Validator ownership không overlap: T04B chỉ technical geometry set đã freeze; T04C sở hữu identity/style/cross-view set gồm V13/V15. Không còn V15 thuộc T04B.
9. F-9 legacy-status decision nhất quán: legacy preserved, candidate lifecycle tách riêng, cleanup backlogged; T04A không bị D4-4 stale block.
10. F-10 benchmark decision nhất quán: exact 30-member alpha baseline, truth/threshold freeze-before-run; T08A không đòi roster; T08B chỉ mở khi N>=3 blind reviewer roster đã confirm; thiếu roster là `BLOCKED_DEPENDENCY`, deviation note không thể thay PASS evidence.
11. X6 trỏ đúng F-9; R7 không trao network authority; mọi OPEN/FROZEN/SUPERSEDED marker không mâu thuẫn.
12. Acceptance phản ánh đầy đủ mandatory S13 identity-quality requirements trong ROADMAP và Source-Locked target profile; không hạ scope để dễ pass.
13. Phân rã có thể triển khai thực tế trên repository hiện hành: tên module/route/migration/UI path không bịa, write-set không bỏ sót shared files, dependencies lên character library/durable jobs/version pinning đúng.
14. Đánh giá khách quan liệu S13 có thể chạy song song với S09/S11. Chỉ cho phép khi exact worktree/base và write/runtime sets thực sự tách biệt; nếu không chứng minh được thì prompt downstream phải chặn dispatch hoặc serialize, không dùng tốc độ làm lý do.

# 6. Quy tắc verdict và findings

- Không mặc định approve vì Manager báo xanh.
- Finding phải có `P0/P1/P2`, exact file:dòng, chứng cứ/cách tái hiện, expected/actual, impact, test/evidence cần bổ sung và exact owner nhận correction.
- `APPROVED` chỉ khi toàn bộ P00 readiness/decomposition đủ để Codex cấp quyền production mà không cần Hermes tự suy luận planning.
- Nếu còn quyết định BA quan trọng chưa freeze, write-set/DAG không an toàn hoặc acceptance thiếu, verdict là `CHANGES_REQUESTED`.

# 7. Prompt downstream bắt buộc theo verdict

## Nếu CHANGES_REQUESTED

Viết prompt correction hoàn chỉnh bắt đầu bằng lệnh đọc toàn bộ `HERMES_AUTOPILOT_RULES.md`. Chỉ resume exact synthesis owner `20260823_033031_3a5082`, giữ provider/model/API mode/reasoning cũ: provider `custom` qua 9Router `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled. Không tạo replacement session khi owner còn resume được; không rerun A/B/C; chỉ cho sửa exact existing synthesis files liên quan findings; không mở production. Prompt phải có từng finding, binary acceptance, hashes, heartbeat 20 phút, audit 8 phút, retry-wait 5 phút và terminal `TASK_MANAGER_VERIFIED -> PENDING_CODEX_REVIEW`.

## Nếu APPROVED

Codex/BA tự freeze task map cuối và viết **một prompt Hermes Manager chạy full sprint S13** nếu và chỉ nếu dependency/worktree audit chứng minh có thể mở production. Prompt đó phải:

- Bắt đầu bằng lệnh Manager đọc toàn bộ rules, rồi handoff/roadmap/current artifacts và báo `RULES_LOADED`.
- Ghi Codex là reviewer gate; Hermes Manager không code.
- Chỉ cấp quyền exact sprint S13/subtasks đã được Codex duyệt; không đưa backlog ngoài S13.
- Liệt kê đầy đủ từng Task ID đã freeze (dự kiến 19 IDs `T01A..T08B`) với outcome, dependency, exclusive write allowlist, forbidden paths, binary acceptance và evidence — không bảo Hermes tự chia task.
- Một task mới = một worker session/chat mới. Correction của task nào phải resume đúng session owner của task đó đến khi xong. Manager duy trì registry.
- Worker mới do manager chat này tạo phải dùng provider `custom` qua 9Router `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled. Session cũ giữ route cũ; route sai dừng `BLOCKED_MODEL_ROUTE`.
- Chạy tối đa mọi task dependency-ready và disjoint đã được Codex chứng minh; không chạy song song task chung schema/API/migration/component/fixture/runtime. Global gates qua mutex tại checkpoint ổn định.
- Pin exact workspace/worktree/branch/current HEAD/dirty baseline sau audit. Nếu S09/S11 còn writer hoặc dependency overlap, prompt phải nêu gate chờ/serialize cụ thể; không tự chuyển sang stale `prepare-s13-t01` và không copy/merge uncommitted state.
- Heartbeat ít nhất 20 phút; 8 phút không progress phải audit; lỗi kết nối tạm thời báo ngay, chờ đủ 5 phút rồi resume same session/same model, không fallback.
- Manager tự review/correction từng task, nhưng không ghi Codex APPROVED. Được chạy toàn sprint đã cấp quyền rồi dừng đúng một lần ở `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW` để Codex review sprint exit.
- Không commit/push/merge/reset/restore/clean/stash/delete; không production DB/network probe nếu chưa có quyền đích danh; mọi test dùng isolated resources.
- Có required report: task/session/model map, changed files, DAG/waves, commands/results, migration head, DB/network guards, screenshots/benchmark evidence nếu tới scope, protected-data comparison, corrections và residual risks.
- Kết thúc bằng start command yêu cầu preflight/dispatch ngay, không chỉ trả lại kế hoạch.

Nếu P00 được APPROVED nhưng dependency hoặc integration base chưa đủ an toàn để mở S13 production, không giả vờ cấp full-sprint authority. Hãy nêu blocker chính xác và viết prompt Hermes **preflight/wait-only** không có quyền production, hoặc correction/integration-readiness prompt đúng owner/scope cần thiết; đồng thời chỉ rõ điều kiện nhị phân để Codex mở sprint sau.

# 8. Output và write authority của Codex session này

Được phép tạo/cập nhật đúng các PM artifacts cần thiết sau khi review xong và tree ổn định:

- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S13_P00_PM_REVIEW_2026-08-23.md` — append vòng review C3, không xóa lịch sử.
- Một file prompt mới dưới `C:\Users\Admin\MotionForge2D\docs\pm\prompts\` chứa nguyên văn prompt downstream vừa kết luận.

Không được sửa production code/test/migration/UI/config/data. Trước khi ghi, kiểm tra dirty ownership để không ghi đè thay đổi người khác. Nếu không thể ghi an toàn, vẫn trả toàn bộ verdict và prompt trong chat, báo rõ file chưa ghi.

# 9. Terminal response bắt buộc

Trả về theo thứ tự:

1. `WORKSPACE_INSTRUCTIONS_LOADED` và `RULES_LOADED`.
2. Preflight facts + mọi discrepancy stale.
3. Findings theo P-level, hoặc nói rõ không có actionable finding.
4. Verdict `S13-P00 APPROVED` hoặc `S13-P00 CHANGES_REQUESTED`.
5. Dependency/concurrency decision cho S13 so với S09/S11.
6. **Nguyên văn prompt Hermes Manager hoàn chỉnh trong một code block duy nhất** để người dùng copy.
7. Các PM artifact đã ghi và verification đã chạy.

Bắt đầu ngay bằng việc đọc Settings/workspace instructions và toàn bộ rules; sau đó audit process/tree/artifact thật, review C3 độc lập và giao verdict + prompt. Không chỉ tóm tắt REPORT, không hỏi lại người dùng nếu có thể tự kiểm chứng từ workspace.
