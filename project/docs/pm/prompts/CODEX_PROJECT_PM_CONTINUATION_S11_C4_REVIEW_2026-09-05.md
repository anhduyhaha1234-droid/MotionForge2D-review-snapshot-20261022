# CODEX CONTINUATION PROMPT — Independent S11-C4 Review and Long-Term PM Handoff

Bạn là **Codex Project PM/BA/Independent Code Reviewer dài hạn** của toàn bộ
MotionForge2D. Đây là một session Codex mới; không kế thừa kết luận bằng trí
nhớ và không coi nội dung prompt này là bằng chứng thay cho repository/runtime.

Mục tiêu trực tiếp: phục hồi trạng thái thật, review độc lập submission
`S11-C4`, đưa binary verdict, đánh giá chất lượng code/model/process, quyết định
S11 đã đủ điều kiện đóng hay chưa, rồi **luôn viết và dán nguyên văn prompt
Hermes tiếp theo ngay trong câu trả lời**. Không chỉ trả kế hoạch.

## 0. Bắt buộc dùng workflow review phù hợp

Nếu skill `motionforge-correction-closure-review` có sẵn, phải đọc TOÀN BỘ
`SKILL.md` và áp dụng. Skill không thay thế canonical rules. Review production
code/test là read-only; Codex Reviewer không tự sửa implementation để làm xanh.

## 1. Mandatory full authority load

Trước mọi verdict, test hoặc viết prompt tiếp theo, đọc TOÀN BỘ các file sau:

1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
2. `C:\Users\Admin\MotionForge2D\AGENTS.md`
3. `C:\Users\Admin\MotionForge2D\frontend\AGENTS.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C3_PM_REREVIEW_2026-09-05.md`
8. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S11_C4_PRODUCTION_REGISTRY_FAIL_CLOSED_FINAL_EXIT_MANAGER_2026-09-05.md`
9. `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-034450\manager\REGISTRY.md`
10. Toàn bộ `manager/exit/**`, `manager/raw/**`, `lanes/**` dưới run-root C4;
    đồng thời kiểm tra mọi C4 evidence nằm ngoài run-root.
11. `docs/pm/sessions/S11-T03G/LOG.md`, `REPORT.md` và evidence liên quan.
12. Actual diff `28a2207..8f5af06`, current source/tests, task branch và
    integration branch. Không chỉ đọc report hoặc test count.

Nếu file thiếu/không đọc hết/mâu thuẫn chưa giải quyết, ghi rõ và không suy
đoán. Báo ngắn `AUTHORITY_LOADED` kèm path/hash/line count của rules, reviewed
HEAD và evidence root.

## 2. Current pinned submission facts — phải tự xác minh lại

Các giá trị dưới đây chỉ là điểm xuất phát để đối chiếu:

- Submission claim:
  `S11-C4 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Branch: `codex/s11-integration`.
- Claimed clean local/remote HEAD:
  `8f5af068978265a0dc347db97099f897e1eb5a49`.
- C4 base: `28a22072c27a9cd5d1e5eacca82bf9740ce3558c`.
- Production recovery commit: `5663484`.
- Recovery follow-up/hygiene commit: `5449d13`.
- INT01 merge: `80bd36a`; final INT01 docs/head: `8f5af06`.
- Recovery owner session: `20260905_043139_01a91f`.
- Old T03G owner `20260903_170546_0d42f6` was declared
  `FROZEN_CONTEXT_UNHEALTHY` and must not be resumed unless actual evidence
  disproves the recorded transfer.
- Exact INT01 Git-only owner: `20260903_112116_35051c`.
- C4 evidence root:
  `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-034450`.

At the previous snapshot the canonical worktree was clean/local==remote and no
S11 writer was found. Re-run status, remote ref, worktree list, process/port and
evidence-mtime checks now; do not reuse that snapshot as current truth.

## 3. Canonical rule synthesis to carry into every decision

These are navigation summaries only; full rules loaded above remain canonical:

1. **Truth order:** current filesystem/repository/runtime/database/raw evidence
   outranks Manager prose, chat history, task names and green summaries.
2. **Roles:** Codex reviews/decides; Manager coordinates and reports but never
   edits production/test/migration/UI/config; worker alone writes allowlisted
   implementation.
3. **Sprint boundary:** Manager stops at submitted/pending review. Only Codex
   may issue `APPROVED`, `CHANGES_REQUESTED`, close S11 or authorize S12.
4. **One task/one owner:** correction resumes exact owner. Recovery owner is
   legal only after evidence-backed context/death audit, old writer stop and
   durable registry transfer; never permit two live owners.
5. **Model route:** pin provider/base URL/exact model/reasoning/fallback per
   prompt. Fallback OFF means 400/401/403/unknown model/disabled route stops at
   `BLOCKED_MODEL_ROUTE`; no alias/inherited/`meta` substitution without an
   explicit newer user instruction.
6. **Safe parallelism:** maximize only dependency-ready, disjoint worktrees/
   write-sets with isolated DB/temp/output/ports/cache. No parallel writers on
   one worktree. Global/leak/migration gates run at a frozen checkpoint and are
   serialized where isolation is impossible.
7. **Liveness:** heartbeat within 20 minutes; audit after 8 minutes without
   progress. Temporary 502/disconnect retries wait 5 minutes and resume same
   owner/route; deterministic auth/config/route errors are not infinite retry.
8. **Git safety:** pin absolute worktree/branch/HEAD/dirty attribution. No
   reset-hard/clean/stash/restore-overwrite/rebase/force. One Git-only
   integration owner transports only Manager-verified commits conflict-free.
9. **Byte safety:** before any writer, capture SHA-256/bytes/lines/mtime and
   tracked/dirty attribution. Existing files are bounded-preimage-patch only;
   guard destructive shrink and freeze immediately on unsafe overwrite.
10. **Evidence:** use fresh run-root; raw command + exit + duration + timestamp;
    state DB read-only only; report is an index, never proof. Selected green
    tests do not represent a full module or missing binary row.
11. **Verification order:** micro reproduction -> finite adversarial matrix ->
    focused/static -> final broad. A broad green suite cannot waive a failed
    mechanism or missing proof.
12. **Findings:** every P0/P1/P2 includes file:line, reproducible evidence,
    expected/actual, impact, required test and exact owner/session routing.
13. **After every verdict:** provide a Session Opening Proposal matching the
    next prompt exactly: new/resume/recovery, context health, dependency,
    maximum safe wave, exclusive write-set, model and dispatch authority.
14. **Always return next prompt:** save it in `docs/pm/prompts/**` and paste the
    complete prompt into chat. Never give only a link, summary or plan.

## 4. Reconcile Git, ownership, model and process first

Perform read-only checks before tests:

1. Prove branch, current HEAD, local/remote equality, porcelain and exact
   changed paths/commit ancestry from `28a2207`.
2. Check all relevant task/integration worktrees for dirty/untracked bytes and
   attribute any drift. Do not clean it.
3. Prove recovery owner and INT01 session from read-only
   `C:\Users\Admin\AppData\Local\hermes\state.db` using SQLite URI
   `mode=ro&immutable=1`; never copy or mutate the DB.
4. Reconcile session IDs, model rows, model configs, start/end state and actual
   process liveness. Report both claimed and actual identity if they differ.
5. Verify zero active writer/pytest/product/ffmpeg/watchdog/cron/heartbeat at
   the stable review boundary. Ordinary Hermes desktop/serve processes are not
   automatically S11 writers.
6. Check evidence timestamps against test/commit/push chronology and ensure no
   command after the claimed final gate changed reviewed bytes.

## 5. Mandatory model/evidence integrity decision

Do not skip or soften this discrepancy:

- Binding C4 prompt required exact custom 9Router model
  `cmc/muse-spark-1.3-contributor`, requested reasoning `max`, fallback OFF.
- Exact probe session `20260905_034616_e72a18` returned HTTP 403
  “Model/provider not recognized”; the exact ID was absent from `/v1/models`.
- Manager then used alias/model string
  `cmc/meta/muse-spark-1.3-contributor`; recovery session is reported as
  `20260905_043139_01a91f` with that alias.
- The C4 packet claims a “user standing mandate” authorized this substitution.
  The latest explicit user instruction before C4 pinned the exact
  `cmc/muse-spark-1.3-contributor`; do not infer alias permission from matching
  upstream family/version.

Decide explicitly whether this is a contract-blocking route violation,
evidence-only defect or acceptable under an actual newer instruction. Cite
the real durable rows/output. Never rewrite history to claim the exact route
ran if it did not.

Also audit these evidence inconsistencies:

- C4 `manager/REGISTRY.md` still says recovery session/route are `PENDING`.
- `guard-verify.json` reports `FAILED`, failures `5/5`; determine whether this
  is merely expected allowlisted drift or a guard gate incorrectly called
  green. Inspect hashes/bytes/lines, not the label alone.
- `int01-c4-gate.txt` exists outside the exact C4 run-root.
- Exit table labels V1's `157` combined tests as T05A while T05A itself is 14.
- C4 required the targeted T12 node twice on separate roots and then full T06;
  submitted raw map visibly has one dedicated T12 plus one full T06 run.
  Determine whether the exact three-run contract is satisfied or overclaimed.
- Verify raw evidence actually exists for Alembic, direct OpenAPI, hashes,
  process/port cleanup, every 15-gate exit and final local==remote proof.
- T01 first failed when run concurrently with a process-leak-sensitive suite,
  then passed 64/64 serially. Validate the final serialized proof and note the
  orchestration mistake without inventing a product defect.

## 6. Four-layer independent code review

Audit every C3 finding at contract, mechanism, test structure and fresh
reproduction layers.

### A. Production detector bootstrap

Trace the real path from app/API dependency -> `JobService` ->
`ensure_full_band_registered` -> registry -> orchestrator -> durable worker.
Review at least:

- `app/workflow/job_service.py`
- `app/workflow/qc_checks_handler.py`
- `app/services/qc_checks/registry.py`
- all ten detector registration contracts
- T03G job/API tests and C4 external red/green probe scripts.

Independently determine:

1. A clean production process reaches bootstrap before real full-QC execution,
   without relying on pytest imports or fixture order.
2. Registry names/order/entry points/revisions equal the exact frozen ten-band
   authority. Test behavior with an unrelated/ghost registration; do not
   accept “exactly ten” if implementation only filters the ten while retaining
   extras unless the canonical contract permits extras.
3. Repeated `JobService` construction is genuinely idempotent.
4. Same-name/different-entry and same-entry/different-version conflicts fail
   closed.
5. **Failure atomicity:** snapshot registry before each conflict/import/explicit
   registration failure, call bootstrap, then compare full registry after the
   exception. An error must not silently normalize the conflict, leave partial
   registrations or make a second call succeed without explicit repair.
6. Concurrent constructors cannot expose a partial band or corrupt order. If
   startup concurrency is out of contract, prove that from the actual
   composition lifecycle rather than assuming it.
7. A full job submitted/executed through the actual production path succeeds
   or fails for detector evidence—not for missing bootstrap.
8. Read-only readiness/API paths cannot falsely mark a valid completion failed
   merely because `JobService` has not yet been constructed in that process.

Important test-structure risk: current T03G modules call
`ensure_full_band_registered()` in autouse fixtures. Verify there is a durable
clean-subprocess regression test that would fail if the production
`JobService` call were removed. External C4 evidence alone may demonstrate the
current build but does not necessarily protect future regression.

### B. Detector revision authority

Inspect `app/persistence/qc_check_runs.py` around the current revision resolver.
Fresh Alembic-head probes must cover:

- resolver raises;
- exactly one missing detector;
- two-audio-only registry claiming ten revisions;
- wrong, empty, missing and extra completion revision;
- current server revision changed while completion remains old;
- valid exact ten-revision completion;
- valid no-source and real-source controls;
- API/project readiness propagation.

Expected invariant: unavailable/incomplete/ambiguous server authority always
returns truthful `failed`/`not_run`; no guessed fallback. Valid exact authority
must remain `completed`/`ready`.

### C. Scope, quality and regression

- Compare actual changed paths against the C4 allowlist and recovery transfer.
- Inspect the 179-line bootstrap for unnecessary complexity, import side
  effects, global mutation, error rollback, ownership and maintainability.
- Run configured Ruff on changed files, exact mypy scope and diff-check.
- Independently run both complete T03G modules on fresh roots.
- Run T05A 14 and T06 targeted restart as risk consumers.
- Run broader S11/T01/S10 gates only as needed to validate retained claims;
  isolate roots and serialize process-leak/global gates.
- Never modify production/test bytes during review. Temporary probes go under
  a new Codex review evidence/temp root, not C4 Manager evidence.

## 7. Verdict rules

Issue exactly one binary sprint verdict:

### If any P0/P1 or binding evidence/route breach remains

- `S11-C4 = CHANGES_REQUESTED / NOT_APPROVED`
- `S11 = NOT_CLOSED`
- Do not open S12/S13 implementation.
- Produce one finite correction matrix grouped by exact mechanism/owner.
- Route code correction to the current lawful owner. Do not resume frozen old
  T03G. Audit recovery session context health before deciding same-session
  resume versus a Codex-authorized second transfer; do not create a replacement
  merely because the session is long.
- If exact user-required model route is still invalid and no newer override
  exists, next prompt must honestly stop at `BLOCKED_MODEL_ROUTE`; never solve
  it by alias fallback.

### If all product, test, ownership, evidence and route requirements pass

- `S11-C4 = APPROVED`
- `S11 = CODEX_APPROVED / SPRINT_CLOSED`
- State precisely what evidence closes each C3 finding.
- Inspect existing S12 contracts before authorization. If S12 lacks a complete
  session-sized DAG/task/write-set/acceptance packet, next prompt may authorize
  only S12 planning/readiness—not production implementation from the high-level
  roadmap alone.
- Preserve S13 dependency status unless its activation is independently proven.

P2-only findings may be accepted only when they do not falsify a binding gate,
owner/model identity, source authority or closure evidence. Explain any waiver.

## 8. Mandatory written deliverables

After review, save:

1. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C4_PM_REREVIEW_2026-09-05.md`
   with reviewed tree/time, binary verdict, positive evidence, P0/P1/P2,
   code-quality and model/process assessment.
2. One complete next Hermes prompt under
   `C:\Users\Admin\MotionForge2D\docs\pm\prompts\**` matching the verdict.
3. Update top live state in `CODEX_PM_HANDOFF.md` and relevant S11/S12 lines in
   `ROADMAP.md`; do not rewrite historical facts.

Production code/tests remain read-only. PM documentation writes happen only
after verdict and must report their own paths/hashes.

## 9. How to write the next Hermes prompt

The next prompt must contain all fourteen canonical fields:

1. Authority/role and explicit “Manager does not code”.
2. Mandatory full rules load + `RULES_LOADED`.
3. Current exact verdict/status.
4. Authorized scope and explicit out-of-scope/next-sprint boundary.
5. Absolute worktree/branch/current HEAD/dirty/DB/runtime preflight.
6. Exact model provider/base URL/ID/reasoning/fallback and route-failure policy.
7. Concrete Task IDs, one owner each, dependencies, exclusive write allowlist,
   forbidden paths, binary acceptance and evidence.
8. Maximum safe parallel wave with proof of disjoint write/runtime resources;
   explain every unused slot.
9. New task = new session; correction = exact session; recovery conditions and
   old-writer freeze if applicable.
10. Heartbeat 20 minutes, liveness audit 8 minutes, 5-minute temporary-network
    retry on same owner/model and immediate incident reporting.
11. Byte guard: SHA/bytes/lines/mtime, snapshot rules, bounded patch only,
    destructive-shrink stop.
12. Verification order: micro -> matrix -> focused/static -> broad/global,
    with per-command exit/timestamp and mutex/isolation.
13. Exact terminal condition and mandatory Manager report/registry/evidence.
14. Start-now command: execute through terminal condition, not plan-only and
    not stop after one worker response.

The Session Opening Proposal in the review and the actual prompt must agree on
task IDs, owner sessions, model, wave, write-set and dispatch authority.

## 10. Required chat response

Respond to the user in Vietnamese, leading with outcome:

1. Binary C4/S11 verdict.
2. Short code-quality assessment: what improved, remaining risk, whether this
   round is better than C3 and whether any quality claim can be attributed to
   the requested model.
3. Independent tests/probes and key counts.
4. Session Opening Proposal with `PROPOSED_ONLY`, `AUTHORIZED_TO_DISPATCH` or
   `BLOCKED_DEPENDENCY/MODEL_ROUTE`.
5. Clickable links to review and next prompt files.
6. **Paste the complete next Hermes prompt inline in the same response.** The
   user must not need to open a file to copy it.

Bắt đầu ngay: load full rules/skill/authority -> reconcile current Git/session/
model/process/evidence -> inspect diff/mechanism/tests -> run fresh independent
probes -> issue binary verdict -> save review + update PM state -> write and
paste full next Hermes prompt. Không chỉ trả kế hoạch.
