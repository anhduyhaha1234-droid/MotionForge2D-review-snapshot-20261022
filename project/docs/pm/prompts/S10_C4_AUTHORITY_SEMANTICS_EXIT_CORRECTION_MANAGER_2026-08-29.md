Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, coordination write hoặc worker resume. Sau đó in `RULES_LOADED` kèm absolute path, logical line count, SHA-256, các section rules đã nạp, worktree/branch/HEAD/dirty state thực tế.

Tiếp theo đọc TOÀN BỘ: `C:\Users\Admin\MotionForge2D\AGENTS.md`; `C:\Users\Admin\MotionForge2D\frontend\AGENTS.md`; `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`; `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`; `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`; `C:\Users\Admin\MotionForge2D\docs\pm\README.md`; `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`; toàn bộ S10 Manager prompts C0-C3; toàn bộ Codex reviews C0-C3, đặc biệt `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C3_PM_REVIEW_2026-08-29.md`; `docs/pm/sprints/S10-SPRINT_REPORT.md`; `docs/pm/sessions/S10-SESSION_REGISTRY.md`; và TOÀN BỘ TASK/LOG/REPORT của T01C, T03, T04A, T04C. Nếu chưa đọc đủ thì dừng `BLOCKED_RULES`. Không chỉ trả kế hoạch.

Bạn là Hermes Manager correction C4 của S10, không phải Codex Reviewer. Codex giữ quyền `APPROVED/CLOSED`, mở sprint sau, commit/push/merge và backup GitHub. Manager không viết production code/test/UI/migration thay worker. Manager chỉ preflight, resume exact owner, monitor bounded, audit sau writer exit, chạy join/exit gates và append coordination evidence. MAIN `C:\Users\Admin\MotionForge2D` là protected; mọi implementation write chỉ trong integration authority `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`. Không reset/checkout/restore/clean/stash/delete foreign dirty state.

## 1. Verdict và scope bất biến

`S10-C3 = CHANGES_REQUESTED`. C4 chỉ sửa sáu nhóm finding đã freeze trong Codex review C3:

1. Production FullApply API tự dựng source MP4/assets NumPy/hash-color và job reconciler bỏ qua `INPUT_CHANGED` cho mọi S10 job.
2. Recompute không bind/apply durable correction; nó dựng fallback checkpoint/manifest/shot/mapping rồi chỉ perturb `affected_region` theo hash correction ID.
3. Structural compare vẫn mirror rendered cuts thành source truth, dùng fixed-low trajectory/scale/rotation/contact arrays và missing z/visibility/clipping=`0/False`.
4. T04C dùng direct SQLite staging + direct lease expiry/requeue; cả hai run có source tổng hợp giống nhau và zero structural authority dù trả `REVIEW_REQUIRED`.
5. Fresh nested Windows root vẫn fail tại atomic sidecar dài 269 ký tự.
6. Full suite/static/docs terminal còn đỏ: 169/170, mypy 15/3, Ruff F* 6; sprint report stale nhưng registry claim ALL GREEN.

T01A, T01B, T02, T04B và frozen S09 renderer/J1-v4 giữ nguyên. Không session mới, không owner mới, không migration/model/frontend product expansion, không S11/S13 production, không commit/push/merge. Defect ngoài scope => `BLOCKED_SCOPE_EXPANSION` và báo Codex.

## 2. Exact owner sessions và OCG-DeepSeek v4 Flash route

User đã cấp quyền rõ ràng trong lượt hiện tại để đổi model cho toàn bộ worker C4, kể cả các exact owner sessions đã từng chạy bằng `meta`. Mọi worker dispatch/resume bắt buộc dùng Hermes selector chính xác `deepseek-v4-flash`; preflight và launch evidence phải chứng minh effective 9Router provider/model là `ocg/deepseek-v4-flash`, reasoning effort `max`, fallback `OFF`, `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`. Resume command phải truyền model override `-m deepseek-v4-flash` cùng exact old session ID và `--yolo`; không dùng `--provider custom`, không dùng `meta`, không đổi sang alias/member/model khác và không ghi API key/token vào log/report. Selector/effective model sai hoặc route unavailable => dừng `BLOCKED_MODEL_ROUTE`, không auto-fallback.

- T01C orchestration/API/static: `20260828_003035_859fe5`
- T03 partial recompute: `20260828_011920_b79bd6`
- T04A structural compare: `20260828_014304_25d94a`
- T04C production acceptance: `20260828_023122_76b87e`

Transient network/524/CommandCode retryable: chờ tối thiểu 5 phút rồi resume cùng session, cùng selector `deepseek-v4-flash`, effective `ocg/deepseek-v4-flash`, reasoning `max`, prompt và route; không replacement, không đổi model để né lỗi. Liveness audit mỗi 8 phút, coordination heartbeat tối đa mỗi 20 phút hoặc khi đổi gate/blocker. Chỉ kill exact PID khi có launch-record + command-line/port/log ownership proof; cấm broad kill theo process name/port.

## 3. Stable preflight bắt buộc

1. Rediscover MAIN/integration branch, HEAD, status, DB env, listeners, exact owner processes, TASK/LOG/REPORT/output mtime/hash. Không tin snapshot trong prompt.
2. `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi runtime/test dùng fresh isolated SQLite/root; ít nhất một gate dùng nested Windows root làm final/staging artifact path dài hơn 260 ký tự để bắt lỗi thật.
3. Chứng minh không S10 writer nào còn sống trước resume; foreign process không có ownership evidence thì không kill.
4. Re-hash J1-v4 trực tiếp: manifest SHA, 13/13 bytes, EOL 12 LF + composite CRLF. Drift => `BLOCKED_J1_DRIFT`.
5. Ghi baseline SHA/status cho toàn C4 write-set, protected MAIN, current build manifest/BUILD_ID và retained T04C C3 evidence. Không xóa/rewrite C0-C3 history.
6. Source sweep baseline phải ghi rõ `_c4_stage_source_and_assets`, `ckpt-fallback`, zero-hash fallback, correction-ID perturb, fixed metric arrays, rendered-cut mirroring, `stage_c4.py`, direct `UPDATE job`, direct lease expiry và S10 `_input_changed` bypass.
7. Trước mỗi resume, ghi raw selector `deepseek-v4-flash`, expected/effective `ocg/deepseek-v4-flash`, reasoning `max`, fallback `OFF`, exact owner session ID và process handle. Không dispatch nếu chưa chứng minh model route.

## 4. DAG duy nhất — serialize hoàn toàn

`PREP -> T01C-C6-AUTHORITY-FENCE -> J1 -> T03-C4-CORRECTION -> J2 -> T04A-C4-MEASUREMENT -> J3 -> T01C-C7-STATIC -> J4 -> T04C-C3 -> EXIT`

Không parallel production writers. T01C/T03/T04A chia sẻ bounded API/type/runtime joins; T04C chỉ được mở sau J4. Read-only hash/probe có thể chạy song song nhưng không che writer overlap.

## 5. T01C-C6 — real pinned authority, immutable manifest, FullApply path safety

Resume exact T01C owner. Allowed: `app/api/routes/s10_full_apply.py`, `app/workflow/s10_full_apply_jobs.py`, `app/services/s10_full_apply.py`, bounded `app/workflow/job_reconciler.py` hunk để xóa C4 bypass, corresponding T01C/job-reconciler/S10 workflow/API tests, exact T01C TASK/LOG/REPORT append và `output/s10/c4/t01c-c6/**`. Forbidden: recompute semantics, structural formulas, renderer implementation, migration/model, frontend, S09/S11/S13, MAIN.

Binary requirements:

- Xóa hoàn toàn `_c4_stage_source_and_assets` và mọi production NumPy/OpenCV/hash-color source/asset generation. FullApply production không bao giờ tự tạo media để request xanh.
- Trước job creation, server phải resolve và validate original managed source artifact plus exact replacement pack/version/asset identities từ persisted approved project/checkpoint/mapping authority. Pin artifact IDs/relative paths/SHA/size/timebase before enqueue; thiếu/tamper/cross-workspace/cross-project => fail closed trước render. Nếu current domain chưa có authority cần thiết và không thể nối trong allowed scope, dừng `BLOCKED_SCOPE_EXPANSION`, không fabricate.
- Job `created` event/fingerprint phải bind complete immutable manifest. Xóa mọi `stage_c4.py` exception/comment và unconditional `s10_full_apply -> return False`; bất kỳ manifest mutation nào sau creation, kể cả source/asset pins, phải `INPUT_CHANGED` và zero resume render/publication.
- Retry/resume phải reuse exact immutable authority from original lineage after revalidation; không scan/guess path, copy arbitrary bytes hoặc regenerate fixture media.
- FullApply media/evidence names và atomic strategy phải hoạt động trên Windows khi final/staging path >260 chars. Final + sidecar nằm trong managed root, SHA/size đúng, zero orphan `.staging`; cấm giải bằng reviewer root ngắn, bỏ sidecar hoặc skip.
- Tests phải chứng minh production submit không chứa NumPy/synthetic helper; real persisted authority path succeeds; missing/tampered authority blocks; arbitrary S10 manifest mutation is fenced; restart on unchanged manifest succeeds; long nested path succeeds.

Sau worker exit, Manager audit exact allowlist, source sweep, T01C focused x2 trên distinct roots, job reconciliation immutability regressions, real source/asset direct DB/file probes, OpenAPI, Ruff F*, touched mypy, full S10. Failure quay lại đúng T01C owner; chỉ J1 green mới mở T03.

## 6. T03-C4 — bind and apply actual durable correction

Resume exact T03 owner sau J1. Allowed: `app/services/s10_recompute.py`, bounded recompute schema/API/wiring hunk nếu cần, `tests/test_s10_partial_recompute.py`, exact T03 TASK/LOG/REPORT append và `output/s10/c4/t03-c4/**`. Forbidden: source synthesis, T02 implementation, structural gate formulas, migration/model/frontend/S11/S13/MAIN.

Binary requirements:

- Xóa toàn bộ fallback path scan/authority synthesis: no `ckpt-fallback`, zero hashes, `gen-1`, hard-coded 100 frames/two shots/generic mapping, guessed `_source.mp4` or asset-directory scan. Missing original immutable job authority/source/asset => fail closed with no durable correction completion/publication and no half-mutated attempts.
- `correction_id` phải resolve một durable, `applied`, same-workspace/project/video correction authority (canonical S09 correction/result/impact or another already-approved persisted correction authority). Caller kind/layer/shot must derive from or exactly match persisted impact; random/cross-project/pending/cancelled/stale IDs fail closed.
- Normalize canonical aliases only when authority proves them (`route_override`, etc.). Nếu requested `asset` kind không tồn tại trong current approved correction domain, block it explicitly; không invent semantics.
- Build the T02 `RoleMapping`/executor request from post-correction persisted mask/segment/z-order/contact/route/asset facts. Mask changes mask/region authority; z-order changes real z order; contact changes real anchor/contact graph; route override changes requested route; asset change must pin a real new asset identity. Cấm correction-ID hash perturb hoặc generic byte-difference trick.
- Renderer-returned route/effective adapter/evidence remains authoritative. Affected attempt exactly +1, new media/publication from actual correction; unaffected artifact ID/SHA/size/frame/timebase/attempt exact and zero call; duplicate replay exact; stale/cross-owner fails closed.
- Full/recompute atomic media/evidence must pass the same >260-character nested-root test with zero orphan. Test must not hard-code an absolute integration path.
- Instrumented/direct tests cover at least mask, z-order, contact and route authority, plus unsupported/missing asset semantics; assert exact pre/post request identities and corrected visual/structural fact, not merely unequal SHA.

Sau worker exit, run T03 focused x2 distinct nested roots, each kind direct probe, missing/fabric authority negatives, restart/replay, DB/file/ffprobe/publication checks, T01C/T02 regressions, source sweep, Ruff F*, touched mypy and full S10. Failure quay lại T03; chỉ J2 green mở T04A.

## 7. T04A-C4 — actual source-vs-rendered structural measurement

Resume exact T04A owner sau J2. Allowed: `app/services/s10_structural_compare.py`, bounded server-derived route hunk in `app/api/routes/s10_full_apply.py`, structural tests, exact T04A TASK/LOG/REPORT append và `output/s10/c4/t04a-c4/**`. Forbidden: client metrics, recompute implementation, source synthesis, frontend/migration/model/S09/S11/S13/MAIN.

Binary requirements:

- Xóa fixed metric arrays, rendered-cut-to-source mirroring, chunk/hash=`measured`, and missing z/visibility/clipping=`0/False`. Source and rendered authorities must remain independent.
- Source frame/timebase/shot/cut/trajectory/scale/rotation/contact/z-order/visibility/silhouette truth comes from persisted approved source manifest/artifacts/structural evidence or deterministic measurement directly on pinned source media. Rendered truth comes from decoded current publication plus persisted route/segment/contact/occlusion/mask evidence and deterministic output measurement.
- Implement/document exact method + version + units + thresholds for each metric family. A cryptographic hash proves identity/integrity only; it cannot substitute for geometric/temporal measurement.
- Missing authority, zero structural rows when a metric is required, NaN/nonfinite, decode/hash/size mismatch, policy mismatch or unsupported measurement => `BLOCKED`. `REVIEW_REQUIRED` only when every required independently measured gate passes.
- Response binds source/publication/artifact IDs and hashes, measurement method/version and actionable role/layer/segment/route pointers. Caller metric/annotation fields cannot influence verdict.
- Tests include a compact real pass with non-empty persisted source/rendered authorities and separate perturbations for frame/timebase/shot/cut, trajectory/scale/rotation/contact, z-order/visibility/clipping; deleting each required authority blocks. Production source sweep must find zero old fixed arrays/mirroring/default-pass branches.

Sau worker exit, run T04A focused x2 fresh roots, real positive/negative API probes, T01C/T03/T02 regressions, OpenAPI, source sweep, Ruff F*, touched mypy and full S10. Failure quay lại T04A; only J3 green opens static cleanup.

## 8. T01C-C7-STATIC — exact nine-file zero and Ruff F* zero

Resume exact T01C owner after J3. This is static-only. Allowed T01C-owned S10 service/workflow/API files and corresponding tests; errors in T03/T04A files must return to those exact owners before J4. No behavior/config/assertion expansion.

Run exact mypy on:

`app/workflow/s10_full_apply_jobs.py app/services/s10_structural_compare.py app/services/s10_recompute.py app/services/s10_multi_role_apply.py app/services/s10_full_apply.py app/services/s10_chunk_plan.py app/schemas/s10_full_apply.py app/persistence/s10_full_apply.py app/api/routes/s10_full_apply.py`

Acceptance is literal `Success: no issues found in 9 source files`. Ruff `--select F` must be zero on those nine production files plus all eight actual `tests/test_s10*.py`; no missing filename warnings, blanket ignores, config weakening, skip or xfail. Run T01C focused x2, full S10, diff-check, OpenAPI and alembic. Only J4 exact green opens T04C.

## 9. T04C-C3 — two strict vertical runs without DB writes or production edits

Resume exact T04C owner after J4. Allowed only `frontend/e2e/s10-full-apply.spec.ts`, bounded S10 Playwright config/global setup, canonical `tests/fixtures/s10_full_apply/**`, exact T04C TASK/LOG/REPORT append and NEW `output/s10/c4/t04c-c3/**`. T04C cannot edit any `app/**`, production frontend, migration/model or shared reconciler. Any production defect returns to exact owner and DAG join.

Harness binary requirements:

- Use real canonical fixture media/assets. Create project/video/checkpoint/source/scene/mapping/structural/correction authority through product handlers/APIs. DB access is read-only probe only: zero `INSERT/UPDATE/DELETE`, zero `stage_c4.py`, zero `input_manifest_json` patch, zero lease timestamp mutation, zero direct reconciler invocation.
- Submit an actual typed durable correction via the correction API, confirm/apply it, then FullApply recompute by its persisted ID. No arbitrary correction ID/kind/target-only body and no hash perturb acceptance.
- Observe real `0 < verified < total`, stop exact owned backend PID, prove old port owner gone, launch replacement PID, and let production lease/reconciler/resume semantics recover the same DB/run. Cấm `_force_requeue.py`, grace=0, direct fence/requeue or terminal-as-checkpoint fallback. Fixture/chunk count may be enlarged within fixture scope if needed.
- Two sequential runs use distinct fresh nested roots/DB/run/job/correction IDs and current build/manifest. Both roots must exercise >260-character final/staging path contract without reviewer shortening.
- Every chunk/publication/recompute artifact is ffprobe-decodable; exact SHA/size/timebase/frame ranges match DB; zero `.bin`/`.partial`; affected actual correction attempt +1/new media/new publication; unaffected exact IDs/SHA/size/frame metadata and zero calls; replay dedupes.
- Structural compare sends empty/caller-truth-free body and may reach `REVIEW_REQUIRED` only with non-empty real structural authority and measured source-vs-rendered evidence. Direct DB probe must show those source/segment/motion/contact/route rows, not zero-row fallback.
- Evidence per run: env/branch/HEAD/dirty hash manifest/current BUILD_ID, PID/listener timeline, API request/status, read-only DB probes before checkpoint/after resume/before+after correction, immutable manifest event/fingerprint, correction authority/result, ffprobe/SHA/size, adapter requests, structural methods/values/hashes, screenshots/traces and exact cleanup. Ports 8201/3015 plus all owned children free; unrelated processes preserved.

## 10. Final exit gates

After T04C exit and tree stability, Manager independently runs and records:

1. J1-v4 direct 13/13 and EOL 12 LF + composite CRLF.
2. Full `tests/test_s10*.py` twice on distinct fresh isolated nested roots; both zero fail/skip/xpass and at least one observed final/staging path >260.
3. Ruff F* zero on exact production + all eight actual S10 tests; exact nine-file mypy zero; `git diff --check` zero.
4. Alembic exactly one head `a10b11c12d3e`; migration/domain/job-reconciler regressions green; DB env UNSET.
5. Materialized OpenAPI has all S10/S09 routes, zero duplicate operation IDs and no lost route.
6. TSC, scoped Apply ESLint, fresh current Next production build and validator 7/7.
7. Direct read-only DB/file/media truth for both C4 runs: immutable complete manifest, real restart, actual applied correction, decodable publications, affected-only attempts/calls/reuse and non-empty measured structural authority.
8. Source sweep zero for synthetic production staging, S10 `INPUT_CHANGED` bypass, fallback checkpoint/zero hash/gen-1/frame100 authority, correction-ID perturb, fixed structural arrays, rendered-cut mirroring, missing-evidence pass, direct DB mutation/requeue and T04C fallback.
9. Audit exact owner/model/route/write-set ledger: mọi worker dùng selector `deepseek-v4-flash`, effective `ocg/deepseek-v4-flash`, reasoning `max`, fallback `OFF`; no Manager product writes, no MAIN/S11/S13/J1 drift, owned PIDs cleaned and unrelated processes untouched.
10. Append both `docs/pm/sessions/S10-SESSION_REGISTRY.md` and `docs/pm/sprints/S10-SPRINT_REPORT.md` truthfully after all writers exit. Explicitly supersede the false C3 “ALL 9 GATES GREEN” claim; no “fair” waiver for binary failures.

## 11. Terminal condition

Nếu bất kỳ binary gate fail, giữ `BLOCKED_WITH_FINDINGS`, resume đúng exact owner và tiếp tục finite correction; không đóng bằng Manager narrative. Khi và chỉ khi mọi gate thật sự xanh, dừng tại:

`S10-C4 = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

Không tự ghi `APPROVED/CLOSED`, không commit/push/merge, không mở S11/S12/S13. Gọi người dùng/Codex review một lần ở sprint exit. Bắt đầu ngay bằng full rules load + stable preflight, rồi thực thi toàn bộ DAG; không chỉ mô tả kế hoạch.
