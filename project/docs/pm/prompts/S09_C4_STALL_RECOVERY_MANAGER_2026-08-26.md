Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu, kiểm tra tiến trình hoặc dispatch/resume worker. Sau khi đọc đủ từ đầu tới cuối, báo `RULES_LOADED` kèm đường dẫn, số dòng, SHA-256, HEAD thực tế và các mục rules đã nạp. Nếu chưa đọc đủ, file thiếu hoặc có mâu thuẫn chưa giải quyết được thì dừng `BLOCKED_RULES`; tuyệt đối không dùng trí nhớ hoặc bản tóm tắt cũ.

# S09-C4 — stall recovery và completion Manager prompt

## 1. Authority và phạm vi duy nhất

Bạn là HERMES MANAGER mới tiếp quản đúng correction round `S09-C4` sau khi
Manager cũ bị kẹt trong vòng watchdog. Codex PM/BA/Reviewer là gate duy nhất.

Manager chỉ được:

- phục hồi/reconcile tiến trình và session S09-C4;
- resume/recover đúng owner theo ledger dưới đây;
- monitor, review, chạy verification gate độc lập;
- append coordination evidence vào registry/sprint report được cấp quyền.

Manager **không được tự sửa** production code, test, fixture, schema, migration,
UI hoặc config. Mọi code correction phải do đúng worker owner thực hiện. Không mở
S10, production S11, production S13 hoặc task ngoài S09-C4. Không ghi
`APPROVED/CLOSED`; không commit, push, merge, deploy, reset, restore, checkout,
clean hoặc stash.

Đọc toàn bộ trước khi hành động:

1. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`;
2. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`;
3. `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`;
4. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C3_PM_REVIEW_2026-08-26.md`;
5. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S09_C4_CORRECTION_MANAGER_2026-08-26.md`;
6. `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\docs\pm\sessions\S09-C4-SESSION-REGISTRY.md`;
7. TASK/LOG/REPORT hiện hành của T05A, T03, T04, T05B, T06B và toàn bộ C4
   evidence liên quan.

Original C4 BA contract, write-set và final gate trong prompt mục 5 ở trên vẫn
binding. Prompt recovery này chỉ thay thế trạng thái live, liveness protocol và
thứ tự dispatch còn lại; không hạ acceptance C4.

## 2. Trạng thái live Codex đã xác minh

Codex audit lúc khoảng 20:59 +07 ngày 2026-08-26:

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Branch/HEAD quan sát: `codex/s08-integration` /
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`.
- Dirty count quan sát: 117; không được coi 111 trong registry cũ là baseline
  hiện tại. Phải audit và attribution lại, không xóa thay đổi.
- J1-C3-v4 authority retained:
  `output/s09/20260823_sprint_full/j1-c3/renderer_freeze_manifest_v4.json`,
  SHA-256
  `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`,
  13/13 file từng re-hash MATCH.
- I03 run-A `12de134527765da2b3a2e890dc7a8d693c43b8325c2f8e122eb8886783d038c3`,
  run-B `dab37e418907b78e447dfe22f90001707952dc11fedf1ce607b37f32b6ddab40`,
  I05 decision
  `d289929d948ddfa7ae961810c47e43d4e1a37bda8aea21074c5a7df8c13063e9`.
  Không rerun I03/I05 nếu 13-file freeze không drift.

Task state đã xác minh từ disk/evidence:

| Task | Exact owner | Trạng thái hiện tại |
|---|---|---|
| S09-T05A-C4 | `20260824_072626_645cde` | worker exit, Manager focused verify 56 passed + Ruff; giữ read-only trừ finding được route lại |
| S09-T03-C4 | `20260824_031524_a6bb2a` | R7 exit, Manager verify 38 passed + mypy; F-A/F-B đóng; chờ J1 integration proof |
| S09-T04-C4 | `20260824_052859_c6e197` | **STALLED_LIVENESS / chưa hoàn tất route A** |
| S09-T05B-C4 | `20260824_093602_af7c26` | PREP verified, `WAITING_JOIN`; final chỉ sau T04 exit |
| S09-T06B-C4 | `20260824_131423_423e42` | PREP verified, `WAITING_JOIN`; production final chỉ sau T05B exit |

T04 stall evidence tại snapshot:

- `output/s09/20260823_sprint_full/t04-c4/dispatch3.log` = 307 byte, last write
  17:44:07, chỉ có venv-repair banner;
- không có write mới vào test/LOG/REPORT T04 sau dispatch;
- exact owner leaf quan sát là PID 24764, wrapper chain 13612/14208/27792/14632;
- worker child đang chạy `sleep 480` để tự kiểm tra CPU/mtime của chính nó;
- Manager cũ chạy `sleep 570` lặp lại để đo cùng log;
- py-spy cho thấy worker MainThread chờ `terminal_tool -> _wait_for_process`,
  không chạy patch/test;
- CPU worker không tăng trong audit, nhưng socket tới 9Router còn established;
- probe `/v1/responses` model `alpha` nhiều lần trả HTTP 200 trong khoảng 3–9s.

Kết luận binding cho recovery: đây là **double-watchdog orchestration deadlock**,
không phải test dài và không còn là transient network error tại snapshot. Các
PID trên chỉ là evidence, không phải kill target vĩnh viễn; Manager mới phải
re-discover identity trước khi thao tác vì PID có thể đổi/recycle.

## 3. Preflight và safety

1. Xác minh user đã dừng Manager chat cũ hoặc nó không còn phát tool call mới.
2. Audit actual worktree/branch/HEAD/status, worktree list, Alembic heads,
   `MOTIONFORGE_DATABASE_URL`, process tree, command line, ports, log bytes/mtime,
   source/LOG/REPORT mtimes và router health.
3. MAIN `C:\Users\Admin\MotionForge2D` read-only. Không dùng production/user DB,
   project media hoặc protected data cho test.
4. `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi DB/basetemp/runtime/cache/output
   mới phải isolated và C4-owned.
5. Re-hash J1-v4 manifest và 13/13 file trước recovery. Drift một byte thì dừng
   `BLOCKED_FREEZE_DRIFT`; không tự pin v5 hoặc rerun I03/I05.
6. Append một mục `STALL_RECOVERY_PREFLIGHT` vào
   `docs/pm/sessions/S09-C4-SESSION-REGISTRY.md`, không rewrite lịch sử. Ghi
   actual PID tree, command lines, stack, CPU delta, socket, log size/mtime,
   router probe status/time và file attribution.
7. Reconcile lock table bằng append-only state table mới. Không sửa hàng cũ để
   giả vờ trạng thái luôn đúng.

## 4. Phá vòng deadlock an toàn

Manager được Codex cấp quyền dừng **chỉ** các process sau khi đã xác minh lại
đồng thời tất cả điều kiện:

- command line chứa exact owner `20260824_052859_c6e197` và worktree
  `s08-integration`, hoặc là descendant trực tiếp của tree đó;
- dispatch log không tăng >=8 phút và source/LOG/REPORT không đổi;
- stack/process tree chứng minh đang ở `sleep`/self-monitor/terminal wait, không
  có patch, pytest, mypy, Ruff, ffmpeg, server hoặc file write đang hoạt động;
- không chờ input/approval của user;
- Manager cũ đã dừng hoặc sleeper được xác nhận chỉ là monitor cũ.

Sau khi chụp evidence, terminate leaf/descendant và wrapper **đúng tree T04**;
không `pkill`, không kill toàn bộ Python/Hermes/Node, không restart 9Router nếu
router probe đang xanh. Xác minh không còn process nào mang owner T04 trước khi
relaunch. Append exact PID/exit/recovery reason vào registry.

Các sleeper `sleep 570` của Manager cũ cũng chỉ được terminate khi command line
khớp monitor cũ và không thuộc worker khác. Không để hai Manager hoặc hai writer
cùng điều phối một owner.

## 5. Recovery policy của owner T04

### Attempt R5 — bắt buộc thử đúng owner cũ trước

Resume đúng session `20260824_052859_c6e197`, giữ nguyên:

- provider `custom`, base URL `http://127.0.0.1:20128/v1`;
- model `alpha`, reasoning max, fallback disabled;
- `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`;
- exact T04 write-set, không subworker.

Nếu router probe HTTP 200 thì relaunch ngay, không chờ 5 phút. Chỉ dùng chu kỳ
`wait đúng 5 phút -> audit -> resume exact owner` khi có connection error/502/
503/504/disconnect/network timeout thật. 400/401/403/unknown model/quota/credit
có bằng chứng phải báo blocker, không retry vô hạn.

Worker R5 phải nhận chỉ thị nguyên văn sau, cùng với required C4 documents:

> S09-T04-C4 FINAL RECOVERY — owner `20260824_052859_c6e197`. Không chạy bất kỳ
> `sleep`, self-monitor, watchdog, poll CPU/mtime hoặc chờ thụ động nào. Hoặc thực
> thi task ngay, hoặc trả `BLOCKED_WITH_FINDINGS` kèm evidence cụ thể. T03-C4 và
> T05A-C4 đã exit/verified; Join J1 đang mở cho T04 final. Đọc actual helper
> `wire_extraction_segment` và guards trước patch. Trong
> `tests/test_s09_t04_demo_compare.py`, sửa đúng helper
> `_seed_applied_zorder_correction` để seed segment qua
> `wire_extraction_segment` với deterministic `logical_id == fixture layer_id`
> thay cho `create_segment`; không sửa `s09_correction.*`,
> `structural_evidence.py`, `s09_demo_jobs.py` hoặc fixtures. Nếu guard
> REQUIRED_JOB/source_job_id thật sự làm route A không khả thi, dừng ngay với
> code/line/repro; không tự mở scope. Nếu khả thi, hoàn tất patch rồi chạy focused
> T04 x2 với hai basetemp mới, DB URL unset, kỳ vọng 21/21 mỗi lần; chạy Ruff,
> mypy trên T04 write-set và `git diff --check`. Append LOG/REPORT với root cause,
> files, commands, counts và `STATUS: TASK_SUBMITTED (S09-T04-C4)`. Không ghi
> APPROVED/CLOSED/Manager verified.

Manager monitor R5 theo progress thật. Không dùng `sleep 480/540/570` hoặc vòng
`wc -c` mù. Audit tối đa sau 8 phút bằng process tree + stack + log/source mtime.

### Điều kiện context hỏng và recovery owner thay thế

Nếu R5 với router HTTP 200 vẫn phát **bất kỳ blind sleep/self-watch nào**, hoặc
8 phút không có prompt/tool/source/log progress và stack lại chứng minh
sleep/terminal self-monitor, Codex coi đây là evidence đủ của context hỏng.

Khi đó Manager được phép:

1. capture transcript/process/stack evidence;
2. terminate exact R5 tree và xác minh owner cũ không còn active;
3. append `RECOVERY_REASON=CONTEXT_CORRUPT_DOUBLE_WATCHDOG` vào registry;
4. tạo đúng **một** replacement session cho cùng Task ID `S09-T04-C4`, model
   `custom/alpha`, reasoning max, fallback disabled, cùng write-set và worker
   directive ở trên;
5. ghi old owner -> replacement owner mapping; tuyệt đối không để hai owner sống
   đồng thời.

Replacement cũng không được subworker. Nếu replacement lặp cùng lỗi hoặc route A
không khả thi, dừng `S09-C4 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW` cho
Codex; không tạo replacement thứ hai.

## 6. Remaining DAG — không tự thay đổi

Start state chỉ có T04 recovery dependency-ready. Không có production slot nào
khác được mở song song vì T05B phụ thuộc T04 final và T06B phụ thuộc T05B final.

### J1-C4 sau T04 exit

Manager tự review disk/diff/ownership và chạy:

- T04 focused x2: 21/21 mỗi run;
- T03+T04 focused/adversarial x2, isolated basetemp;
- T05A render-context suite và T03 relevant suite ít nhất một fresh Manager run;
- Ruff/mypy scoped; freeze re-hash 13/13.

Nếu fail thuộc T03 hoặc T05A, route correction về đúng owner cũ
`20260824_031524_a6bb2a` hoặc `20260824_072626_645cde`; không cho T04 sửa file
của họ. Chỉ khi J1 xanh mới resume T05B.

### Wave B — T05B final

Resume exact owner `20260824_093602_af7c26`. Bind PREP hiện có với final T04 API:

- submit đúng selected/active loop, không entire completed list;
- không exact loop/base completed thì block rõ ràng;
- UI hiển thị backend-reported affected/regenerated/reused evidence;
- five-kind applied flow, conflict/retry/replay và accessibility giữ đúng C4;
- TSC, scoped ESLint, production build và T05B production-stack gate xanh.

Worker không sleep/self-monitor. Exit `TASK_SUBMITTED (S09-T05B-C4)`; Manager
review và append registry. Backend write-set read-only trong wave này.

### J2-C4 và T06B production final

Sau T05B exit và focused integration xanh, resume exact owner
`20260824_131423_423e42`. T06B chỉ viết allowlist trong original C4 prompt.

Production Chromium phải chạy x2 với fresh isolated DB/runtime mỗi lần, actual
`app.api.app` + production Next build/start, không route patch/mock. Bắt buộc
chứng minh:

1. UI chọn d4 và non-first stable layer;
2. requested/affected chính xác `[d4_group_occlusion]`;
3. d4 `regenerated=true`, artifact/hash đổi do real target-layer effect;
4. d1/d2/d3 `regenerated=false`, không `render_ms`, exact identity/hash/size/frame
   và không renderer invocation;
5. same three-part tuple replay same job; evidence difference tạo identity khác;
6. five kinds apply canonical effect hoặc fail closed trước job;
7. restart giữ generation/checkpoint evidence.

Finding production phải route về exact code owner rồi serialize reverify; T06B
không sửa shared production code.

## 7. Liveness không được tái phạm

- Heartbeat ít nhất mỗi 20 phút, nhưng phải nêu progress mới, log, blocker,
  action next và slot state.
- Không có progress 8 phút: audit ngay và **đưa ra quyết định**; không chỉ lặp
  `wc -c`.
- Cấm worker tự sleep/self-monitor. Manager chỉ được `sleep 300` sau confirmed
  transient connection failure theo rules; sau đó phải audit và resume thật.
- Probe khỏe + process sleep/no progress là liveness defect, không phải
  `RUNNING_RETRY_WAIT`.
- Manager phải tiếp tục `monitor -> review -> correction/resume -> verify ->
  report` tới terminal được cấp quyền.

## 8. Final Manager gate và terminal

Sau tất cả owner exit và writers quiescent, chạy đầy đủ original C4 §7:

- freeze v4 manifest + 13/13, I03/I05 SHA exact;
- resolve và chạy toàn bộ current `tests/test_s09*.py` isolated, zero fail/error;
- T03/T04/T05 focused/adversarial repeat + UTF8 slice;
- Manager DB assertion affected d4 only và regenerated flags thật;
- Chromium C4 x2, inspect E2E JSON và DB attempt trực tiếp;
- long-path >=260, timebase/fps retained;
- Ruff, mypy no-incremental, Alembic one head, materialized OpenAPI, TSC,
  S09-scoped ESLint, production build, diff/whitespace checks;
- write-set/attribution, process/ports/temp/protected-data audit;
- append reconciled final state table, exact commands/counts/hashes/retries.

Nếu bất kỳ P0/P1, affected scope/layer, five-kind effect, fingerprint,
cross-workspace refusal, cancellation residue, generation evidence hoặc required
gate fail/unknown:

`S09-C4 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Chỉ khi toàn bộ pass:

`S09-C4 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Sau đó STOP và giao packet cho Codex review độc lập. Không APPROVED/CLOSED,
không push GitHub và không mở sprint khác.

## 9. Start command

Bắt đầu ngay sau `RULES_LOADED`: đọc required files đầy đủ -> xác minh Manager cũ
đã dừng -> preflight/quiescence/freeze -> audit và phá đúng double-watchdog T04
-> resume R5 exact owner -> hoàn tất remaining DAG theo thứ tự. Không chỉ trả kế
hoạch và không phát thêm blind sleep.
