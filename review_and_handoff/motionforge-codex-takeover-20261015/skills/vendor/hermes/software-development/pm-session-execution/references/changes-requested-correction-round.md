# CHANGES_REQUESTED → fast-track correction round (S09-C1 pattern, 2026-08-24 night)

Lifecycle lesson from the round after `SPRINT_SUBMITTED`: Codex came back `CHANGES_REQUESTED` with 7 findings (F1–F7) and a full fast-track Manager prompt (`docs/pm/prompts/S09_C1_FAST_TRACK_MANAGER_<date>.md`) authorizing up to 5 parallel owner-resumes, phased write-set expansion (join gates), and prompt-specific terminal states. This reference covers how to RUN such a round; the green-suite gap that CAUSED it is §1.

## 1. Green full-suite ≠ Codex-proof — the four surfaces my final gate never exercised
My final gate ran the complete pytest tree (1760 passed / 0 failed) yet Codex still returned CHANGES_REQUESTED. The findings attacked integration surfaces the suite never touched:
- **Production-app route mounting (F4)**: T05A/T06A tests mounted routers on isolated FastAPI apps, so "OpenAPI additive" checks passed while the ACTUAL `app.api.app` had zero correction/approval paths (frontend got 404s). Final-gate fix: boot the real app and assert feature paths present in `app.openapi()['paths']` — cheap, definitive.
- **Transaction semantics masked by test doubles (F4b)**: `submit_checkpoint` had no commit; the test dependency committed after every request, hiding it. Gate fix: one test through PRODUCTION dependency semantics + fresh-session reload assertion.
- **Schema boundary probes (F5)**: direct Pydantic probes accepted `bogus_from`, anchors `9.0/-2.0`, reversed frames, empty evidence. Gate fix: adversarial payload probes at the HTTP boundary, asserting reject-without-side-effect (row counts unchanged).
- **Environment-sensitive gates (F3)**: a passing test compared worktree source vs `git show HEAD` decoded through ambient subprocess encoding — red with `PYTHONUTF8` unset, green with it set, and coupled to mutable git history. Gate fix: forbid `git show` comparisons in tests; pin `encoding="utf-8", errors="replace"` on subprocess reads; run the encoding slice both with and without `PYTHONUTF8`.
- **Contract-depth checks (F1/F2)**: "tests pass" didn't prove the renderer composited replacement assets vs re-encoding source, nor that benchmarks measured rendered output vs observing input frames. Reviewers diff the IMPLEMENTATION against the outcome statement, not just test results — manager verify must too (read adapter code paths, look for replacement-asset plumbing, not just green counts).
Encode into every final-gate checklist: real-app OpenAPI mount check, production-dependency transaction test, HTTP-boundary adversarial payloads, env-matrix rerun of suspicious gates, and implementation-level reading of any task whose acceptance is behavioral ("composites X") rather than countable.

## 2. Pre-resume owner verification (new mandatory preflight step)
Fast-track prompts name EXACT owner sids to resume (some weeks old). Before any dispatch, verify each one in hermes state.db: row EXISTS **and** first user message matches the expected TASK-ID prefix (`SELECT content FROM messages WHERE session_id=? AND role='user' ORDER BY rowid LIMIT 1`). Real run: 11/11 sids verified in one batch — catches stale/wrong sids in the prompt before wasting a dispatch, and satisfies Rules Mục 4 ownership evidence.

## 3. Lock-table registry for the round
New file `docs/pm/sessions/<SPRINT>-C1-SESSION-REGISTRY.md` (Manager sole writer; workers append only own LOG/REPORT): columns Task ID / exact owner session / phase / proc / state / exclusive write-set / **hashes-before** (12-char sha256 of each hot file) / dependencies. Hashes-before make post-correction diffs attributable. Append-log rows for every dispatch/verify event.

## 4. Correction prompts cite finding IDs, not re-prose
Resume packets say "đọc TOÀN BỘ review <path> (finding F1 P0 + F3 P1)" + prompt-section pointer ("mục 4 của S09_C1_FAST_TRACK…"), then carry ONLY task-specific deltas: exact write-set, binary acceptance, join-gate notes, forbidden list. Keeps worker behavior traceable to the reviewer's words instead of a manager paraphrase that can drift.

## 5. Join gates = phased write-set expansion (J1/J2)
- **J1 contract freeze**: when the core worker finishes public contract + focused contract tests, Manager records SHA-256 of contract/router files in the registry and emits a named marker (`T02_CONTRACT_FROZEN_FOR_I03`). The dependent benchmark worker may then integrate against the FROZEN contract while the core keeps polishing internals/tests. Core changing public contract after freeze requires stopping the dependent and redoing the hash handshake.
- **J2 production-API integration**: the ONLY phase permitted to touch the shared wiring file (`app/api/app.py`) is a dedicated integration phase run by ONE worker (T06A owner) AFTER both sibling corrections reach TASK_MANAGER_VERIFIED and exit. This kills the who-owns-shared-file collision by deferring, not locking.
- **Wave B parallelism**: downstream measured-decision worker ∥ production-stack E2E worker (disjoint output lanes). A third (UI-fix) owner resumes ONLY if the production-stack failure is provably UI-owned; shared frontend files take turns with Manager-issued locks, integration owner default.

## 6. Parallel owner-resume dispatch
Five simultaneous `--resume` dispatches fired cleanly (each log showed `↻ Resumed session …` within ~60s; sizes 389B–15KB at first sample). Dispatch-time serialization NOT required despite the lane's empty-content history — but keep post-dispatch liveness sampling cadence (log-delta + owned-pid) from §silent-death in SKILL.md, since revival ≠ immunity.

## 7. FG-reconciliation discipline when Codex challenges your process (F7)
When the review flags prior correction tasks (FG1/FG2/FG3) as outside the authorized task map: record their EXACT session ids in the new registry, keep their fixes on disk, and mark explicitly "fixes retained pending Codex decision — not retroactively legitimized". Never invent new task IDs mid-round; never quietly fold unauthorized work into the authorized map. Process compliance is reviewed separately from code correctness, and honesty here is what keeps the code fixes reviewable.

## 8. Prompt-defined terminal states
Fast-track rounds may define their OWN terminal vocabulary — real example: `S09-C1 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW` or `S09-C1 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW` (note: BLOCKED_WITH_FINDINGS is not in the standard Mục-11 vocabulary; the round prompt supersedes). Use the round's exact strings verbatim, then STOP — same review boundary as sprint-level SUBMITTED.
