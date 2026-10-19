# Subtask Sprint Slice — Registry + Packet Templates (copy & modify)

Part of `worker-orchestration`. Use when a parent task is decomposed into
formal subtask IDs, each with its own owning worker session (S11-T01A/B/C/D
pattern, verified 2026-08-21).

## 1. Session registry (`docs/pm/sessions/<SPRINT>-SESSION_REGISTRY.md`)

```markdown
# <SPRINT> SESSION REGISTRY (Manager-maintained)

Model chuẩn lane (directive <date time+07>): `<model>` @ provider `<provider>`, reasoning max, fallback disabled.
Baseline HEAD: <sha> — branch <branch>.

| Task ID | Role | Session ID | Process | Model | State | Exclusive files | Dependency | Last heartbeat (+07) |
|---|---|---|---|---|---|---|---|---|
| <SPRINT>-T01A | production writer | <hermes-session-id> | <proc_id> | <model>@<provider>, max, no-fallback | RUNNING | <files...> | none (Wave 1) | <time> |
| <SPRINT>-T01C | production writer | — (chưa tạo) | — | <model>@<provider>, max, no-fallback | BLOCKED_ON_T01B | <files...> | T01B MANAGER_VERIFIED | — |
| <SPRINT>-RO1 | read-only reviewer | — (chưa tạo) | — | <model>@<provider>, max | PLANNED | output/<sprint>-readonly-review/<run>/ only | sau khi có code | — |

## Rules
- Mỗi Task ID đúng một owning session; correction = resume đúng session đó
  (`hermes chat --resume <id> --provider <p> --model <m> -q ... --yolo`).
- Recovery chỉ khi owning session chết/không resume được; ghi reason + last
  confirmed hash/test trước.
- Không reuse BA/reviewer session làm writer; không đụng lane sprint khác.
- Baseline hashes tại dispatch: <file=sha256, ...> (allowlist + locked files).
```

States: PLANNED READY RUNNING SUBMITTED CORRECTION_REQUIRED MANAGER_VERIFIED
BLOCKED_SCOPE BLOCKED_MODEL_ROUTE.

## 2. Per-subtask TASK.md skeleton (`docs/pm/sessions/<SPRINT>-T01X-<slug>/TASK.md`)

```markdown
# <SPRINT>-T01X — <Name>

**Task ID:** <SPRINT>-T01X
**State:** READY
**Owning session:** (điền bởi Manager khi launch)
**Worktree:** <path> — branch <branch> @ <sha>

## Outcome
<1-3 câu: deliverable là gì, không phải là gì>

## Exclusive write ownership
| File | Phạm vi |
|---|---|
| app/services/<x>.py | NEW / CHỈ <behavior> |
| tests/test_<x>.py | NEW / CHỈ <regressions> |
| docs/pm/sessions/<SPRINT>-T01X-<slug>/ | packet/evidence |
| output/<sprint>-t01x/<run-id>/ | logs, test output |

## Forbidden
<sibling test files, shared core, migrations, models.py, API/frontend, lane khác>.
Ngoài allowlist → STOP BLOCKED_SCOPE.

## Required tests (binary)
1. <assertion có thể pass/fail> ... (map 1:1 tới AC)

## Worker protocol
- Hard worktree guard trước mọi write; sai tree → BLOCKED WRONG_WORKTREE, exit.
- Cấm reset/clean/stash/restore/checkout file/commit/push/merge; MAIN; production
  DB; git global config.
- Tests: temp DB + --basetemp Windows-native riêng + -p no:cacheprovider.
- Viết file mới lớn theo chunk ≤200 dòng mỗi lần write_file (tránh response
  truncation finish_reason='length').
- Kết thúc: điền Owning session ID vào TASK.md, REPORT.md status=SUBMITTED,
  evidence lệnh+output thật vào LOG.md. KHÔNG tự ghi APPROVED.
- Model: <model> @ <provider>, reasoning max, fallback disabled. Route chết →
  BLOCKED_MODEL_ROUTE vào LOG.
```

## 3. Dispatch command (one owning writer)

```bash
cd <worktree> && mkdir -p output/<sprint>-t01x && hermes chat --provider <p> \
  --model <m> -q "TASK: Bạn là owning production writer của <SPRINT>-T01X. \
Đọc TOÀN BỘ theo thứ tự: (1) docs/pm/sessions/<SPRINT>-T01X-<slug>/TASK.md, \
(2) .../LOG.md, (3) docs/pm/sprints/<SPRINT>-SPRINT_CONTRACT.md, rồi <các file code>. \
<guard + allowlist + forbidden + required tests + close-out, rút từ TASK.md>" \
  --yolo --pass-session-id --max-turns 300 --source tool 2>&1 | tee output/<sprint>-t01x/<ts>_writer.log
```

Launch with `terminal(background=true, notify_on_complete=true)`. Immediately
after, bind session ID via state.db first-user-message match (SKILL.md pitfall 26).
