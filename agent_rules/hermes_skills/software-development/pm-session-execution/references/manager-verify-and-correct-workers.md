# Manager: verifying & correcting incomplete/crashed workers

Companion to `references/manager-liveness-and-worker-process-audit.md` (liveness while running). This file covers AFTER a worker exits: deciding whether it actually finished, proving it independently, and routing corrections back to the true owner session.

## Exit status does not mean completion
- `EXIT != 0` = crashed mid-edit (e.g. EXIT=4 during a test-file rewrite).
- `EXIT=0` ≠ done: `hermes chat` can end normally (turn/context limit) while the worker is mid-patch, before it wrote REPORT.md.
- Treat a task as DONE only when: REPORT.md exists with `STATUS: TASK_SUBMITTED` AND the evidence files it cites exist AND manager-run gates pass.

## Liveness/completion signals, ranked (this host)
1. Log size delta: `stat -c%s dispatch.log` sampled ≥60s apart; frozen size + no SUBMITTED marker = dead or stalled.
2. `EXIT=` / `session_id:` markers in the log — but crashes truncate BEFORE the session id prints; absence proves nothing.
3. NEVER MSYS `ps` PID mapping (known-wrong on this machine). Use wmic cmdline grep or marker/delta methods.

## Owner session discovery when the log lacks the session id
Query the Hermes state DB directly, then disambiguate by first user message:
```
python -c "import sqlite3,time; c=sqlite3.connect(r'C:/Users/Admin/AppData/Local/hermes/state.db'); [print(time.strftime('%H:%M',time.localtime(t)),i) for i,t in c.execute('SELECT id,started_at FROM sessions WHERE started_at>? ORDER BY started_at',(cutoff,))]"
python -c "import sqlite3; c=sqlite3.connect(r'C:/Users/Admin/AppData/Local/hermes/state.db'); print(c.execute('SELECT content FROM messages WHERE session_id=? AND role=\'user\' ORDER BY rowid LIMIT 1',(sid,)).fetchone()[0][:80])"
```
Match the `TASK ID: <task-id>` prefix. Corrections must RESUME that id (`--resume <sid>`), never open a fresh session — otherwise two owners exist and attribution collapses.

## Independent verification recipe (run ALL gates yourself before believing anything)
1. Re-run the worker's focused suites ×2 with isolated basetemp, `env -u MOTIONFORGE_DATABASE_URL`, `-p no:cacheprovider`; record pass counts.
2. Additive-only proof for shared files: difflib.unified_diff against the PRE-EDIT baseline snapshot; count removed lines (must be 0). Requires the writer saved a baseline copy first — make "save `*_baseline_<hash>.py` before first edit" part of every implementation TASK.md.
3. Migrations touched: `ScriptDirectory.get_heads()` single-head assertion + upgrade round-trip.
4. Write-set audit: `find app tests migrations -newermt '<dispatch-time>'` vs the allowlist — catches scope leaks regardless of what the report claims.
5. Read the tail of the worker's reasoning/log to locate exactly where it stopped and what it was about to do — feed this back verbatim in the correction prompt.

## Correction-resume dispatch pattern
Write `correction-r1.txt` in the task's own output lane containing:
- Numbered findings, ROOT-CAUSED BY THE MANAGER first (file:line specifics — e.g. "migration has CHECK x, ORM class missing it → parity fails"; "test seed inserts duplicate PK 'rr1'").
- Explicit keep-list: prior work stays untouched; write-set and forbidden list unchanged.
- Remaining checklist from TASK.md (remaining suites, ruff/mypy, round-trip, REPORT.md format).
Dispatch appended to the SAME log:
```
hermes chat --provider custom --model alpha --resume <owner-sid> -q "$(cat .../correction-r1.txt)" --yolo -Q >> .../dispatch.log 2>&1; echo "EXIT-R1=$?" >> .../dispatch.log
```
After exit: redo the full verification recipe; only then mark the registry row `TASK_MANAGER_VERIFIED`.

## Parallel writers in one worktree: interference is expected
A writer publishing schema/migrations mid-run breaks OTHER writers' fixture-setup suites transiently (real case: 27 failed / 187 errors, every failure inside `alembic upgrade head`, caused by the sibling writer's half-written migration).
Worker-side protocol (encode in TASK packets): attribute failures by WRITE-SET OWNERSHIP before self-blame; bounded wait ≤10 min per cycle; re-probe (upgrade head, table list) after the sibling settles; never revert another writer's files.
Manager-side mitigation: stagger dispatches so the schema-publishing writer lands first, or schedule suite-heavy regression runs after the schema writer reports its migration stable (mtime + probe).

## Acceptance-gate phrasing that produced clean one-shot submissions (S09 sprint, 2026-08-23/24)
How acceptance criteria are WORDED in TASK packets decides whether workers pass gates first try:
- **Migration budget**: "ĐÚNG MỘT migration mới CHỈ nếu thật sự cần; nếu dùng được bảng hiện có thì KHÔNG tạo và ghi rõ quyết định trong REPORT" — T03 correctly reused existing job tables and skipped migration entirely under this wording.
- **Joint coverage**: when N artifacts must collectively cover M categories, say "JOINTLY cover" and require a coverage-assert test plus a fail-closed refusal path for partial coverage (`test_four_loops_jointly_cover_six_risk_classes` + `test_planner_refuses_partial_coverage`). Merging two categories into one artifact is acceptable only if its manifest declares both explicitly.
- **Immutable history**: "persist provenance history qua <history table> — KHÔNG mutate row cũ" so overrides/corrections land as supersede rows with audit lineage, never in-place edits.
- **UI standing preference** (embed verbatim in UI-task packets): dark theme; EVERY button carries a short Vietnamese helper line directly UNDER it (`text-gray-400` or brighter, min 11px); loading/error/empty states required; fabricated fallback data forbidden. At verify time count `grep -c 'text-gray-400'` across new components as concrete evidence — don't accept "UI done".
- **Linter gate matrix is language-scoped**: ruff+mypy for .py only; tsc --noEmit + eslint --max-warnings 0 for frontend. Running ruff on a .ts file yields hundreds of fake "invalid-syntax" errors — discard such a run and note it if it leaked into evidence text.
- **OpenAPI path-count gate**: boot app, `len(app.openapi()['paths'])` + filtered feature list; additive-only = count increased, zero pre-existing paths removed (219→221→229 across T00–T03). Snapshot `openapi_paths_before.txt` into the task output lane BEFORE dispatch so the baseline is pinned, not remembered.

## Manager assumptions are falsifiable — re-prove before accepting either direction
When a worker contradicts a claim in your own TASK packet (real case: packet said reference media "KHÔNG có trên máy"; worker found it under MAIN projects/ read-only), do NOT silently accept or silently revert: run the proof command YOURSELF (chunked sha256 read matched expected prefix → VERIFIED), then update the registry noting both the original wrong assumption and the re-proof. Worker transparency about a packet error is a PASS signal — reward it by correcting the record, not by punishing the deviation.

## Green STATUS line over a red suite — the most common worker-report lie
A worker can exit 0 with `STATUS: TASK_SUBMITTED` while its focused suite is actually RED. Real case (S09-C2): I03-PREP submitted with the harness suite at **8 failed / 21 passed** — it bumped `SCHEMA_VERSION = 3` in the benchmark script but left the fixture `thresholds.json` at version 2, so every subprocess test fail-closed on load. The STATUS line and the log looked clean; only running the suite exposed it.
- ALWAYS run the worker's own focused suite yourself before accepting TASK_SUBMITTED, even when the report cites gate logs.
- Generalize into every PREP/correction packet up front: "bump của bất kỳ SCHEMA_VERSION/policy constant nào phải bump CẢ mọi fixture/data file mang version đó trong cùng một change."
- Root-cause such failures yourself before resuming (file:line + the two diverging values); resume packets that name the exact mismatch get one-shot fixes.

## E2E findings that name a schema-vs-contract contradiction: read the code, then route (S09-C3 endgame)
An acceptance lane exiting `BLOCKED_WITH_FINDINGS` with real production defects is a SUCCESS of the gate, not a round failure — T06B-C3's honest self-block surfaced two defects every earlier green suite had missed:
- **F1**: `RegenerateJobRequest.expect_content_sha256` was a REQUIRED Pydantic field while the written API contract said body = correction_id only (+ pin only when needed). Server-side pinning was already fail-closed, so the required client field was redundant AND blocked the UI with 422. Fix direction: make the field OPTIONAL, keep the existing TOCTOU branch for callers that do send it. Lesson: **when server enforcement and the documented contract disagree, the contract wins**; redundant mandatory client inputs are defects even when they look like "extra safety".
- **F2**: replay returned HTTP 201 + `reused:false` despite an identical job_id — idempotency must be asserted via the `reused` flag/identity match, never inferred from status code.
Routing pattern that worked:
1. Manager personally reads the flagged file:line and confirms root cause BEFORE writing any packet (both findings confirmed in one grep pass).
2. Correction packet cites the authorizing prompt clause for the chosen fix ("§3.2 … KHI SCHEMA HIỆN HÀNH CẦN"), states preferred option + rationale, names the fallback option and which lane it would drag in.
3. Packet demands NEW test cases per defect (no-pin→201 / wrong-pin→409 / replay×2→reused=true) plus focused ×2 rerun.
4. The E2E lane's spec stays FROZEN — it asserted correctly; only resume it for the ×2 rerun after the fix lands. Never let a third session rewrite a good spec.
Also record the diagnostic positives as architecture evidence: same-stack API call with full pin → 201 completed; affected artifact_id AND sha256 changed for real (79461→79333 bytes via the overlap fixture z-order effect); context SHA stable across calls. "The hard part works, fixes are wiring" is exactly what Codex wants to see alongside the finding list.
