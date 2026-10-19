# HERMES PROMPT — S11-C1 Full-Scope Readiness + Executable Restart Closure

Bạn là Hermes Manager cho correction sprint hữu hạn `S11-C1` của
MotionForge2D. Bắt đầu thực thi ngay; đây không phải yêu cầu chỉ lập kế hoạch.

## 0. Lệnh bắt buộc đầu tiên

Đọc TOÀN BỘ, không đọc lướt và không chỉ dựa vào chat summary:

1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
2. `C:\Users\Admin\MotionForge2D\AGENTS.md`
3. `C:\Users\Admin\MotionForge2D\frontend\AGENTS.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_T02_T06_PM_REVIEW_2026-09-04.md`
8. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S11_T02_T06_FULL_SPRINT_MANAGER_2026-09-03.md`
9. `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s11-post-t01-readiness\r1\synthesis\S11_T02_T06_PRODUCTION_PLAN.md`
10. `C:\Users\Admin\MotionForge2D-evidence\s11-production\manager\exit\NEXT_REVIEW_PACKET.md`
11. Mọi LOG/REPORT/evidence hiện hữu của T03A, T03G, T04B, T05A, T06C và
    S11-INT01 trước khi resume owner tương ứng.

Rules canonical thắng nếu bất kỳ chỉ dẫn cũ nào xung đột. Phải ghi SHA-256 và
số dòng của rules, review, prompt này và production plan vào registry mới.

## 1. Quyền thực thi và trạng thái vào vòng

`AUTHORIZED_TO_DISPATCH` cho đúng correction sprint này.

- Verdict vào vòng:
  `S11-T02..T06 = CHANGES_REQUESTED / NOT_APPROVED / S11_NOT_CLOSED`.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Canonical branch: `codex/s11-integration`.
- Reviewed local/remote HEAD bắt buộc:
  `4d7ad8196c3f7a21af744906ef4174690159d889`.
- Activation base của full sprint:
  `7751598214eedb6b72e3783e39a2a408721abe40`.
- Không mở S12 hoặc S13 trong vòng này.
- Không tự tuyên bố `APPROVED` hay `SPRINT_CLOSED`. Trạng thái terminal duy nhất
  khi mọi gate xanh là
  `S11-C1 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`.

Mở MỘT Manager session mới, compact, không resume Manager full-sprint cũ. Manager
chỉ điều phối, kiểm chứng, ghi registry/evidence và dispatch; Manager không sửa
production code hoặc test thay worker.

## 2. Model route bắt buộc cho vòng mới

Mọi turn được dispatch/resume bởi prompt này, gồm implementation owners,
evidence owner và `S11-INT01`, dùng chính xác:

- provider/route: custom 9Router hiện có;
- model: `ocgfree/muse-spark-1.3-contributor-free`;
- requested reasoning: `max`;
- fallback: `OFF`;
- TTFB timeout: `900` giây.

Đây là override model theo chỉ thị mới nhất của user nhưng KHÔNG thay đổi durable
task/session ownership. Nếu route/model không khả dụng, ghi raw lỗi, chờ tối
thiểu 5 phút rồi retry đúng session một lần. Vẫn lỗi thì dừng
`BLOCKED_MODEL_ROUTE`; không đổi model, không fallback và không tạo owner mới.

## 3. Preflight bắt buộc trước dispatch

Manager phải tự kiểm tra và lưu raw evidence:

1. `git status --porcelain=v1 --untracked-files=all` canonical bằng rỗng.
2. Local HEAD đúng reviewed HEAD; `git ls-remote origin
   refs/heads/codex/s11-integration` bằng đúng local HEAD.
3. Không có implementation writer, pytest, product app hoặc ffmpeg của S11 đang
   chạy. Không kết luận chỉ từ một tín hiệu; dùng quy tắc exact-owner trong rules.
4. Không đặt hoặc dùng production DB. Unset mọi biến DB override trước test; mọi
   probe dùng DB/temp root mới, cô lập.
5. Chụp hash/size/line-count cho các file critical trước sửa:
   - `app/persistence/qc_check_runs.py`
   - `app/persistence/readiness.py`
   - `app/workflow/qc_checks_handler.py`
   - `app/services/qc_correction_bridge.py`
   - `tests/test_s11_t03g_qc_check_job.py`
   - `tests/test_s11_t03g_qc_check_api.py`
   - `tests/test_s11_t05a_readiness_api.py`
   - `tests/test_s11_t02_t06_acceptance.py`
   - `docs/pm/sessions/S11-T03A/evidence/provenance_audit.txt`
6. Kiểm tra các task worktree sạch và branch đúng. Trước sửa, mỗi exact owner
   phải đưa branch của mình lên canonical base hiện hành bằng fast-forward-only;
   drift hoặc không ff được thì dừng owner đó và báo Manager, không reset/rebase.
7. Tạo run-id mới dưới
   `C:\Users\Admin\MotionForge2D-evidence\s11-c1\` cho registry, prompt snapshots,
   raw commands và gate outputs. Không ghi artifact runtime vào source tree.

Preflight lệch ở mục 1-3 hoặc remote drift => dừng trước mọi write với trạng thái
blocker chính xác. Không tự chữa Git state ngoài quyền prompt.

## 4. Kỷ luật session và context

Correction phải resume exact task owner; không tạo implementation owner mới:

| Task | Exact session | Worktree | Branch |
|---|---|---|---|
| S11-T03A | `20260903_130858_8ca677` | `C:\Users\Admin\MotionForge2D-worktrees\s11-t03a-0903w5` | `codex/s11/t03a-0903w5` |
| S11-T03G | `20260903_170546_0d42f6` | `C:\Users\Admin\MotionForge2D-worktrees\s11-t03g-0903w8` | `codex/s11/t03g-0903w8` |
| S11-T04B, conditional only | `20260903_183246_706d31` | `C:\Users\Admin\MotionForge2D-worktrees\s11-t04b-0903w10` | `codex/s11/t04b-0903w10` |
| S11-T05A | `20260903_203404_4a4548` | `C:\Users\Admin\MotionForge2D-worktrees\s11-t05a-0903w12` | `codex/s11/t05a-0903w12` |
| S11-T06C | `20260903_223530_b90853` | `C:\Users\Admin\MotionForge2D-worktrees\s11-t06c-0903w14` | `codex/s11/t06c-0903w14` |
| S11-INT01 | `20260903_112116_35051c` | canonical | `codex/s11-integration` transport role |

Trước nội dung sửa, gửi cho mỗi owner một compact handoff chứa: finding chính
xác, current canonical SHA, allowlist, forbidden files, acceptance matrix, lệnh
test và terminal condition. High message/token count một mình không đủ quyền
transfer owner.

Nếu cùng exact owner hai bounded resume liên tiếp không tạo usable progress,
lặp lại scope cũ, mất contract, hoặc thực hiện write không an toàn, dừng
`BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED` và chờ Codex. Không tự tạo
replacement owner, không rebuild từ memory, không overwrite nguyên file test.

Mọi sửa file đã tồn tại phải dùng patch hẹp. Cấm `write_file`/whole-file
overwrite, copy-restore, generated rewrite hoặc script ghi đè đối với source,
tests và evidence hiện hữu. Trước/sau mỗi turn, Manager kiểm tra diff, size và
hash để phát hiện destructive write.

## 5. Wave C1 — chạy tối đa ba lane song song

Chỉ dispatch sau preflight xanh. Ba lane có workset tách biệt và được chạy song
song thật.

### Lane C1-A — T03G: full-run authority, fail-closed completion

Resume exact S11-T03G owner. Allowed write set:

- `app/persistence/qc_check_runs.py`
- `app/workflow/qc_checks_handler.py`
- `tests/test_s11_t03g_qc_check_job.py`
- `tests/test_s11_t03g_qc_check_api.py`
- `docs/pm/sessions/S11-T03G/**`
- evidence external của run-id mới.

Không sửa `readiness.py`, correction bridge, frontend hoặc T06C acceptance.

Yêu cầu hành vi:

1. Readiness authority phải chọn current matching FULL run, không chọn đơn giản
   newest `RUN_QC_CHECKS` bất kể scope.
2. `SCOPE_FULL` chỉ completed-current khi completion envelope khớp manifest,
   project/video/input fingerprint và chứng minh đủ mười detector chuẩn: tám
   visual + hai audio, `errors == 0`, `skipped == 0`.
3. Audio-only/visual-only/partial run không được thay thế full authority. Không
   cộng gộp tùy ý nhiều partial run thành full coverage.
4. Full run mới nhất queued/running/failed/stale/corrupt phải fail closed thay vì
   lùi về full run completed cũ.
5. Một audio-only run mới hơn full run completed không xóa full authority; nhưng
   QC item blocker mới mở vẫn được blocker query chặn.
6. Full current completed, đủ coverage, zero item vẫn là ready candidate.
7. Xóa trailing whitespace ở `app/workflow/qc_checks_handler.py:12` trong cùng
   patch hẹp; không refactor ngoài finding.

T03G phải thêm executable tests trên fresh DB cho tối thiểu matrix:

- audio-only completed, không full => `not_run`;
- full completed rồi audio-only completed => full authority được giữ;
- newest matching full queued/running/failed/stale => `not_run`;
- manifest/completion scope mismatch => fail closed;
- fingerprint mismatch => fail closed;
- full completion thiếu bất kỳ detector nào => fail closed;
- full completion có error/skipped => fail closed;
- full complete zero-item => ready candidate.

Không dùng mock để thay durable repository/DB authority cần chứng minh.

### Lane C1-B — T06C: executable restart/resume epic-exit proof

Resume exact S11-T06C owner. Allowed write set:

- `tests/test_s11_t02_t06_acceptance.py`
- `docs/pm/sessions/S11-T06C/**`
- external evidence của run-id mới.

Không sửa production code ở lane này.

Thay manifest-only/proxy proof bằng một scenario thực thi trên DB và managed root
mới. Scenario phải:

1. Seed project/video/QC blocker hợp lệ và submit correction/recompute qua stack
   thật tương ứng.
2. Dừng/recreate `JobService` hoặc worker/process boundary sau khi durable job đã
   tồn tại, dùng lại đúng DB + managed root.
3. Resume job persisted và chờ terminal state bằng bounded polling, không sleep
   vô hạn.
4. Chứng minh đúng một successor/effect; không duplicate correction resolution,
   không duplicate enqueue do restart.
5. Chứng minh rerun chỉ tạo artifact/phạm vi affected segment; ready scenes và
   phần timeline không liên quan không bị review/recompute lại.
6. Chứng minh trạng thái readiness cuối ổn định sau query lại từ repository mới.
7. Scenario D phải gọi executable assertion/node thật; không chỉ đọc golden JSON,
   tìm chuỗi hoặc tin vào số pass của file test khác.

Nếu executable test xanh với production code hiện tại, không dispatch T04B. Nếu
nó phát hiện lỗi product cụ thể trong correction bridge, T06C ghi minimal failing
reproducer, actual/expected và dừng lane ở `NEEDS_T04B_PRODUCT_FIX`; không tự sửa
production.

### Lane C1-C — T03A: diff-check provenance cleanup

Resume exact S11-T03A owner. Allowed write set:

- `docs/pm/sessions/S11-T03A/evidence/provenance_audit.txt`
- `docs/pm/sessions/S11-T03A/LOG.md`
- `docs/pm/sessions/S11-T03A/REPORT.md`
- external evidence của run-id mới.

Chỉ xóa trailing whitespace tại các dòng bị `git diff --check` báo. Ghi rõ đây
là formatting correction sau Codex review; không thay đổi nội dung provenance,
không sửa code/test và không tái tạo evidence.

### Exit từng lane C1

Mỗi owner:

- chạy focused tests trong allowlist;
- chạy `git diff --check` trên own diff;
- chứng minh không chạm forbidden files;
- commit local trên exact task branch, không push/merge/rebase/reset/stash/clean;
- trả SHA, raw test output, diff stat, before/after hash/size và terminal
  `TASK_SUBMITTED` hoặc blocker chính xác;
- sau đó dừng hoàn toàn.

Manager phải review độc lập từng diff/test/evidence. Chỉ owner đạt
`MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` mới được giao INT01.

## 6. Conditional Wave C1-D — chỉ khi T06C chứng minh product bug

Không dispatch mặc định. Nếu và chỉ nếu T06C có executable failing reproducer
cho production correction bridge, resume exact S11-T04B owner.

Allowed write set:

- `app/services/qc_correction_bridge.py`
- các test T04B hiện hữu trực tiếp chứng minh cùng defect;
- `docs/pm/sessions/S11-T04B/**`;
- external evidence run-id mới.

T04B sửa tối thiểu để restart/resume idempotent và affected-only. Sau T04B commit,
resume exact T06C owner để fast-forward-only tới canonical mới và chứng minh
executable acceptance xanh. Không transfer ownership giữa T04B và T06C.

## 7. Integration gate sau C1

Resume exact `S11-INT01`; role này chỉ làm Git transport và chạy lệnh gate được
Manager chỉ định. Trước mỗi merge:

- canonical porcelain phải rỗng;
- local HEAD phải bằng remote;
- task SHA phải đúng Manager-verified SHA;
- merge `--ff-only` khi có thể, nếu cần merge commit phải conflict-free;
- bất kỳ conflict nào => abort, không tự resolve, trả owner;
- push non-force chỉ sau combined micro gate xanh;
- verify remote SHA sau push.

Merge các lane C1 đã verified tuần tự. Sau merge, chạy combined matrix T03G và
T06C. Nếu T04B conditional tồn tại, merge nó và T06C follow-up theo đúng dependency
trước khi mở C2.

## 8. Wave C2 — T05A consumer/API regression, dependency-serial

Chỉ dispatch sau full-scope authority của T03G đã merge, push và combined gate
xanh. Resume exact S11-T05A owner; fast-forward-only branch/worktree tới canonical
HEAD mới.

Allowed write set:

- `app/persistence/readiness.py` chỉ khi consumer logic thực sự cần đổi;
- `tests/test_s11_t05a_readiness_api.py`;
- `docs/pm/sessions/S11-T05A/**`;
- external evidence run-id mới.

Không sửa lại T03G mechanism trừ khi trả finding về exact T03G owner.

T05A phải chứng minh qua API/project aggregate trên fresh real DB:

1. Chỉ có audio-only completed current => video/project `not_run`, không `ready`.
2. Full completed đủ mười detector + zero blocker => ready candidate.
3. Full completed + blocker mở => blocked.
4. Full completed rồi audio-only completed zero blocker => vẫn dùng full authority.
5. Full authority stale hoặc newest matching full failed/running => `not_run`.
6. Multi-video: chỉ một video thiếu full authority => project không ready.
7. Response/reason giữ deterministic, không rò absolute path và không làm hỏng
   contract hiện hữu.

Focused tests, diff-check, commit và stop theo cùng protocol C1. Manager review
độc lập rồi mới resume INT01 merge/push.

## 9. Gate ladder — fail fast, không chạy vòng rộng vô ích

Theo đúng thứ tự; gate nhỏ fail thì trả exact owner, không chạy broad gate:

1. Per-owner micro tests và matrix mới: 100% pass, 0 deselected nếu node list
   được yêu cầu chính xác.
2. Combined T03G + T05A + T06C focused tests.
3. Static affected scope: Ruff và mypy theo retained S11 command/allowlist.
4. `git diff --check 7751598214eedb6b72e3783e39a2a408721abe40..HEAD`
   phải exit 0.
5. Alembic: một head và fresh upgrade thành công trên temp DB.
6. OpenAPI duplicate-route check theo retained command, exit 0.
7. T06C one-command acceptance phải thực sự chạy executable restart case và
   exit 0.
8. Independent 20-file backend risk suite tương đương packet trước: tối thiểu
   giữ `314 passed`, không giảm collection hoặc bỏ node.
9. Retained S11-T01 original-audio suite: 64/64.
10. Retained S10 full-apply API suite: 71/71.
11. Frontend build/Playwright có thể RETAIN thay vì chạy lại chỉ khi Manager
    chứng minh toàn bộ frontend source, config và relevant backend API contract
    files không đổi hash từ reviewed HEAD. Nếu bất kỳ file đó đổi, chạy lại đúng
    build + Playwright gates của full-sprint prompt.
12. Canonical porcelain rỗng; local HEAD == remote HEAD sau final non-force push;
    zero writer, ports liên quan free, heartbeat removed.

Mọi test dùng fresh `--basetemp` có đường dẫn đủ ngắn và unique. Không tái sử dụng
cache/evidence cũ để thay execution. Không sửa test chỉ để khớp implementation;
matrix và binding acceptance là authority.

## 10. Evidence và báo cáo terminal

Manager phải tạo ít nhất:

- `C:\Users\Admin\MotionForge2D-evidence\s11-c1\manager\REGISTRY.md`
- per-lane prompt snapshot, session/model/branch/worktree/commit map;
- raw preflight, micro, focused, static, migration, OpenAPI, broad và Git outputs;
- `C:\Users\Admin\MotionForge2D-evidence\s11-c1\manager\exit\EXIT_VERDICT.md`
- `C:\Users\Admin\MotionForge2D-evidence\s11-c1\manager\exit\NEXT_REVIEW_PACKET.md`

Packet cuối phải nêu rõ:

1. Mỗi finding được sửa ở commit/file/test nào.
2. Actual model/provider/reasoning/fallback cho từng resumed turn; không chỉ ghi
   requested config.
3. Có hay không dispatch conditional T04B và bằng chứng quyết định.
4. Raw count mọi gate, return code, command, temp roots và timestamps.
5. Canonical local SHA, remote SHA, porcelain, process/port/heartbeat cleanup.
6. Retained evidence nào được dùng và hash proof cho phép retain.
7. Không còn P0/P1/P2 nào thuộc S11-C1 theo Manager review.
8. Trạng thái duy nhất khi xanh:
   `S11-C1 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`.

Nếu còn bất kỳ failure, overclaim, remote drift, destructive write, unresolved
conflict hoặc context-owner blocker, báo trạng thái blocker trung thực và dừng;
không tự đóng sprint.

Bắt đầu ngay bằng full-rule load, preflight và registry. Sau đó dispatch ba lane
C1-A/C1-B/C1-C song song nếu và chỉ nếu preflight xanh.
