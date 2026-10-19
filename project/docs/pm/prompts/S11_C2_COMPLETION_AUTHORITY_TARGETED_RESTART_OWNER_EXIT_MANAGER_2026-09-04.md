# HERMES PROMPT — S11-C2 Completion Authority + Targeted Restart + Owner/Remote Closure

Bạn là Hermes Manager mới cho correction sprint hữu hạn `S11-C2` của
MotionForge2D. Bắt đầu thực thi ngay; không chỉ trả kế hoạch.

## 0. Mandatory authority load

Trước preflight hoặc dispatch, đọc TOÀN BỘ:

1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
2. `C:\Users\Admin\MotionForge2D\AGENTS.md`
3. `C:\Users\Admin\MotionForge2D\frontend\AGENTS.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C1_PM_REREVIEW_2026-09-04.md`
8. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_T02_T06_PM_REVIEW_2026-09-04.md`
9. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S11_C1_FULL_SCOPE_READINESS_RESTART_EXIT_MANAGER_2026-09-04.md`
10. `C:\Users\Admin\MotionForge2D-evidence\s11-c1\manager\REGISTRY.md`
11. `C:\Users\Admin\MotionForge2D-evidence\s11-c1\manager\exit\EXIT_VERDICT.md`
12. `C:\Users\Admin\MotionForge2D-evidence\s11-c1\manager\exit\NEXT_REVIEW_PACKET.md`
13. LOG/REPORT/evidence và current source/tests của T03G, T04B, T05A, T06C,
    T04D owner identity và S11-INT01.

Sau khi đọc, báo `RULES_LOADED` kèm path, SHA-256, số dòng, local HEAD, remote
HEAD và các mục chính đã nạp. Rules canonical thắng mọi prompt/report cũ.

## 1. Verdict, authority và review boundary

`AUTHORIZED_TO_DISPATCH` chỉ cho `S11-C2` trong prompt này.

- Current verdict: `S11-C1 = CHANGES_REQUESTED / NOT_APPROVED`.
- Whole sprint: `S11 = NOT_CLOSED`.
- Không mở hoặc làm S12/S13.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Canonical branch: `codex/s11-integration`.
- Reviewed local HEAD: `c9d5453b429fd96957860cd7ed27eddcf18e2ead`.
- Expected remote HEAD vào vòng:
  `4d7ad8196c3f7a21af744906ef4174690159d889`.
- Known state: local ahead remote 14 commits. Đây là finding đã pin, không phải
  quyền reset/rebase/force hoặc push sớm.
- Manager S11-C1 đã nghỉ; mở MỘT Manager session mới, compact. Manager không sửa
  production code/test/config/migration.
- Terminal xanh duy nhất:
  `S11-C2 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`.
- Không tự ghi `APPROVED`, `CLOSED` hoặc mở sprint tiếp.

## 2. Model policy

Mọi turn được dispatch/resume bởi prompt này dùng:

- provider/route: custom 9Router;
- model: `ocgfree/muse-spark-1.3-contributor-free`;
- requested reasoning: `max`;
- fallback: `OFF`;
- TTFB timeout: `900` giây.

Ghi requested và actual route/model trong registry bằng Hermes state evidence.
Nếu connection/502/503/504/disconnect, áp dụng chính xác wait 5 phút rồi resume
cùng session/model. Unknown model/auth/quota xác định => `BLOCKED_MODEL_ROUTE`;
không fallback hoặc đổi model.

## 3. Preflight và cleanup trước writer

Manager tự làm và lưu raw evidence dưới run-id mới:
`C:\Users\Admin\MotionForge2D-evidence\s11-c2\`.

1. Canonical porcelain phải rỗng; local HEAD phải đúng `c9d5453`.
2. Remote phải đúng `4d7ad81`. Bất kỳ local/remote SHA khác cặp đã pin =>
   `BLOCKED_REMOTE_DRIFT` trước write.
3. Xác minh command line rồi dừng hai loop/background process chạy
   `s11c1_watchdog.py`; remove/disable cron `s11c1-watchdog-10m` nếu còn. Chứng
   minh không còn process, cron, heartbeat hoặc file mtime tiếp tục thay đổi.
   Không tạo watchdog/cron mới cho C2; Manager dùng monitor/heartbeat native.
4. Zero implementation writer/pytest/product app/ffmpeg của S11. Dùng exact-
   owner + process + worktree evidence, không kết luận từ một tín hiệu.
5. Unset production DB env; mọi test/probe dùng fresh Alembic-head SQLite,
   basetemp/root unique và đủ ngắn.
6. Chụp SHA-256, bytes, logical lines, mtime, tracked/dirty attribution bằng
   `docs/pm/tools/write_set_guard.py` hoặc equivalent cho:
   - `app/persistence/qc_check_runs.py`
   - `app/workflow/qc_checks_handler.py`
   - `app/persistence/readiness.py`
   - `app/services/qc_correction_bridge.py`
   - `tests/test_s11_t03g_qc_check_job.py`
   - `tests/test_s11_t03g_qc_check_api.py`
   - `tests/test_s11_t05a_readiness_api.py`
   - `tests/test_s11_t02_t06_acceptance.py`
   - T03G/T04B/T05A/T06C session LOG/REPORT.
7. Query Hermes state DB read-only và ghi durable identity:
   - real T05A owner = `20260903_203404_4a4548`;
   - `20260903_203404_5b3841` is T04D owner and must never receive T05A work.
8. Các exact task worktree phải sạch. Trước write, owner đưa task branch lên
   current local canonical bằng `merge --ff-only`; không reset/rebase/stash/
   clean/force. Không ff được => stop và báo Manager.

File hiện hữu chỉ patch hẹp có preimage. Cấm whole-file overwrite,
`write_file`, redirection, `Set-Content`, `Out-File`, script direct-write,
copy/move-overwrite hoặc generated rewrite. Guard sau mỗi turn; destructive
shrink/scope drift => freeze writer ngay.

## 4. Durable session map và context-health gate

| Role | Exact session | Worktree / branch | Quyền |
|---|---|---|---|
| T03G | `20260903_170546_0d42f6` | `s11-t03g-0903w8` / `codex/s11/t03g-0903w8` | completion authority |
| T06C | `20260903_223530_b90853` | `s11-t06c-0903w14` / `codex/s11/t06c-0903w14` | executable acceptance |
| T04B conditional | `20260903_183246_706d31` | `s11-t04b-0903w10` / `codex/s11/t04b-0903w10` | product bridge only if reproduced |
| T05A real owner | `20260903_203404_4a4548` | `s11-t05a-0903w12` / `codex/s11/t05a-0903w12` | API/consumer regression |
| T04D owner, frozen from T05A | `20260903_203404_5b3841` | T04D lineage | no C2 dispatch |
| INT01 | `20260903_112116_35051c` | canonical / `codex/s11-integration` | Git transport only |

T03G và T06C đã compact/context dài và C1 còn miss contract. Trước resume, gửi
compact handoff chỉ gồm current local SHA, finding hiện tại, finite matrix,
allowlist/forbidden set, exact commands và terminal. Đây là một guarded bounded
resume cuối của lineage hiện tại. Nếu owner lại làm sai workflow, bỏ matrix,
không tạo usable bytes hoặc có unsafe/scope write, dừng
`BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`; không tự tạo recovery owner.

Ghi incident T05A trung thực: commit `3beee0d` được tạo bởi T04D session bị
misroute. Không rewrite history để che. Freeze `...5b3841` khỏi T05A; phần T05A
còn lại chỉ exact owner `...4a4548` được viết.

## 5. Wave C2-A — hai lane disjoint chạy song song

Chỉ dispatch khi preflight/cleanup xanh. Maximum safe concurrency = 2.

### C2-A1 — T03G: completion envelope và unbounded matching-full authority

Resume exact T03G. Allowed write set:

- `app/persistence/qc_check_runs.py`
- `tests/test_s11_t03g_qc_check_job.py`
- `tests/test_s11_t03g_qc_check_api.py`
- `docs/pm/sessions/S11-T03G/**`
- external S11-C2 evidence.

`app/workflow/qc_checks_handler.py` là read-only trừ khi exact executable RED
chứng minh completion producer thiếu field bắt buộc; khi đó T03G báo Manager
trước, không tự mở scope.

Required invariants:

1. Query/chọn newest matching `SCOPE_FULL` trực tiếp; 50, 51 hoặc 100+ newer
   audio/partial jobs không được evict valid full authority. Không scan một
   page hỗn hợp có limit rồi filter trong memory.
2. Newest matching full queued/running/failed/stale/corrupt vẫn fail closed và
   không fallback full cũ.
3. Completion identity phải khớp manifest/current cho schema, job type, scope,
   scope fingerprint, evidence fingerprint, policy identity/hash, source
   generation và các identity field producer thực sự ghi.
4. Required summary fields phải PRESENT với JSON type hợp lệ; missing/null/bool/
   string/unreadable không được default thành zero.
5. `errors == 0`, `checks_skipped == 0`, `cancelled is False`,
   `deadline_exceeded is False`.
6. `checks_requested == checks_run == len(full_band) == 10`; detector list phải
   exact full band, không duplicate/extra/missing.
7. Detector revision envelope phải exact key set, mỗi value non-empty và phù
   hợp server-owned revision evidence; missing/extra/empty fails closed.
8. Valid full completed zero-item remains ready candidate; open blockers still
   return blocked; audio-only never becomes full authority.

Finite executable matrix trên fresh real DB phải có ít nhất:

- required `errors` missing, null, string và bool;
- required `checks_skipped` missing, null, string và bool;
- completion evidence fingerprint mismatch;
- completion policy hash/id mismatch;
- source generation mismatch;
- requested/run count missing, 0, 9, 11 hoặc unequal;
- cancelled/deadline true hoặc missing required producer field;
- detector duplicate/missing/extra;
- revision missing/extra/empty;
- valid full + 51 and 101 newer audio runs retains exact full job;
- no full + 101 audio runs remains never_run;
- newest full nonterminal/stale/corrupt does not fallback;
- valid full zero-item ready and valid full blocker blocked.

Không chỉ test helper trực tiếp: có ít nhất một API/project readiness row cho
completion identity tamper và history-pressure case.

### C2-A2 — T06C: restart the actual targeted correction/recompute path

Resume exact T06C. Allowed write set:

- `tests/test_s11_t02_t06_acceptance.py`
- `docs/pm/sessions/S11-T06C/**`
- external S11-C2 evidence.

Production code, T03G tests và T04B tests read-only trong lane này.

Replace/augment the misleading C1B proof with an executable scenario that:

1. Seeds real project/video, occurrence/role, affected and unaffected ready
   artifacts including their row IDs, SHA-256 and managed bytes, plus an
   eligible QC blocker.
2. Calls the real correction API/`qc_correction_bridge.run_correction_chain`,
   producing one durable `ObjectCorrection` and one queued
   `RECOMPUTE_OBJECTS` job. `submit_run_qc_checks` alone is not this row.
3. Records the queued correction/recompute state, stops/drops service/worker,
   recreates a new production `JobService` on the same DB and managed root,
   and resumes the persisted recompute with bounded polling.
4. Proves exactly one correction, one recompute successor/effect, one terminal
   resolution and no duplicate enqueue/attempt caused by restart/replay.
5. Proves affected role/segment artifacts are recomputed while every unaffected
   ready artifact row, association, SHA-256 and byte content is identical.
6. Proves manifest scope is affected-only and no full-project/full-timeline job
   or publication occurs.
7. Reopens fresh repository/service reads and proves stable final correction,
   recompute, QCItem and readiness state.
8. Writes assertion-indexed evidence to the new S11-C2 run-id, not historical
   C1 files. Docstring/comments must match the operation actually executed.

Run the exact new node twice on separate fresh roots. If it passes current
production bytes, do not dispatch T04B. If it exposes a product defect, save a
minimal failing reproducer with actual/expected and return
`NEEDS_T04B_PRODUCT_FIX`; T06C must not edit product code.

### Per-lane terminal

Each owner runs micro matrix -> full own module -> Ruff/mypy affected scope ->
own diff-check, proves allowlist and guard, commits local task branch, returns
SHA/raw outputs and `TASK_SUBMITTED`, then exits. No push/merge/rebase/reset/
stash/clean/force.

Manager independently reviews current committed bytes and reruns risk rows.
Only `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` commits proceed.

## 6. Conditional C2-A3 — T04B only on executable product failure

Only when C2-A2 produces a minimal failing correction/recompute restart case,
resume exact T04B owner. Allowed write set:

- `app/services/qc_correction_bridge.py`
- directly affected T04B correction/recompute tests;
- `docs/pm/sessions/S11-T04B/**`;
- external S11-C2 evidence.

No speculative refactor. T04B fixes the reproduced defect and commits. Then
T06C exact owner fast-forwards to the new canonical integration point and reruns
the exact executable acceptance twice. If C2-A2 passes current production,
T04B remains undispatched.

## 7. Provisional integration after C2-A

Resume exact INT01. It is Git-only: no manual source/test edits.

- Verify canonical clean at pinned local HEAD and remote still pinned old HEAD.
- Merge Manager-verified task commits conflict-free. Conflict => abort and
  return exact owner; no manual resolution.
- Run combined T03G matrix + T06C executable node.
- Commit integration evidence locally.
- Do NOT push yet; T05A consumer lane depends on integrated T03G behavior.

## 8. Wave C2-B — real T05A owner, dependency-serial

Only after T03G is integrated and combined micro gate green, resume exact T05A
owner `20260903_203404_4a4548`. Never resume `...5b3841`.

Allowed write set:

- `tests/test_s11_t05a_readiness_api.py`
- `app/persistence/readiness.py` only if a real consumer defect requires it;
- `docs/pm/sessions/S11-T05A/**`;
- external S11-C2 evidence.

Owner must read current bytes including misrouted commit `3beee0d`, independently
re-derive them from the current contract, record which bytes are retained or
replaced, and add real API/project aggregate regression for:

1. completion missing required zero fields => `not_run`, never ready;
2. completion identity mismatch => `not_run`;
3. valid full followed by 51+ audio jobs => still exact full authority;
4. no full with 51+ audio jobs => `not_run`;
5. multi-video project with one corrupt/missing full authority => project
   `not_run`;
6. valid full complete zero-item => ready candidate;
7. valid full + blocker => blocked.

No history rewrite to hide the misroute. Commit the exact-owner correction and
document the ownership incident in LOG/REPORT. Manager verifies independently,
then INT01 merges conflict-free.

## 9. Final gate ladder and remote push

Fail small before broad. Any failure returns to exact owner; do not run broad
while matrix is red.

1. Codex three-probe regression: missing counts, completion identity mismatch,
   valid full hidden behind 51+ audio runs — all expected fail-closed/retained.
2. T03G finite matrix 100% and full T03G modules.
3. T06C actual correction/recompute restart node twice on fresh roots.
4. T05A API/project matrix and complete T05A modules.
5. Combined T03G + T04B if used + T05A + T06C focused gate.
6. Ruff and mypy retained affected scope.
7. `git diff --check 7751598214eedb6b72e3783e39a2a408721abe40..HEAD`
   exit 0.
8. Alembic sole head + fresh upgrade; migrations unchanged unless separately
   authorized (none are authorized here).
9. OpenAPI duplicate-route gate.
10. Outer acceptance must include the genuine targeted restart node and pass at
    least 11/11 without lowering collection.
11. Inner S11 QC suite must retain at least 326 passes plus all new nodes.
12. T01 64/64 and S10 full-apply 71/71.
13. Frontend evidence may be retained only with hash proof that frontend and
    public API contract files are unchanged; otherwise rerun build/Playwright.
14. Canonical porcelain empty; zero pytest/product/ffmpeg/writer; no watchdog,
    cron or heartbeat.

Only after every gate green, resume INT01 for ONE non-force push:

`git push origin HEAD:refs/heads/codex/s11-integration`

Then independently verify `git ls-remote` equals local final HEAD. Push failure
or remote drift is terminal blocker; no force push. The sprint is not submitted
until local == remote.

## 10. Evidence and terminal packet

Create:

- `C:\Users\Admin\MotionForge2D-evidence\s11-c2\manager\REGISTRY.md`
- raw preflight/cleanup/process/model/guard/micro/matrix/focused/static/broad/Git
  outputs;
- per-lane prompt snapshots and dispatch logs;
- `manager\exit\EXIT_VERDICT.md`;
- `manager\exit\NEXT_REVIEW_PACKET.md`.

Packet must map every finding to exact owner/session/commit/test; disclose the
T05A/T04D misroute and repair; list actual model usage; show T04B conditional
decision; include local/remote final SHA, clean porcelain and zero watchdog;
index every adversarial row with actual/expected and raw path.

Green terminal only:

`S11-C2 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Any open P0/P1/P2, overclaim, wrong owner, route fallback, destructive write,
unresolved conflict, red matrix, active watchdog or local/remote mismatch =>
report exact blocker and stop without closing S11.

Bắt đầu ngay: full rules load -> new registry -> stop S11-C1 watchdog -> pinned
preflight -> dispatch C2-A1 và C2-A2 song song nếu xanh.

