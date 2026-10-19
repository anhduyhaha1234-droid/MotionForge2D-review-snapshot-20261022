# FINISH packet template — worker hit the iteration cap with work on disk

Use when a worker launcher exits `exit=0` but the log ends with
`⚠ Iteration budget reached (160/160)` and the task worktree HEAD is still the
transport/parent commit. Fill every `<...>` from the Manager's OWN measurement
(`git status --porcelain`, run the task's test file, `ls` the evidence dir) —
the resumed agent must spend zero calls rediscovering state.

---

# <TASK-ID> — FINISH (hết budget 160/160; đĩa đã có việc, chưa commit)

**Owner (RESUME):** `<session_id>` · Model pin như cũ · Worktree như cũ.
**TÌNH TRẠNG ĐO ĐƯỢC (Manager):** porcelain: `<M path1 · M path2 · ?? path3>`;
`pytest <tests/.../test_task.py>` = **<N> passed** (Manager tự chạy); evidence dir có
`<raw/ tools/ write_set/ ...>` (thiếu `<REPORT/...>`). **CHƯA commit** (HEAD = `<sha>` transport).

## Việc cần làm (4 bước — đừng mở rộng)

1. **Xác minh nhanh**: `<task test file>` + `tests/product_p1/public_chain` (2 lệnh, ghi rc).
2. **Đóng evidence**: `REPORT.md` (ngắn: làm gì, gate nào, open points) +
   `raw/final_gate.json` + append `commands.jsonl` (UTC, exit) — no new large artifacts.
3. **Commit đúng allowlist**: `<N>` path ở trên với message
   `<TASK-ID>: … (finish pass: commit + evidence closure)`.
   Không add file ngoài allowlist. Không push, không amend.
4. **Terminal**: `TASK_SUBMITTED · QUALITY_ACCEPTED=0 · commit <sha> · không push` + evidence root.

**Không** GPU, không mở scope, không file mới ngoài allowlist.
Budget lượt này: **≤40 tool calls**. In ≤200 ký tự/lệnh.

---

Dispatch (same session, proves the resume, keeps the owner):

```
python.exe -B mfv1_launch_delivery.py <finish-packet> <worktree> <log> <receipt> --resume <session_id>
```

Measured recovery times: 5m46s (first occurrence) and 3m28s (second occurrence) —
the pattern gets faster once the packet is fully pre-measured.
