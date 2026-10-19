---
name: bom-weekly-work-report
description: Convert task notes into a polished weekly report.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: work
    tags: [report, operations, vietnamese]
---

# bom-weekly-work-report

## When to Use

- The user provides rough work notes, statuses, blockers, or plans for a weekly report.
- A professional Vietnamese operational report is required.

## Required Inputs

- Task list and status.
- Reporting period.
- Completed, in-progress, delayed, and next-period items.
- Names, contract codes, shipment dates, and amounts exactly as supplied.

## Procedure

1. Group notes into completed work, ongoing work, blockers, and next actions.
2. Normalize status language without changing factual completion state.
3. Preserve codes, dates, quantities, supplier names, and document names exactly.
4. Remove repetition and convert fragments into concise professional Vietnamese.
5. Use measurable progress wording and name the owner or dependency when known.
6. Flag missing information instead of filling it in.

## Decision Rules

- Use “tiến độ công việc đang phù hợp với tiến độ đã đặt ra” for on-track incomplete work when appropriate.
- Do not mark an item complete merely because work started.
- Avoid unnecessary English terms when a clear Vietnamese equivalent exists.
- Do not omit unresolved original-document follow-up or supplier dependency.

## Pitfalls

- Turning ongoing tasks into completed tasks.
- Changing contract or shipment codes.
- Using vague phrases such as “đã xử lý” without the actual result.
- Repeating the same task in several sections.

## Verification

- Every source note appears once in the correct status group.
- Codes, dates, and amounts match the input.
- Completion wording matches reality.
- The report is concise and readable.

## Output Format

- Công việc đã hoàn thành.
- Công việc đang triển khai.
- Vướng mắc và nguyên nhân.
- Kế hoạch tiếp theo.
