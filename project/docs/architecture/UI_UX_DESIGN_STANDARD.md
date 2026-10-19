# MotionForge2D UI/UX Design Standard

**Status:** Proposed baseline for S04 and all later UI tasks
**Audience:** Product, design, frontend, QA, and Hermes implementation sessions

## Product intent

MotionForge2D is a guided production tool, not a dense non-linear editor. The
default experience must help a first-time Vietnamese user finish useful work
without learning internal engines, codecs, models, or filesystem structure.

The durable project flow has six stages:

1. Nhập video
2. Đối tượng
3. Demo thay thế
4. Áp dụng
5. Kiểm tra
6. Xuất 4K

At any moment, show the current stage, one dominant next action, unmet
prerequisites, and the most recent durable result. Advanced technical settings
remain available through progressive disclosure and must persist when changed.

## Information architecture

- Global navigation: `Trang chủ`, `Kênh`, `Dự án`, `Thư viện nhân vật`.
- Global utilities: durable `Công việc`, system status, and help.
- Project header: project name, source channel, production channel, and save
  state.
- Project navigation: the six-stage rail plus `Dự án / Video / Bước hiện tại`
  context.
- Main area: the current task and its evidence.
- Context inspector: only properties relevant to the current selection.
- Timeline or scene detail: open only when time-precise correction is needed.

## Interaction rules

1. Each screen has at most one visually dominant primary action.
2. A disabled action has a visible reason and a direct way to satisfy its
   blocker.
3. Prefer targeted reruns (`Tạo lại cảnh này`, `Thử lại 2 mục lỗi`) over a full
   recompute.
4. Full apply is unavailable until the demo is explicitly approved. Its
   confirmation names the scope, estimated time/cost, and preserved checkpoint.
5. Long jobs never block navigation. Refresh or restart restores the same
   durable job without duplicate submission.
6. Required instructions and validation errors are visible; they are never
   hidden only inside a tooltip.
7. Destructive actions state the consequence and preserve recoverable data
   whenever the domain contract permits it.

## Button labels and local guidance

Use a verb plus an object and, when material, make the consequence explicit.
Avoid ambiguous primary labels such as `OK`, `Xử lý`, or bare `Tiếp tục`.

Preferred labels include:

- `Tạo dự án`
- `Thêm video`
- `Phân tích video`
- `Tạo demo 3–5 cảnh`
- `Tạo lại cảnh này`
- `Duyệt demo và áp dụng toàn video`
- `Hủy công việc`
- `Thử lại từ bước lỗi`
- `Xuất bản 4K`
- `Lưu trữ kênh`

Every unfamiliar action or concept has concise local guidance. Use visible
supporting text when the information affects task completion. Use a tooltip for
optional clarification only, limited to two short sentences, available on both
focus and hover, dismissible with Escape, hoverable, and persistent while used.

Examples:

- `Kênh nguồn: nơi chứa video gốc.`
- `Kênh sản xuất: nơi nhận phiên bản đã xử lý.`
- `Demo: 3–5 cảnh đại diện để kiểm tra trước khi chạy toàn video.`
- `Proxy: bản nhẹ để xem nhanh; không làm giảm chất lượng file xuất.`
- `Độ tin cậy thấp: hệ thống chưa chắc các vùng này thuộc cùng một đối tượng.`

Archive confirmation copy:

> Kênh sẽ ẩn khỏi danh sách đang hoạt động. Dự án cũ vẫn giữ liên kết.

## Required states

- **Empty:** explain what will appear, show one next action, optionally show an
  example.
- **Initial loading:** use a skeleton matching the resulting layout; do not show
  invented progress.
- **Refreshing:** retain stale usable content and label the refresh.
- **Long job:** show state, completed/current/next step, real progress only,
  elapsed time, clearly labelled ETA estimate, background behavior, and allowed
  cancel/retry actions.
- **Success:** show output evidence and the next action.
- **Recoverable error:** identify the cause and affected item, say what work was
  preserved, and provide an exact recovery action.
- **Partial failure:** show succeeded and failed counts and retry only failed
  items where supported.
- **Offline/restart:** show reconnection state and rehydrate durable work.

## Accessibility baseline

Target WCAG 2.2 AA for core flows:

- Complete keyboard operation with logical focus order and no keyboard traps.
- Deterministic focus placement and restoration around dialogs.
- Visible focus and UI component contrast of at least 3:1; normal text contrast
  of at least 4.5:1.
- Controls at least 24 by 24 CSS pixels, preferably 44 by 44 for primary touch
  targets.
- Labels accompany icons; state is never represented by color alone.
- Support reduced motion and retain all function at 200% zoom.
- Announce ordinary job changes with `role="status"`; reserve `role="alert"`
  for urgent errors. Progress bars expose an accessible name and value.
- Form help and errors are programmatically associated with their fields.

## Acceptance criteria for S04 and later UI tasks

1. A first-time user can select or create channels, create a project, add a
   Video Item, and identify the next action without documentation or filesystem
   navigation.
2. Refresh, restart, and browser Back preserve project/video context and the
   current stage without duplicate work.
3. The basic happy path exposes no provider, codec, GPU, or threshold controls;
   these remain available under labelled advanced settings.
4. Job Center represents every durable job state and its affected project/video,
   with cancel/retry only when the contract permits it.
5. Lists have distinct empty, loading, refreshing, partial-data, and error
   presentations.
6. Conflict and stale-revision errors preserve entered values and move or link
   focus to the affected control.
7. Automated accessibility checks have no critical violations, followed by a
   manual keyboard and screen-reader smoke test of the core flow.
8. Automated copy checks reject ambiguous primary action labels and require
   descriptive text for destructive consequences.
9. Demo comparison supports original/result plus split, wipe, or blink; it is
   keyboard operable and exposes scene/timecode and original-audio state.
10. Before S04 exit, usability evidence records representative users attempting
    the management scenario, observed failures, and resulting iterations.

## Research basis

Observed product patterns informed this standard; MotionForge2D-specific rules
above are product inferences rather than claims made by those products.

- [Adobe Premiere: change, create, and reset workspaces](https://helpx.adobe.com/premiere/desktop/get-started/tour-the-workspace/change-create-reset-workspaces.html)
- [Descript: Scenes overview](https://help.descript.com/hc/en-us/articles/10248939749517-Scenes-overview)
- [Descript: Timeline overview](https://help.descript.com/hc/en-us/articles/10249275208717-Timeline-overview)
- [Descript: Export and publishing](https://help.descript.com/hc/en-us/articles/10255819601037-Export-and-publishing-overview)
- [Runway: Introduction to Workflows](https://help.runwayml.com/hc/en-us/articles/45763528999699-Introduction-to-Workflows)
- [Runway: generation progress and stuck jobs](https://help.runwayml.com/hc/en-us/articles/32881061675795-Why-is-my-generation-stuck)
- [Adobe Premiere EncoderManager events](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/encodermanager)
- [Canva accessibility](https://www.canva.com/accessibility/)
- [W3C accessibility principles](https://www.w3.org/WAI/fundamentals/accessibility-principles/)
- [W3C focus order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html)
- [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages)
- [W3C content on hover or focus](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus)
