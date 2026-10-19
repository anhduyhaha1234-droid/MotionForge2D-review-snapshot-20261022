# A02-T02 authority gate + flaky-test triage (verified 2026-08-20, S08-A02 cycle)

Manager cycle that opened S08-A02-T02 (Extraction Evidence and Artifact Wiring) after
A02-T01 C4 hygiene. Two reusable lessons: (1) where follow-on-task authority actually lives, and
(2) how to triage a test that passes alone but flakes in the combined suite.

## 1. Authority discovery for a follow-on task not in ROADMAP/sprint contracts

The task ID was referenced by prior TASK.md ("contract that S08-A02-T02 will use as its single
durable truth") but had NO entry in `docs/pm/ROADMAP.md`, `S08-SPRINT_CONTRACT.md` or
`S08-SPRINT_REPORT.md` (those only list S08-T01..T06). The authoritative spec was NOT in the PM
tree — it lived in planning artifacts:

- `output/overnight-planning/S08-A02-T02-DRAFT.md` (goal, scope/out-of-scope, allowlist,
  generation rules, 10 AC, test matrix)
- `output/s08-a02-t01-r1-c1/ro2-t02-planning.md` (221-line read-only plan: mapping contract,
  mask lifecycle, motion, edges, generation authority, file overlap map, 10 binary AC, test plan)
- Only-line references: `docs/pm/sessions/S08-A02-scene-structural-evidence-bridge/TASK.md:11,25`
  and `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`

Drill pattern:
1. `grep -rn "<TASK-ID>\|<concept...>" docs/ output/ --include=*.md` (task ID + producer/consumer/
   renderer bridge / correction bridge / generation-scoped evidence).
2. Distinguish real authority from "do not open" boilerplate (many files mention the ID purely as
   FORBIDDEN); read the planning docs and cross-check the allowlist filenames against HEAD
   (`ls`/`test -f` each allowlisted path + grep the quoted handler symbols exist, e.g.
   `_publish_effect`, `_extract_phase`, `DeterministicExtractionProvider`).
3. Write TASK.md with an explicit **Authority map table** — every requirement row cites
   `file:line` provenance (requirements from RO-2 §N / DRAFT §N / persistence line numbers).
4. Gate dispatch on 8 aspects: outcome · producer/consumer · API/domain contract · write allowlist ·
   out-of-scope · binary acceptance criteria · migration policy · test plan.
   - All present → build packet (TASK/START_PROMPT/LOG/REPORT) + dispatch ONE Muse writer.
   - Any missing → discovery report + `BLOCKED_A02_T02_SCOPE` + exactly ONE question to user;
     never invent scope.

A02-T02 example outcome: full wiring of `occurrence_segment` / `segment_motion` /
`scene_graph_occlusion` / `scene_graph_contact` inside `_publish_effect` transaction, mask
lifecycle, deterministic QA adapters emitting edges, completed-only read API; 10/10 AC met,
single migration head `a0b1c2d3e4f5` (no new migration).

## 2. Flaky statement-count test in the combined suite (order-sensitive)

Symptom: `test_c4_multi_video_no_nplus1` passed alone 10/10 and in its own file, but failed
~1/12 inside the FULL 12-file combined suite. Assertion: SQLAlchemy statement counter
`event.listen(engine, "before_cursor_execute")` counting calls to `list_historical_segments`
with `assert counter <= 10` (batch expected ~7 statements; legacy N+1 was ~16 for 13 videos).

Recovery sequence that pinned it:
1. Re-run the single test alone → PASS (10/10). Not a deterministic regression.
2. Re-run the full combined → interleaved PASS/FAIL (303+1fail, 304, 304).
3. Re-run extraction suites FIRST then the c3 file → reproduced 1/4, then 0/N — order + timing
   dependent. Never accept "passes alone" as sufficient.
4. Root cause (hypothesis, statistically consistent): the test wraps setup in
   `contextlib.suppress(Exception): _advance_generation(...)`. When that call fails under load,
   the SQLAlchemy session is left in pending-rollback; the next measured call emits extra
   ROLLBACK/BEGIN statements, tipping the strict `<=10` counter over the bound → false "N+1".

Manager rule when the flaky test is OUT of the current task's allowlist (C4 test inside a T02
cycle): do NOT silently expand scope to edit it. Choices to offer user: (a) patch the flaky test
in ITS OWN scope (C4) then re-verify both; (b) accept as known-limitation, record root-cause
hypothesis + occurrence rate in REPORT/MANAGER_STATE for Codex; (c) dispatch a small Muse writer
in that scope. If it IS in scope, harden it: narrow the broad except, and set the counter bound
to a value still BELOW the real legacy N+1 count (e.g. 12-13 for 13 videos), not 10.

## 3. Inline noqa triage (complement to "grep file-level noqa")

After a writer pass, grep `noqa: <RULE>` counts and judge by code, not by total:

- PLC0415 local imports (`import torch`, `import sam2...`) + BLE001 `except Exception` capability
  probes + F401 deferred optional imports → pre-existing deliberate provider pattern, fine.
- E501 on long deterministic f-string ids → formatting noise, fine.
- RED FLAG = whole-file `# ruff: noqa:` header line (`grep -n "^# ruff: noqa" file`). Reject and
  require real wrapping / narrow inline noqa with justification.

Also verify "no new migration" claims with hashes: after the wiring task, confirm
`migrations/versions/*` and `app/persistence/models.py` hashes are UNCHANGED, not just that
`alembic heads` prints one line.
