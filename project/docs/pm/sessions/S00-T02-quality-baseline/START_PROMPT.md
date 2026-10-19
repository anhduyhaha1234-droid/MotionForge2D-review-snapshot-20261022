# Start Prompt for Hermes - S00-T02

Gửi nguyên văn phần trong code block vào một chat Hermes mới:

```text
Bạn đang thực hiện đúng MỘT coding session cho MotionForge 2D.

SESSION_PATH: docs/pm/sessions/S00-T02-quality-baseline
TASK_ID: S00-T02

Quy trình bắt buộc:
1. Đọc đầy đủ theo thứ tự:
   - docs/pm/SESSION_PROTOCOL.md
   - docs/pm/sessions/S00-T02-quality-baseline/TASK.md
   - mọi file trong Required reading của TASK.md.
   Không đọc lan sang milestone/performance docs cũ.
2. Chạy `git status --short`; bảo vệ mọi user changes và output của S00-T01.
3. Xác nhận trong chat: outcome, allowed/forbidden scope, 7 quality gates, validation commands và plan tối đa 7 bước.
4. Chỉ xây quality baseline runner/report. Không sửa bất kỳ lint/type/build/test failure hoặc warning nào; những failure đó là dữ liệu baseline.
5. Chỉ sửa đúng Allowed write scope. Generated artifacts chỉ ghi dưới `output/quality-baseline/`.
6. Cập nhật LOG.md append-only trong quá trình làm.
7. Chạy runner hai lần. Runner phải tiếp tục qua đủ 7 gate dù gate trước fail và phải trả non-zero nếu required gate fail.
8. Điền REPORT.md với exact exit code/status/duration của từng gate ở cả hai runs, chuyển report thành SUBMITTED rồi dừng.
9. Không tự sửa PM_REVIEW.md, không tự ghi APPROVED, không commit/push và không bắt đầu S00-T03.

Rules quan trọng:
- Không sửa `app/`, `tests/`, `frontend/src/`, pyproject, package.json hoặc lockfile.
- Không auto-install dependencies.
- Không chạy GPU/SAM2/integration/E2E.
- Không hard-code absolute machine path vào tracked files.
- Không che failure hoặc biến gate required thành optional.
- Không dừng session chỉ vì runner trả non-zero; hãy kiểm tra report đã đủ 7 gate.

Nếu cần mở write scope, sửa source/dependency, bỏ một gate hoặc build/test đụng production data: ghi BLOCKED trong REPORT.md, append LOG.md và hỏi đúng một câu hỏi tối thiểu.

Definition of done duy nhất: AC1-AC7 trong TASK.md có evidence.
```
