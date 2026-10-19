Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa coordination artifact hoặc resume worker. Sau đó báo `RULES_LOADED` kèm absolute path, line count, SHA-256, worktree/branch/HEAD/dirty state thực tế và các mục rules đã nạp. Tiếp theo đọc TOÀN BỘ `C:\Users\Admin\MotionForge2D\AGENTS.md`, `C:\Users\Admin\MotionForge2D\docs\pm\prompts\CODEX_PROJECT_PM_HANDOFF_2026-08-23.md`, `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_FULL_APPLY_MANAGER_2026-08-27.md`, `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C1_REAL_FULL_APPLY_CORRECTION_MANAGER_2026-08-28.md`, `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C0_PM_REVIEW_2026-08-28.md`, `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C1_PM_REVIEW_2026-08-28.md`, report/registry S10 hiện hành và TOÀN BỘ TASK/LOG/REPORT của sáu owner phải resume. Chưa đọc đầy đủ thì dừng `BLOCKED_RULES`.

# S10-C2 — DeepSeek real-production correction manager

Bạn là Hermes Manager correction của S10, không phải Codex Reviewer. Codex giữ quyền phân rã task, quyết định parallel, `APPROVED/CLOSED`, mở sprint tiếp theo và GitHub backup. Manager không viết production code/test/UI/migration thay worker; chỉ preflight, resume đúng exact owner, monitor bằng bounded checks, audit sau worker exit, chạy join/exit gates và append coordination evidence.

## 1. Authority, model override và terminal

- Current Codex verdict: `S10-C1 = CHANGES_REQUESTED`; `S10 = PENDING_CODEX_REREVIEW`, không `APPROVED/CLOSED`.
- Worktree authority: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, expected branch `codex/s08-integration`, reviewed base HEAD `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`; discover actual values, không reset/restore tree về snapshot.
- Protected MAIN/reference: `C:\Users\Admin\MotionForge2D`.
- User đã cấp quyền đổi model cho các worker correction còn lại vì `meta` hết usage. Mọi worker resume trong C2 bắt buộc dùng Hermes selector chính xác `deepseek-v4-flash`; preflight phải chứng minh effective provider/model là 9Router `ocg/deepseek-v4-flash`, reasoning effort `max`, fallback `OFF`, TTFB 900. Không dùng `meta`, không auto-fallback sang model khác, không ghi API key/token vào log/report. Route sai hoặc unavailable thì dừng `BLOCKED_MODEL_ROUTE`.
- Đây là model override cho exact existing owner sessions, không phải quyền tạo owner/session production mới.
- T01A/T01B frozen. Không mở task mới, không đổi owner, không parallel production writer, không sửa frozen S09 renderer/J1-v4 manifest.
- Không commit/push/merge/reset/restore/clean/stash. Không mở sprint/lane production khác.
- Terminal xanh duy nhất: `S10-C2 = TASK_MANAGER_VERIFIED / S10 = PENDING_CODEX_REREVIEW`, rồi dừng. Không tự ghi `APPROVED`, `CLOSED` hoặc unblock dependency.

## 2. Stable preflight bắt buộc

1. Xác minh process/writer thực tế. C1 registry dừng sau T04B-C1 dispatch bằng `meta`; `output/s10/c1/t04b-c1` chỉ có `prompt.txt`, T04B packet chưa có TASK/LOG/REPORT và frontend chưa đổi. Không nhận dispatch cũ là completion.
2. Inventory toàn dirty set, file mtime/size và attribution. Bảo toàn mọi pre-existing/unrelated file. Chỉ append coordination evidence sau exact worker exit và manager audit.
3. `MOTIONFORGE_DATABASE_URL` phải UNSET. Test/run dùng fresh isolated temp DB/root/basetemp/cache/output/ports ngoài MAIN và user data. Trên Windows phải test đúng nested-path behavior, không chỉ short POSIX path.
4. Re-hash J1-v4 13/13 direct bytes + EOL trước/sau. Frozen renderer modules chỉ được import/call.
5. Reproduce independent baseline trước sửa: full `tests/test_s10*.py` currently reports `143 passed, 2 failed`; inspect exact failures rather than trusting prior J3 registry claim.
6. Mọi resume command phải dùng exact old session ID với model override `deepseek-v4-flash`; record effective model, PID/process handle, start/end, exit code and changed files. Không dùng vòng `sleep 570`; monitor bằng bounded process/log checks theo rules và tiếp tục cho đến worker terminal.

## 3. Codex-frozen serial DAG

Thực thi đúng một production writer tại một thời điểm:

`PREP -> T02-C2 -> J1 -> T01C-C4 -> J2 -> T03-C2 -> J3 -> T04A-C2 -> J4 -> T04B-C1-R1 -> J5 -> T04C-C1 -> EXIT`

Không parallel các owner này: T02 định nghĩa executor mà T01C/T03 dùng; T04A phụ thuộc output/evidence của T01C/T03; T04B phụ thuộc server contract; T04C phụ thuộc toàn product. Chỉ read-only audit/hash không ghi chung mới được chạy song song.

## 4. Exact correction tasks

### S10-T02-C2 — authoritative renderer request and truthful route evidence

- Resume exact session `20260828_010435_b24638` bằng `deepseek-v4-flash`.
- Allowed: `app/services/s10_multi_role_apply.py`, `tests/test_s10_multi_role_apply.py`, exact task-owned append-only docs/output.
- Xóa hard-coded `s10_t02_ws/s10_t02_proj/s10_t02_item`; typed executor phải nhận và preserve server-bound workspace/project/video/segment identities.
- Không hash `layer_id` để bịa affected bbox, anchor, role, pack hoặc mapping. Require pinned source artifact, approved replacement asset/pack, exact segment geometry/mask, motion/contact/z-order, route, frame range/timebase and dependency hashes. Thiếu authority phải fail closed trước render.
- Effective adapter phải đúng route evidence. Không được chạy `SpriteAffineAdapter` nhưng report `controlled_redraw` nếu contract không định nghĩa chính xác mapping đó. Unsupported/unlicensed route fail closed; evidence record requested route, effective adapter, source/output hash, exact frames and visible affected-region delta.
- Real-adapter tests trên compact media phải chứng minh replacement-region change, exact identity/range/timebase, deterministic result and negative cases for missing/fabricated authority.

### J1

Sau worker exit: audit allowlist; chạy T02 tests hai lần trên fresh roots; retained renderer regressions; direct evidence probe; J1-v4 13/13 hash/EOL. Defect quay lại cùng T02 owner, không dispatch task kế.

### S10-T01C-C4 — pinned real inputs, durable publication and strict completion

- Resume exact session `20260828_003035_859fe5` bằng `deepseek-v4-flash`.
- Allowed: bounded T01C service/workflow/API/schema/handler files, T01C tests, exact task-owned append-only docs/output.
- Production worker phải load server-side immutable checkpoint/source artifact/replacement packs/scene/mapping/routes/corrections. Xóa `_ensure_synthetic_source`, `_ensure_replacement_asset`, fabricated layer/pack/mapping/route fallback khỏi production path. Test fixtures may build assets outside production handler only.
- Call corrected T02 executor with exact authoritative identities and pinned hashes. Each output must be decodable media, exact frame/range/timebase, actual SHA/size and route/dependency evidence.
- Zero chunks is fail-closed/non-completed unless product contract explicitly produces and verifies the required empty publication; do not mark completed without exactly one completed verified publication.
- Remove caller-controlled production `stop_after_chunk`; expose crash/restart injection only through test-owned worker control that cannot be supplied by production API manifest.
- Preserve strict resume tamper verification and deterministic stitch/publication. Add negative tests for synthetic/missing source, asset, mapping, route, zero chunks, stitch failure and caller crash-hook injection.

### J2

Run T01C tests twice, T02 and retained renderer regressions, OpenAPI, direct DB/artifact/publication probe, Ruff functional checks and mypy on touched modules. Source search must prove no production synthetic source/asset/fabricated mapping and no `.bin` Full Apply path.

### S10-T03-C2 — real durable affected-only recompute

- Resume exact session `20260828_011920_b79bd6` bằng `deepseek-v4-flash`.
- Allowed: `app/services/s10_recompute.py`, bounded recompute API/workflow wiring, `tests/test_s10_partial_recompute.py`, exact task-owned append-only docs/output.
- Delete digest repetition and every `chunk_*.bin` production path. Recompute must enqueue/resume durable work and invoke the same corrected T02 executor with the original pinned identities/dependencies plus correction provenance.
- Store decodable media with actual SHA-256, size, decoded frames/timebase and renderer route/attempt evidence. Never mark fake/missing bytes as ready/verified.
- Fix fresh nested Windows root/staging path robustly. Both previously failing tests must pass without shortening assertions or path coverage.
- Affected closure increments attempts exactly once and gets new verified media; unaffected artifact ID/SHA/size/frame metadata stays byte-exact with zero new adapter call. Replay dedupes. Restart must stop truly partial work and resume, not return a pre-completed checkpoint.
- Deterministically restitch/update publication after correction and bind it to correction/result hash while preserving unaffected identity.

### J3

Run full T03 twice on separate Windows fresh roots plus T01C/T02 regressions and direct DB/file probe. Assert no `.bin`, every recomputed artifact decodes, SHA/size columns match bytes, adapter invocation is nonzero, affected/unaffected attempts are exact, and a corrected publication exists. Then run full `tests/test_s10*.py`; any failure returns to exact owner.

### S10-T04A-C2 — measured server structural gate

- Resume exact session `20260828_014304_25d94a` bằng `deepseek-v4-flash`.
- Allowed: `app/services/s10_structural_compare.py`, bounded S10 gate API/service integration, `tests/test_s10_structural_compare.py`, exact task-owned append-only docs/output.
- Keep client metrics non-authoritative, then remove all server hard-coded/pass placeholders: no fixed low errors, zero inversions/events, mirrored/synthetic cuts, fake `shot_a`, fake annotations or hash-only proof presented as measurement.
- Compute required trajectory/scale/rotation/contact/z-order/visibility/clipping and cut/shot truth from the checkpoint-pinned source evidence, stored segment/motion/contact/order annotations and decoded rendered publication. Record exact input/output/policy/evidence hashes and measurement method/version.
- Missing tables/rows, unsupported measurement, absent annotations, stale policy, null SHA/size, undecodable/tampered media or frame/timebase mismatch must be `BLOCKED`, never converted into a pass placeholder.
- Tests must include a decodable but structurally wrong video, forged good request, removed evidence, wrong policy, cut drift, contact drift, z-order inversion and tamper; each must fail closed. A green case must be measured from real compact rendered evidence.

### J4

Run T04A twice plus real compact pass/fail probes, T03/T01C/T02 regressions, source search for placeholder metrics/annotations and direct evidence-hash/measurement-version checks.

### S10-T04B-C1-R1 — truthful Apply UX and complete packet

- Resume exact session `20260828_020206_b1f8af` bằng `deepseek-v4-flash`. C1 dispatch with `meta` produced no completed work; do not create a replacement owner.
- Allowed only previously authorized Apply frontend/API/nav/e2e files and `docs/pm/sessions/S10-T04B-apply-ux/{TASK,LOG,REPORT}.md` plus isolated output.
- Remove first-checkpoint implicit choice and every fabricated `gen-1`, frame count 100, shots, mapping, policy, metrics and annotations. UI must consume backend-resolved current checkpoint/readiness/plan/evidence for the selected project/video.
- Missing/stale/cross-project/incomplete authority keeps Apply disabled with exact Vietnamese reason. Structural action sends only run identity/request intent; display only hash-bound server-derived result for current publication/revision.
- Progress/cancel/retry/resume/recompute survive reload and reflect backend state. Complete current TASK/LOG/REPORT truthfully.

### J5

Run TSC, scoped ESLint, production Next build, focused Apply UI tests and backend regressions. Source/behavior audit must show zero production synthetic plan/metric fallback. Preserve 8888 fallback only where authorized.

### S10-T04C-C1 — strict real acceptance

- Resume exact session `20260828_023122_76b87e` bằng `deepseek-v4-flash`.
- Allowed only T04C harness/config/fixtures/task docs and fresh C2 output. Production defect returns to its exact owner above; T04C cannot patch production.
- Use production API/frontend and real frozen adapters on compact deterministic fixtures. No API mock, fake digest bytes, source-only re-encode or direct DB mutation to create business success.
- Two sequential accepted Chromium runs on distinct fresh DB/runtime/output roots must prove playable publication, exact frame/timebase/shot/cuts, visible replacement-region change, non-null matching SHA/size, route/adapter evidence and one active completed publication.
- Strict restart must capture `0 < next_chunk_index < total`, `0 < verified < total`, nonterminal run, exact pre-stop PID/port and artifact identities; stop exact owner, prove exit/port release, start different PID, resume via 2xx with `resumed=true`, preserve completed artifacts and finish remaining chunks. Terminal completion and 409 fallback are forbidden.
- Real correction endpoint must finish affected-only recompute: affected attempts +1/new media, unaffected attempts/artifact identity exact, restitched corrected publication and measured structural result. Missing route/non-2xx/unchanged-run fallback fails.
- Structural gate request contains no client metrics. Real green output passes measured gate; isolated structural drift/tamper is blocked.

## 5. Exit gates and reporting

After zero writer and stable tree:

1. J1-v4 13/13 direct bytes + EOL unchanged.
2. Full `tests/test_s10*.py` passes twice on independent fresh Windows roots; specifically the prior two recompute tests pass. No skip/xfail/assertion weakening.
3. Retained S09 renderer suites pass; real adapter calls/evidence are nonzero; negative source-only/fake-byte controls fail.
4. Ruff has no functional `F*`/runtime defect on production write-set; relevant mypy green; `git diff --check` green.
5. One Alembic head/round-trip; materialized OpenAPI additive, unique operation IDs and real recompute route.
6. Frontend TSC, scoped ESLint, production build and focused UI tests green.
7. Direct DB/file truth proves partial checkpoint/resume, real affected-only recompute, exact unaffected reuse, actual SHA/size, decodable files, measured structural gate, completed publication and no `.partial`/`.bin` production artifact.
8. Complete write attribution and current append-only packets/registry/report; no unowned process; task ports free; protected MAIN/data/channels/user media unchanged.

For every resume, append exact owner session, command selector, effective `ocg/deepseek-v4-flash`, reasoning, process handle, timing, files, tests/counts and raw evidence. Correct prior false claims by appending a current C2 section; do not rewrite history. Never expose credentials.

Begin now: load required reading -> stable preflight -> resume T02 exact owner with `deepseek-v4-flash` -> execute the serial DAG through T04C -> all exit gates -> stop at `TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`. Không chỉ trả kế hoạch.
