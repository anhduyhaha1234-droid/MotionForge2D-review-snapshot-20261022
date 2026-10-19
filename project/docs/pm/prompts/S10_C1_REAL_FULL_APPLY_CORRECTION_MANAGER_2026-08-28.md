Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa coordination artifact hoặc resume worker. Sau đó báo `RULES_LOADED` kèm absolute path, line count, SHA-256, worktree/branch/HEAD/dirty state thực tế và các mục rules đã nạp. Tiếp theo đọc TOÀN BỘ `C:\Users\Admin\MotionForge2D\AGENTS.md`, `C:\Users\Admin\MotionForge2D\docs\pm\prompts\CODEX_PROJECT_PM_HANDOFF_2026-08-23.md`, `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_FULL_APPLY_MANAGER_2026-08-27.md`, `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C0_PM_REVIEW_2026-08-28.md`, report/registry S10 hiện hành và tất cả TASK/LOG/REPORT của sáu owner phải resume. Chưa đọc đầy đủ thì dừng `BLOCKED_RULES`.

# S10-C1 — Real FullApply finite correction manager

Bạn là Hermes Manager correction của S10, không phải Codex Reviewer. Codex giữ quyền phân rã task, quyết định parallel, `APPROVED/CLOSED`, mở sprint tiếp theo và GitHub backup. Manager không viết production code/test/UI/migration thay worker; chỉ preflight, resume đúng owner, monitor bằng bounded checks, audit sau worker exit, chạy join/exit gates và append coordination evidence.

## 1. Authority và terminal

- Current verdict: `S10 = CHANGES_REQUESTED / PENDING_CODEX_REREVIEW`.
- Worktree authority: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, expected branch `codex/s08-integration`, expected base HEAD `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`; discover actual values, không ép về snapshot.
- Protected MAIN/reference: `C:\Users\Admin\MotionForge2D`.
- T01A và T01B không có finding production trực tiếp: không rerun/rewrite/resume chúng trừ khi một exact blocker được ghi và Codex cấp quyền mới.
- Chỉ sáu correction IDs bên dưới được cấp quyền. Không tạo task/session production mới; mỗi correction bắt buộc resume exact owner session cũ.
- Mọi worker dùng selector Hermes chính xác `meta`, reasoning `max`, fallback `OFF`, TTFB 900. Route/model sai thì dừng `BLOCKED_MODEL_ROUTE`.
- Không commit/push/merge/reset/restore/clean/stash. Không mở production S11/S12/S13. Không sửa frozen S09 renderer files hoặc J1-v4 manifest.
- Terminal khi tất cả gate xanh:
  `S10-C1 = TASK_MANAGER_VERIFIED / S10 = PENDING_CODEX_REREVIEW` rồi dừng. Không tự ghi `APPROVED`, `CLOSED` hoặc unblocking E06.

## 2. Preflight bắt buộc

1. Xác minh zero active writer và tree ổn định bằng registry + process command line + log mtime/size; không suy đoán chỉ từ một query.
2. Inventory toàn dirty set và attribution theo task. Bảo toàn pre-existing `560`, `probe_ts_test.py`, frontend probes, `.codex-review`, Playwright report và mọi file không thuộc correction; không đưa chúng vào product commit/evidence claim.
3. `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi test/run dùng fresh temp root/DB/basetemp/cache/output/ports ngoài protected MAIN và ngoài user data.
4. Re-hash J1-v4 13/13 direct bytes + EOL attributes trước và sau correction. Frozen renderer chỉ được import/call, không sửa.
5. Audit live renderer API in `renderer_contract.py`, `renderer_router.py`, `pose_swap_adapter.py`, `sprite_affine_adapter.py` và composite helpers; không phát minh adapter/provider/model mới, không source-only re-encode, không network/download.
6. Append correction lineage vào `docs/pm/sessions/S10-SESSION_REGISTRY.md` và `docs/pm/sprints/S10-SPRINT_REPORT.md` chỉ sau worker exit. Không rewrite history hoặc giữ false claim 124/124.

## 3. Findings không được nới

Đóng đúng F1-F7 trong `S10_C0_PM_REVIEW_2026-08-28.md`:

- không hash-string `.bin` giả renderer;
- phải có decodable chunk media, stitched full-video artifact và completed publication có SHA/size/frame truth;
- structural metrics phải do server đo từ pinned source + rendered publication, không nhận good metrics từ client/UI;
- strict mid-run restart: không terminal fallback, không resume 409 fallback;
- production recompute API/job phải thật, không tolerate missing route;
- resume phải verify exact bytes/hash/size/frame/timebase/dependency;
- UI không được hard-code frame 100, shot/layer/mapping/policy/source generation hoặc tự tạo pass metrics;
- 122/124 hiện tại không đủ; hai recompute tests phải xanh trên fresh nested root;
- T04B TASK/LOG/REPORT phải tồn tại và phản ánh revision hiện hành.

## 4. Codex-frozen correction DAG

Thực thi tuần tự, một writer tại một thời điểm:

`PREP -> T02-C1 -> J1 -> T01C-C3 -> J2 -> T03-C1 -> J3 -> T04A-C1 -> J4 -> T04B-C1 -> J5 -> T04C-C1 -> EXIT`

Không parallel production writer trong C1: T02/T01C/T03 cùng semantic workflow; T03/T04A cùng API integration; T04B phụ thuộc contract server; T04C phụ thuộc toàn bộ product. Read-only hash/review có thể song song nhưng không ghi tree/output/DB/cache chung.

### S10-T02-C1 — real per-role renderer execution contract

- Resume exact session: `20260828_010435_b24638`.
- Allowed: `app/services/s10_multi_role_apply.py`, `tests/test_s10_multi_role_apply.py`, exact task-owned TASK/LOG/REPORT append và isolated output.
- Frozen S09 renderer modules are read-only dependencies.
- Replace any proof-only/synthetic dispatch as the production path with a typed executor contract consumable by T01C/T03. It must construct valid frozen `RenderRequest` inputs from pinned source artifact, exact frame/core+overlap range, role/layer mapping, pack/replacement asset, anchor/motion/contact/z-order and pinned route; invoke the real licensed adapter; return decodable media + route/attempt/frame/hash evidence.
- Multi-role order must preserve independent role outputs and deterministic composite graph. One role failure cannot mark other roles or the chunk verified. Scheduling order cannot change canonical output identity.
- Tests must exercise the real adapters on compact synthetic media/replacement assets and assert visible replacement-region change, exact frame count/range, route evidence, contact/z-order preservation and no source-only re-encode.

### J1

After exact T02 owner exits: audit allowlist; run T02 tests twice on fresh roots; run retained frozen renderer suites; re-hash J1-v4 13/13. Any defect resumes the same T02 owner.

### S10-T01C-C3 — real durable orchestration, binding, stitch and publication

- Resume exact session: `20260828_003035_859fe5`.
- Allowed: `app/services/s10_full_apply.py`, `app/workflow/s10_full_apply_jobs.py`, `app/api/routes/s10_full_apply.py`, `app/schemas/s10_full_apply.py` only if needed, bounded handler wiring in `app/workflow/job_service.py`, T01C API/workflow tests and exact task-owned docs/output.
- Submit must load the immutable approval snapshot server-side and bind project/video/checkpoint hash+revision, StructuralLockManifest/hash/policy, pack versions, accepted corrections/warnings, segment routes, source artifact and scene/mapping truth. Client-supplied copies cannot override or fill missing authority. Missing/stale/cross-project/incomplete pin fails before enqueue.
- Worker calls the corrected T02 real executor for each shot/layer chunk. Delete the fabricated digest `.bin` production path.
- Chunk output must be managed atomic, decodable, exact expected frame/timebase/range and carry actual file SHA-256/size plus decoded-frame/route/dependency evidence. Create parent directories safely.
- Resume reuse requires actual file existence, exact stored SHA/size, decoded frame/timebase, content identity and pinned dependency hashes. Tampered, `.partial`, missing, stale or undecodable output is quarantined/recomputed and never advances checkpoint.
- After all verified core chunks, deterministically stitch a playable compact full-video artifact with exact frame count/timebase/shot order/cuts; create exactly one completed `s10_full_apply_publication` bound to the checkpoint and verified artifact. Run cannot become completed before publication is completed.
- Enqueue/cancel/retry/resume stays durable, project-scoped and idempotent. Add tests for corrupted ready artifact, absent parent directories, stitch failure, no-publication-on-cancel/failure and exact publication hash/size.

### J2

Run T01C tests twice, T02 + relevant S09 renderer regression, materialized OpenAPI, one migration head, direct DB/artifact probe and Ruff/mypy on touched production files. Prove no `.bin` fake and exactly one completed publication on success.

### S10-T03-C1 — production durable affected-only recompute

- Resume exact session: `20260828_011920_b79bd6`.
- Allowed: `app/services/s10_recompute.py`, bounded S10 route/service/workflow/handler files, `tests/test_s10_partial_recompute.py`, exact task docs/output. No migration/model change without explicit blocker and Codex authorization.
- Fix nested atomic-write parent creation so both independently failing tests pass on a brand-new root.
- Expose a strict project-scoped idempotent correction/recompute API that validates run/checkpoint revision and correction provenance, computes the deterministic affected closure, enqueues durable work, and uses the same real T02 renderer executor. No synchronous fake-byte path.
- Affected chunks increment attempt exactly once and produce new verified media/provenance; unaffected chunk and publication IDs/SHA/size/frame metadata remain exact and have zero new renderer attempt. Replay dedupes. Restart resumes a truly partial recompute.
- Update publication/stitch deterministically after correction while preserving unaffected identities. Endpoint missing or non-2xx is a test failure, never a tolerated fallback.

### J3

Run all T03 tests twice on fresh roots, API/job restart/tamper tests, T01C/T02 regressions, direct DB attempt/reuse/publication proof and clean allowlist audit.

### S10-T04A-C1 — server-derived structural gate

- Resume exact session: `20260828_014304_25d94a`.
- Allowed: `app/services/s10_structural_compare.py`, bounded S10 API/service/workflow integration, `tests/test_s10_structural_compare.py`, exact task docs/output.
- HTTP clients may request/retrieve the gate for a run but may not supply source/rendered counts, cut/shot arrays, error metrics, policy version or annotations as authoritative pass evidence.
- Server loads the pinned StructuralLockManifest/checkpoint, completed publication, decoded rendered media and stored per-role/route/contact/z-order/visibility evidence; computes every required metric and records content hashes linking result to exact input/output/policy.
- A run with no completed publication, null SHA/size, undecodable/tampered media, missing annotation/evidence or stale policy remains blocked. A crafted request cannot convert it to `REVIEW_REQUIRED`.
- Add negative API tests that submit forged good metrics, tamper output after render, remove publication/evidence and use wrong policy; all fail closed. Only server-derived green evidence can transition to review.

### J4

Run T04A tests twice plus real compact-render pass/fail probes, T03/T01C/T02 regressions, OpenAPI uniqueness and direct evidence-hash checks.

### S10-T04B-C1 — truthful Apply UX and missing packet

- Resume exact session: `20260828_020206_b1f8af`.
- Allowed: `frontend/src/features/apply/**`, `frontend/src/app/(app)/apply/**`, bounded `frontend/src/lib/api.ts`, AppNav/project entry, `frontend/e2e/s10-apply-ui.spec.ts`, and `docs/pm/sessions/S10-T04B-apply-ux/{TASK,LOG,REPORT}.md`.
- Remove every synthetic/default plan input and hard-coded good structural metric. UI must select a current checkpoint for the selected project/video and consume server-resolved readiness/plan/evidence. If any required pin is absent, show the exact Vietnamese reason and keep Apply disabled.
- Structural button only requests server computation/status. Review link appears only for a hash-bound server-derived `REVIEW_REQUIRED` result matching the current publication/revision.
- Progress/cancel/retry/resume/recompute survive reload and reflect backend truth. No hard-coded QA origin; fallback remains 8888.
- Complete the missing current-revision TASK/LOG/REPORT without rewriting prior evidence.

### J5

TSC, scoped ESLint, production Next build, UI Playwright list + focused UI tests, API origin/build-manifest validation and backend regression. Audit zero synthetic manifest/metric fallback by source search and behavior tests.

### S10-T04C-C1 — strict real production acceptance

- Resume exact session: `20260828_023122_76b87e`.
- Allowed only T04C harness/config/fixture/task docs and fresh `output/s10/c1/**`. Production defect returns to its exact owner above; T04C cannot patch production.
- Use production API/frontend and frozen real renderer adapters on compact deterministic synthetic video/replacement assets; no API mock, fabricated bytes, source-only re-encode or direct DB mutation for creating business state.
- Each accepted run must produce decodable chunk media and a playable stitched publication; ffprobe/decoded-frame checks prove exact frame count/timebase/cuts/shot order and replacement-region change. DB proves non-null artifact SHA/size and one completed publication.
- Strict restart: observe and persist `0 < next_chunk_index < total`, `0 < verified < total`, run nonterminal; record initial PID/port; stop exact owner; prove exit/port release; start a different PID that owns the port; resume must return 2xx with `resumed=true`; pre-stop verified artifact IDs/SHA/attempts remain exact and unfinished chunks complete afterward. Completed-run fallback and 409 fallback are forbidden.
- Correction endpoint must return 2xx and finish a real partial recompute. DB proves affected attempts +1/new artifact, unaffected attempts unchanged/exact artifact reuse, then new full publication/evidence bound to correction. Missing route/422/409/unchanged-run fallback fails.
- Structural gate must be requested without client metrics, pass from decoded output, and fail after an isolated tamper/drift case.
- Run Chromium twice sequentially using distinct fresh DB/runtime/output roots and the same validated production build manifest. Retain raw stdout/stderr, lifecycle timestamps, exact PIDs/ports, DB SQL dumps, ffprobe/frame hashes, renderer route/attempt evidence, checkpoint pre/post snapshots, correction closure and port cleanup. Preserve unrelated listeners.

## 5. Exit gates

After zero writer and stable tree:

1. J1-v4 13/13 direct bytes + EOL unchanged.
2. All `tests/test_s10*.py` pass twice on fresh roots; specifically the prior two T03 failures pass. No skip/xfail/assertion weakening.
3. Retained S09 renderer/T06 production suites pass; real adapter invocation count/evidence is nonzero and source-only re-encode negative control fails.
4. Ruff on the S10 production write-set has no functional error (`F*`, unsafe ignored hash/value, import/runtime defect); classify any remaining formatting debt exactly. Mypy relevant modules green.
5. One Alembic head and migration round trip; materialized OpenAPI additive with unique operation IDs and a real recompute route.
6. Frontend TSC, scoped ESLint and one production build green; active build manifest hash is reused by both accepted runs.
7. Direct DB truth per run: partial checkpoint before kill, exact resume reuse, affected-only recompute attempts, non-null artifact SHA/size, decodable files, exactly one active completed publication per accepted lineage and no `.partial`.
8. `git diff --check`; complete write attribution; all six task packet revisions current; no unowned process; task ports free; protected MAIN/data/channels/user media unchanged.

## 6. Reporting

For each correction append exact session ID, resume command/model/reasoning, start/end, files, tests/counts, raw evidence and finding closure to the existing task LOG/REPORT and Manager registry. Replace false current claims only by appending a clearly current C1 section; preserve history. Final sprint report must state the independent baseline `122 passed, 2 failed` and demonstrate the corrected rerun rather than claiming the old 124 result.

Begin now: load all required reading -> stable preflight -> resume T02 exact owner -> execute the frozen serial DAG through T04C -> exit gates -> stop at `TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`. Không chỉ trả kế hoạch.
