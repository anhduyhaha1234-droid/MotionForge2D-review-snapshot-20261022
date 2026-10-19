# Empty-content deaths at session start — shrink the resume packet, don't resend the fat prompt (2026-08-24 midday, T06B)

A fifth death signature appeared on the FINAL task of S09: worker exits almost immediately (log 11KB), tail shows `⚠️ No reply: the model returned empty content after retries and any fallback providers` right after a batch-read plan ("Let me read the routes file and global setup first"). The R1 resume then died THE SAME WAY at 34KB — again empty-content, again mid-batch-read.

## Distinguishing features vs earlier death modes
- Router `/v1/models` stayed 200 throughout; a direct `/v1/chat/completions` probe may even return an auth error without credentials — neither proves the chat path is healthy for long reasoning turns. Treat router health checks as necessary-not-sufficient.
- Deaths clustered during large batched reads early in a resumed turn of a BIG session → suspicion: oversized context assembly on resume (the resumed session re-ingests its whole history plus the new packet).
- Wrapper still appends `EXIT-R1=0` — so unlike silent wave-death, there IS a marker; the model simply produced nothing.

## What worked (R2)
Stop resending the original full TASK prompt; send a SHORT reorientation packet instead:
```
Tiếp tục đúng chỗ dở: bạn đang batch-read X/Y/Z.
Sau đó làm phần còn lại theo TASK.md <path>: <one-line deliverable summary>.
Write-set đúng allowlist. Kết thúc STATUS: TASK_SUBMITTED rồi STOP.
```
Log grew immediately (+16KB within 75s) and the worker progressed into real analysis of approval semantics.

## Rule of thumb
After two consecutive empty-content deaths on the same session, shrink the resume packet to a pointer at TASK.md plus a two-line where-were-you recap. The session history already carries the details; the packet only needs to restart the loop, not repeat it.

Keep marker discipline across all attempts in ONE dispatch.log (`EXIT=`, `EXIT-R1=`, `EXIT-R2=` …) and record each attempt's proc id + death evidence in the registry row so Codex sees the full attempt chain.

## Zero-footprint resume death — an attempt can die before ANYTHING hits the log (2026-08-24 afternoon, T06B R3)
A later resume attempt (R3) died so early that dispatch.log showed ZERO trace of it: no `↻ Resumed session …` banner, no reasoning text, no `EXIT-R3=` marker — byte-frozen at the previous attempt's size, owned PID gone. Evidence the attempt ever existed lives only in Hermes' own background-proc list (`proc_e4c6624ecf01` completed) and the notify-on-complete ping.
- Detection rule: after dispatching ANY resume, require within ~60–90s EITHER fresh log growth OR at minimum the `↻ Resumed session` banner line. Both absent + owned-PID rows zero ⇒ the attempt never started — re-dispatch immediately. Do NOT enter the 5-minute RUNNING_RETRY_WAIT: there is nothing mid-flight to protect.
- Marker discipline caveat this exposes: a missing `EXIT-R<n>=` at EOF can now mean "attempt died pre-write", not only "still running". Distinguish via owned-PID + banner check, never via marker absence alone.
- Counter at 3+ consecutive failed starts on one session: the resumed session may have grown too large for reliable context assembly at all. Options beyond blind retry: dispatch a FRESH owner session as recovery (per rules §8, allowed when owner context is effectively unrecoverable — document the process audit + reason), or split the remaining deliverables into smaller sequential packets.

## Empty-content recurs MID-WORK too — bank progress incrementally (same evening)
The short-packet restart reliably fixes session-START deaths, but empty-content returned later inside long generation stretches (R2 died mid-JSX while writing ApprovalPanel overrides rendering — third empty-content overall). Short packet ≠ immunity for the whole turn.
- Add to every resume packet on an unstable route: "Làm tuần tự, mỗi bước ghi LOG.md/log ngay để không mất tiến độ khi model trả empty" — incremental banking means each surviving stretch persists its output to disk before the next risky stretch.
- Between resumes, re-derive the stop point from DISK (files written, spec/config presence, log tail), never from your memory of the last packet — real case: between R2 and R3 the worker had finished ApprovalPanel.tsx entirely (footer with one-way-approval notice present); the R4 packet therefore skipped straight to E2E/gates/REPORT.

## Endgame validation — the pattern held through sprint close (2026-08-24 evening, T06B + FG2/FG3)
The pointer-packet + incremental-banking discipline carried the worst lane of the night to completion:
- FG2's resume-r1 enumerated EXACT remaining failures (file:line, "keep revision-identity literal" vs "switch head-position assert to live `ScriptDirectory.get_heads()`", named the already-passing sibling file as copy-template, banned hard-coding the NEW head string) → worker returned 18 passed ×2, zero `b3c4d5e6f7a9` occurrences in tests, ≥1 `get_heads` per file.
- FG3 (bootstrap expected-tables + two more stale-HEAD files) followed the same narrow-packet shape: 61 passed ×2 first try.
- Sprint closed the same evening: full regression run 3 = **1760 passed / 0 failed / 19 skipped EXIT=0** (27:59, backgrounded), terminal state written via patch-tool anchor-append into SPRINT_REPORT.md at 20:45+07.
Cost accounting for ETAs on an unstable evening: 3 FG2 attempts (~15–20 min each incl. verify), 4 T06B attempts — budget honestly rather than promising a flat timeline.
- When UI deliverable exists but gates don't: manager can run the language-scoped gates itself (tsc/eslint for .ts, pytest suites) while waiting, so the eventual resume packet shrinks to exactly what remains.

## C2 round reuse — pointer packets survive across correction ROUNDS too (2026-08-25 morning, S09-C2 Wave A)

The same packet-shape discipline carried into the next authorized round (C2) after C1 came back CHANGES_REQUESTED:
- Every Wave-A dispatch prompt for C2 was a POINTER packet: "Đọc TOÀN BỘ review C1 <path> (F<n>) + prompt gốc S09_C2… mục <k>. Bước 0: đọc TOÀN BỘ rules → RULES_LOADED." followed by a numbered BẮT BUỘC SỬA list mapping each finding to concrete file-level fixes, then binary acceptance, write-set, FORBIDDEN list. The long policy lives in the round prompt + review record; the dispatch prompt stays a finding-map.
- PREP-phase packets now end at an explicit non-terminal status: `STATUS: PHASE=WAITING_JOIN / PENDING_<X>_BINDING` (T03-C2) or `CORRECTION_SUBMITTED_C2` (T04-C2) — reserving TASK_SUBMITTED for the final binding run after I05-C2 lands. Manager verifies each phase independently anyway (T03-C2: 15 passed ×2 within ~5 min of exit).
- BA pre-chots arrive IN the round prompt under "không hỏi lại scope" (required classes, evidence-path rules, artifact-hygiene bans). Copy them VERBATIM into each affected worker packet rather than paraphrasing — they are constraints, not suggestions. Full record: `references/s09-c2-correction-round.md`.
