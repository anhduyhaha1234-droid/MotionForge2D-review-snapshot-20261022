# Sprint-exit report & golden structure (proven in S08, 2026-08-16)

## S08-SPRINT_REPORT.md — required sections (Codex sprint-exit review input)

The PM's sprint directive makes these sections mandatory. S08's report passed
manager audit with exactly this shape (docs/pm/sprints/S08-SPRINT_REPORT.md):

1. Header: `Status: SPRINT_SUBMITTED` (never APPROVED), submitted timestamp,
   worktree, branch/base HEAD, base gate (e.g. P00 APPROVED + quality run id).
2. Sprint outcome — one paragraph tying the tasks to the product outcome.
3. Task-by-task table: Task ID | exact Hermes session id | started/finished |
   manager state | corrections count | changed files. Session lineage must
   show every resume/correction round of the SAME session (e.g. T01:
   "first run -> interruption/recovery -> C1 correction").
4. Manager verification results per task: exact independent pytest commands +
   counts + durations (never worker self-reports).
5. Acceptance evidence (sprint level): one bullet per task's contract.
6. Golden metrics table: threshold (fixed pre-run) vs measured, with pointer
   to `golden-metrics.json` and the frozen contract SHA.
7. Migrations: each new revision, down-revision chain, CLI round-trip
   evidence (upgrade -> seed -> downgrade to base -> upgrade, rows preserved).
8. Tests and commands (sprint exit): numbered list of every gate with
   verbatim command + result line.
9. Playwright desktop + mobile evidence: per-task runs + sprint-exit run,
   screenshot paths.
10. Protected-data comparison: channels.json SHA, MAIN DB size, MAIN/S05/S06
    git status counts vs P00 baseline.
11. Incidents — EVERY incident, honestly: what happened, root cause,
    remediation, verification. S08 had 5 (background-delegation kill,
    MAIN-DB migration x2 remediated byte-exact, visual-spec screenshot regen,
    CWD stray cleanup + tracked-file restore).
12. Deviations — contract-level deviations accepted within task scope.
13. Known limitations/risks (e.g. rule-based grouping precision 0.6 with
    reviewer-in-the-loop making durable truth correct).
14. Out-of-scope findings for Codex (product decisions the sprint may not
    make: queued-cancel drain gap, no thumbnail-byte endpoint, extractor
    naming).
15. Recommendation for Codex + End state paragraph (SPRINT_SUBMITTED, no
    commit/push, no S07 started).

## Golden contract recipe (S08-T06 pattern)

1. Write the contract FIRST: case list (same-object-across-scenes,
   similar-different, occlusion, low-confidence, false grouping, required
   merge, required split, source replacement, restart, retry, cancel) and
   thresholds. Freeze a `contract_sha256` over the contract JSON.
2. Dataset is deterministic fixtures only — never user data.
3. Test asserts measured == recorded thresholds; no threshold tuning after
   observing results.
4. Metrics JSON shape (emit to <run-dir>/golden-metrics.json):
   - grouping_precision, grouping_recall (or justified equivalent)
   - proposal_false_merge_rate, executed_false_split_rate
   - post_curation_false_merge_rate, post_curation_false_split_rate
   - review_low_confidence_rate
   - recompute_scope_ratio (affected roles / active roles)
   - runtime per scenario, repeatability (exact vector equality)
   - boolean flags: low_confidence_never_auto_confirmed,
     required_merge_applied, required_split_restored,
     restart_single_effect_set, cancelled_attempt_zero_effects,
     occlusion_occurrence_persisted
5. Keep the pytest golden suite small (S08: 2 tests) and make the suite
   re-runnable with fresh basetemp; env var `S08T06_RUN_ID` (or task
   equivalent) selects the run dir so a bare run can't pollute
   `output/s08-sprint/default/`.

## Sprint-exit manager verification (what the manager itself re-ran in S08)

- Full S08 focused suite (all task suites + golden): 137/137
- S05 41-suite + S06 90-suite shallow basetemp: 131/131
- Golden suite + metrics JSON loaded and compared to the report table
- Fresh 7/7 baseline: read `output/quality-baseline/<run-id>/summary.json`
  directly and print every gate status
- Playwright: interaction specs re-run (`--grep-invert visual`), visual
  validity via mtime check (0 TS files newer than the visual run)
- Protected: certutil SHA channels.json, MAIN DB size, MAIN/S05/S06 counts
