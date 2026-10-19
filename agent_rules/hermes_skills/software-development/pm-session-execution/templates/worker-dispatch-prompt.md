# Worker dispatch prompt template (Hermes CLI, PM-gated sprints)

Copy and fill. Dispatch pattern:

```
cd /c/Users/Admin && HERMES="/c/Users/Admin/AppData/Local/Programs/Python/Python311/Scripts/hermes.exe" && \
"$HERMES" chat --provider custom --model alpha -q "$(cat <task-dir>/prompt.txt)" --yolo --pass-session-id -Q \
  > <task-dir>/dispatch.log 2>&1; echo "EXIT=$?" >> <task-dir>/dispatch.log
```

Resume pattern: same but `--resume <owner-session-id>` with a resume/correction
packet instead of the original prompt, appending to the same dispatch.log with
`EXIT-R<n>=` markers so rounds stay distinguishable.

## prompt.txt (new task)

```
TASK ID: <Sprint>-<Task> - <title> (implementation worker).

Đọc TASK.md đầy đủ tại docs/pm/sessions/<session-dir>/TASK.md trong worktree
<worktree> và thực hiện ĐÚNG từng mục.
BƯỚC 0: đọc TOÀN BỘ C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md
→ in RULES_LOADED; đọc overlay TARGET_PROFILE_2D_SOURCE_LOCKED.md (nếu task
chạm profile contract); worktree guard; MOTIONFORGE_DATABASE_URL phải UNSET.
Write-set chỉ đúng allowlist trong TASK.md.
Kết thúc STATUS: TASK_SUBMITTED rồi STOP.
```

## correction/resume packet (same owner session)

Structure that worked repeatedly:
1. Header: `CORRECTION RESUME — <task-id> (owner session <id>).`
2. What happened: crash/exit state, where exactly they stopped (quote the last
   log line or diff hunk).
3. Verified done-state ON DISK (files + test results YOU measured) so the worker
   doesn't redo or doubt completed work.
4. Numbered findings with exact error messages + root cause + prescribed fix
   (and explicitly which side to fix when migration-vs-ORM parity diverges).
5. Remaining checklist in execution order: focused ×2 → static gates →
   self-audit write-set → LOG append → REPORT.md STATUS: TASK_SUBMITTED → STOP.
6. Write-set unchanged reminder + FORBIDDEN list restated.

## TASK.md packet skeleton (written by manager before dispatch)

- Role line: sole implementation worker for this task; provider/model/reasoning.
- Bước 0 mandatory reads incl. rules file path verbatim.
- Context section: what sibling tasks already delivered (with verification
  status), current alembic head, available backends measured on this machine.
- Outcome numbered list mapped 1:1 to acceptance gates.
- Acceptance gate: binary checks with exact commands. Wording patterns that
  produced first-try passes:
  - Migration budget: "ĐÚNG MỘT migration mới CHỈ nếu thật sự cần; nếu dùng
    được bảng hiện có thì KHÔNG tạo và ghi rõ quyết định trong REPORT".
  - Joint coverage: "N artifacts JOINTLY cover M categories" + require a
    coverage-assert test AND a fail-closed refusal path for partial coverage;
    merged artifacts OK only if manifest declares all covered classes.
  - Immutable history: "persist provenance qua <history-table> — KHÔNG mutate
    row cũ" for any override/correction flow.
  - UI tasks (user standing preference, embed verbatim): dark theme; EVERY
    button has a short Vietnamese helper line directly UNDER it (text-gray-400
    or brighter, min 11px); loading/error/empty states; fabricated fallback
    data forbidden.
  - Machine-state claims phrased as "verify before relying" — a packet claim
    like "media KHÔNG có trên máy" must be re-checkable by the worker, and a
    worker that disproves it transparently is a pass signal.
- Write allowlist: explicit file/dir list — "NGHIÊM".
- FORBIDDEN list restated even if global rules cover it — and grown to name
  every earlier sibling task's owned files in sequential chains.
- End condition: LOG.md append + REPORT.md deliverables table + STATUS:
  TASK_SUBMITTED then STOP.

## Gate matrix per task type (manager-side verify)

- Python code: focused suites ×2 (different basetemps) + ruff + mypy (.py only).
- Frontend: tsc --noEmit EXIT=0 + eslint --max-warnings 0 + Playwright FULL
  spec across all projects (desktop+mobile) — rerun the WHOLE spec after any
  fix; single-test reruns hide order-dependent failures. Non-default ports
  require the matching CORS origins env or meta fetches fail with misleading
  "element(s) not found".
- API-touching: OpenAPI path count additive check against the pre-dispatch
  snapshot (`openapi_paths_before.txt` saved in the task lane).
- Migration-touching: single head via ScriptDirectory.get_heads(), round-trip,
  FK check, ORM parity by constraint-name set-diff, zero-removed difflib proof.
- Measured benchmarks: freeze SHA banner printed BEFORE measurement and
  embedded in results; same-seed runs compared after stripping DECLARED
  non-deterministic fields; real artifacts on disk (media/JSON with concrete
  numbers), never just `"ok": true`.

## Anti-patterns observed

- Prompt too thin ("làm theo TASK.md") without context of sibling verified
  work → worker re-reads everything, wastes turns re-deriving facts manager
  already verified. Always include the verified-context block.
- Resume packet without disk evidence → worker redoes finished work or doubts
  its own earlier output.
- Forgetting to restate FORBIDDEN after a crash resume → drift risk highest
  exactly at recovery time.
