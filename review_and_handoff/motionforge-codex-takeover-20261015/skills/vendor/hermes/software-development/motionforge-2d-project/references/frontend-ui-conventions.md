# MotionForge2D frontend/UI task conventions (standing user preference)

Applies to ANY task whose write-set touches `frontend/**` (first measured use: **MF-END-10** "UI kho nhân vật
và chọn bộ series", 2026-09-28, inside the 28-task Phase-B delivery wave). These are the user's own rules —
they complained **twice** about violations, so treat them as hard acceptance criteria in the launch packet,
not as style suggestions.

## 1. The rules (non-negotiable)

1. **Every dark-theme control** (button, toggle, select) has a SHORT **Vietnamese** helper text directly
   **UNDER** the control.
2. Helper text colour: **`text-gray-400` or BRIGHTER**. `text-gray-500` is unreadable on `gray-900`
   (explicit user complaint).
3. Helper text size: **≥ 11px** (explicit user complaint #2).
4. **All user-facing strings in Vietnamese** — labels, errors, empty-states, tooltips.
5. **No hard-coded hex colours** off the existing `frontend/` palette — reuse existing components/tokens.
6. The UI calls the **real endpoints already in the tree** (for cast/library work: MF-END-06 recommendation,
   MF-END-07 confirm, MF-END-09 asset-job APIs) — never invent a route inside the UI layer.

## 2. Packet block to embed VERBATIM in every UI dispatch

```
## UI CONVENTIONS (BẮT BUỘC — user đã phàn nàn 2 lần)

* Mỗi nút/điều khiển dark-theme phải có helper text tiếng Việt ngắn NGAY DƯỚI nút:
  màu `text-gray-400` hoặc sáng hơn (gray-500 KHÔNG đọc được trên gray-900), cỡ ≥ 11px.
* Mọi chuỗi UI cho người dùng: tiếng Việt. Không hardcode hex màu lệch palette hiện có của `frontend/`.
```

Put it in the launch packet's own section (this session's MF-END-10 packet did), not in a side note — the
worker reads the packet, not your chat.

## 3. Verification after a UI task lands

- Same allowlist / porcelain / independent-test verification as any task
  (`git show --stat HEAD` inside the write-set; `git status --porcelain` == 0; re-run the task's own test file).
- A clean pytest run says nothing about the `.tsx` files: if the repo has a frontend build/lint script, run it
  yourself and record the count; otherwise say explicitly in the ledger row that no FE build was run.
- A visual check is optional — if you did not look at the rendered UI, the verdict stays
  `NOT_VISUALLY_APPROVED` (never implicitly approved). Point the reviewer at the exact files/controls to eyeball.
