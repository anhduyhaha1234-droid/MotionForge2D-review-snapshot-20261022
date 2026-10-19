# HERMES PROMPT — S11-C3 Exact Identity + Restart Proof + Fail-Fast Exit

Bạn là **Hermes Manager mới, context gọn** cho correction sprint hữu hạn
`S11-C3` của MotionForge2D. Bắt đầu thực thi ngay; không chỉ trả kế hoạch.

## 0. Mandatory authority load

Trước preflight hoặc dispatch, đọc TOÀN BỘ:

1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
2. `C:\Users\Admin\MotionForge2D\AGENTS.md`
3. `C:\Users\Admin\MotionForge2D\frontend\AGENTS.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C1_PM_REREVIEW_2026-09-04.md`
8. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C2_PM_REREVIEW_2026-09-04.md`
9. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S11_C2_COMPLETION_AUTHORITY_TARGETED_RESTART_OWNER_EXIT_MANAGER_2026-09-04.md`
10. Toàn bộ C2 registry/exit/raw gate, exact T03G/T06C/T05A/INT01
    LOG/REPORT, current source/tests và task-branch tips.

Báo `RULES_LOADED` kèm path, SHA-256, số dòng, local/remote/task tips và tóm
tắt authority. Rules canonical thắng prompt/report cũ.

## 1. Verdict, boundary và pinned truth

`AUTHORIZED_TO_DISPATCH` chỉ cho `S11-C3` trong prompt này.

- `S11-C2 = CHANGES_REQUESTED / NOT_APPROVED`.
- Whole `S11 = NOT_CLOSED`; không mở/làm S12 hoặc S13.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Canonical branch: `codex/s11-integration`.
- Expected clean local/remote HEAD vào vòng:
  `7474eb7af412fa1a1148f03f3786d1b2728566d9`.
- T03G task branch/worktree is clean at unmerged follow-on
  `e7e9242d862001ae89c852d91e2c6587da4ceeb4`.
- T06C task tip: `6e7eedfd6bd9caa3f85e48b4becefb028b18a16e`.
- T05A real-owner tip: `caf8dcf1948c55a263252b3caff3628da207093e`.
- C2 tests are green for covered paths; do not discard or rewrite their
  history. C3 fixes only the finite residuals below.

Terminal green claim is only:

`S11-C3 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Hermes/Manager never writes `APPROVED`, `CLOSED` or opens S12/S13.

## 2. Manager/session/model policy

- Use a **new compact Manager session**; retire the C2 Manager.
- One Task ID retains one exact owner. Corrections resume exact sessions:
  - T03G: `20260903_170546_0d42f6`, worktree
    `C:\Users\Admin\MotionForge2D-worktrees\s11-t03g-0903w8`;
  - T06C: `20260903_223530_b90853`, worktree
    `C:\Users\Admin\MotionForge2D-worktrees\s11-t06c-0903w14`;
  - T04B conditional: `20260903_183246_706d31`;
  - T05A conditional real owner only: `20260903_203404_4a4548`;
  - INT01 Git-only: `20260903_112116_35051c`.
- Every dispatched/resumed worker turn must explicitly use custom 9Router model
  `cmc/muse-spark-1.3-contributor`, requested reasoning `max`, fallback
  **OFF**, TTFB timeout 900 seconds.
- Record durable `session_model_usage` before/after each new turn. A 429/502/
  `FreeUsageLimitError` may be retried boundedly on the same exact route; it is
  not permission to switch to `meta`, another CMC alias/model, DeepSeek or any
  fallback. If the
  exact route remains unavailable, stop `BLOCKED_MODEL_ROUTE` with evidence.
- T03G/T06C contexts are long. Give each one compact current-byte findings and
  one bounded guarded correction turn. Unsafe overwrite, scope miss or context
  failure => stop `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`; do not
  fabricate a fresh owner.

## 3. Preflight and byte safety

Before any writer:

1. Prove canonical local == remote == `7474eb7` and porcelain empty.
2. Prove all task worktrees above are clean and exact tips match.
3. Prove zero old writer/pytest/product/ffmpeg/watchdog/cron/heartbeat; do not
   create a background watchdog. Use bounded native monitoring only.
4. Query Hermes DB read-only (`mode=ro&immutable=1`) for exact ownership and
   model baseline. Never copy/modify the live DB for authority claims.
5. Create new evidence root
   `C:\Users\Admin\MotionForge2D-evidence\s11-c3\<run-id>\**`; never append to
   or overwrite S11-C2 evidence.
6. Capture SHA-256/bytes/lines/status for every allowed existing file with
   `write_set_guard.py`; pin destructive-shrink thresholds.
7. Workers may modify existing files only by bounded preimage patch. No
   whole-file write, redirection, copy/move-overwrite or reconstruction.

Any mismatch is terminal preflight blocker; do not “repair” it as Manager.

## 4. Wave C3-A — maximum two safe parallel lanes

Dispatch only after preflight is green. The two task worktrees/write sets and
evidence/temp roots are disjoint.

### C3-A1 — T03G exact authority identity

Resume exact T03G at clean tip `e7e9242`. Allowed write set:

- `app/persistence/qc_check_runs.py`
- `tests/test_s11_t03g_qc_check_job.py`
- `tests/test_s11_t03g_qc_check_api.py`
- `docs/pm/sessions/S11-T03G/**`
- new external S11-C3 evidence only.

Read-only: `app/workflow/qc_checks_handler.py`, registry/threshold/source models,
T05A/T06C and every migration/frontend file. The producer already writes the
needed identity fields; do not broaden production scope unless an executable
RED proves otherwise, then stop `NEEDS_SCOPE_DECISION`.

Preserve every green C2 invariant (unbounded newest-full selection, exact
counts/flags/detector set, zero-item/blocker behavior). Close these exact rows:

1. Manifest `schema_version` is PRESENT exact JSON integer and equals
   `RUN_QC_SCHEMA_VERSION`; missing/null/bool/string/wrong integer fails closed.
2. Manifest `policy_id` and `policy_content_hash` equal current server policy.
   Completion values equal both manifest and current policy.
3. Manifest evidence fingerprint equals current evidence. Completion evidence
   fingerprint equals both manifest and current evidence.
4. Manifest `source_generation` is a non-empty string equal to the Job's
   durable `input_generation`; completion generation equals both. Recompute
   current evidence using that exact generation so generation and fingerprint
   cannot contradict one another.
5. Manifest source artifact ID/SHA equal the current persisted source identity.
   Completion `source_artifact_id` and `source_artifact_fingerprint` equal the
   corresponding manifest/current ID and SHA. Handle the legitimate no-source
   representation exactly as the producer writes it; no `or ""` laundering.
6. Completion detector revision key/value map equals the exact server-owned
   `detector_revisions(full_coverage_detectors())`, not merely non-empty values.
7. Completion scope/schema/job/count/flags/detectors continue to match the
   manifest/current full authority exactly.
8. Keep the retained mypy fix from `e7e9242`; do not lose it during integration.

Required fresh Alembic-head executable matrix includes at minimum:

- the five Codex rows: completion source ID/SHA mismatch; detector revision
  non-empty wrong value; manifest policy ID mismatch; manifest schema mismatch;
  manifest+completion generation agreeing with each other but contradicting
  job/evidence;
- missing/null/bool/string variants for new required manifest fields;
- completion source ID-only and SHA-only tamper;
- valid no-source and valid real-source full completion remain accepted;
- all retained C2 count/identity/revision/history/nonterminal rows remain green;
- at least one real API/project readiness row combines source-identity tamper
  with `not_run`, and one keeps valid full authority behind 101 audio jobs.

Worker gate: micro new rows -> both complete T03G modules -> Ruff F -> exact
mypy retained scope -> own diff-check -> guard/allowlist audit. Commit the exact
task branch and report `TASK_SUBMITTED`, then exit.

### C3-A2 — T06C exact affected/QC/readiness restart proof

Resume exact T06C. Allowed write set:

- `tests/test_s11_t02_t06_acceptance.py`
- `docs/pm/sessions/S11-T06C/**`
- new external S11-C3 evidence only.

All production code and T03G/T05A tests are read-only.

Strengthen `test_t12_targeted_correction_recompute_restart` without replacing
the real production path:

1. Before correction, snapshot **both affected role A and unaffected role C**:
   role-artifact association row IDs, artifact IDs, state, relative path,
   SHA-256, size and managed bytes.
2. After restart completion, positively prove new recompute-job artifacts are
   associated with role A, have expected purposes, valid SHA/size/bytes and are
   not just the pre-existing A artifacts. Prove the old/new association and
   supersession behavior exactly matches the production contract.
3. Retain byte-identical proof for every unaffected C row/association/SHA/byte;
   prove zero C publication under the recompute job.
4. Fresh-session reads must explicitly assert the one correction's terminal
   status, one recompute job/attempt/effect, the QCItem's exact expected status
   after correction/recompute (including whether it awaits recheck), and the
   exact computed readiness result/reason. Do not claim resolved/ready if the
   contract correctly leaves the item pending recheck.
5. Retain affected-only manifest, no full timeline/project publication,
   occurrence CAS once and replay/no-duplicate assertions.
6. Make evidence output hermetic. Use an explicit S11-C3 evidence-root env var
   when Manager requests durable evidence; without it, write only under that
   test's fresh temp/scratch root. No ordinary rerun may mutate S11-C2/C3
   submission evidence.
7. Run the exact node twice as two separate pytest commands and separate fresh
   DB/managed/basetemp roots; index actual/expected for every assertion.

If strengthened assertions pass current production, do not dispatch T04B. If
they expose a minimal product defect, save the isolated failing reproducer and
return `NEEDS_T04B_PRODUCT_FIX` to Manager.

Worker gate: exact node twice -> complete T06 acceptance module -> Ruff F for
changed test -> own diff-check -> guard/allowlist audit. Commit and exit at
`TASK_SUBMITTED`.

## 5. Conditional product/consumer routing

### T04B only on a real product RED

If and only if C3-A2 produces a minimal executable production failure, resume
exact T04B `20260903_183246_706d31`. Scope is only the directly implicated
correction/recompute production file and its T04B tests/session evidence. No
speculative refactor. After fix, T06C exact owner rebases/fast-forwards only as
allowed by rules and reruns its node twice.

### T05A only on a real integrated consumer RED

Do not dispatch T05A speculatively. After T03G integration, run all 14 T05A
tests. Only a real product/fixture regression may resume exact real owner
`20260903_203404_4a4548`; T04D `...5b3841` remains permanently forbidden for
T05A. T05A write scope remains its two test modules plus
`app/persistence/readiness.py` only when executable evidence proves a consumer
defect.

## 6. Manager review and integration

Manager never edits implementation/test bytes.

For each submitted lane after writer exit:

- compare exact base/tip and changed paths to allowlist;
- inspect current diff and assertion quality, not just test count;
- rerun the lane's new adversarial rows on a fresh root;
- audit guard hashes and actual model usage for the new turn;
- reject overclaim, missing proof, unmerged tip or gate masking.

Only Manager-verified commits proceed. Resume INT01 Git-only owner on canonical:

1. Reconfirm canonical clean at `7474eb7` and remote unchanged.
2. Merge all exact verified T03G commits, including `e7e9242` and its C3
   successor, conflict-free. Merge exact verified T06C commit. Conflict =>
   abort and return to owner; INT01 may not resolve source/test conflicts.
3. Prove every verified task tip is an ancestor of canonical final HEAD; no
   post-gate commit may remain stranded on a task branch.
4. Run micro/focused gates before any broad ladder. Do not push yet.

## 7. Fail-fast final ladder

Use a runner that preserves **each command's exit code** (`set -euo pipefail`,
PowerShell explicit `$LASTEXITCODE` check after every command, or equivalent).
Never print a green aggregate after any red/missing command.

1. Fresh Codex five-row authority matrix: all five fail closed; valid controls
   remain completed.
2. Both complete T03G modules: at least retained `98` plus all C3 nodes.
3. T06C exact real restart node twice on separate roots, then complete T06
   acceptance module.
4. Both T05A modules: retained 14/14.
5. Combined T03G + T04B if used + T05A + T06C focused gate.
6. `python -m ruff check --select F` on affected code/tests.
7. `python -m mypy app/persistence/qc_check_runs.py app/persistence/readiness.py --follow-imports=skip`
   must print `Success`; verify canonical contains `e7e9242`'s effective fix.
8. `git diff --check 7751598214eedb6b72e3783e39a2a408721abe40..HEAD`
   exit 0.
9. Alembic exactly one head and fresh upgrade succeeds.
10. OpenAPI duplicate-operation scan must call current `app.openapi()` directly
    and report path/operation/duplicate counts. Do not call nonexistent
    `tests/test_openapi_no_duplicate_routes.py`. Expected retained surface is
    at least 274 paths / 340 ops / zero duplicate operation IDs.
11. Outer acceptance retains at least 12 passed and includes strengthened T12.
12. Inner S11 QC suite retains at least 380 plus all new nodes.
13. T01 retains 64/64; S10 full-apply retains 71/71.
14. Frontend/API-route/migration hashes unchanged unless conditionally
    authorized above; otherwise retain prior frontend proof by exact hash.
15. Canonical porcelain empty; zero writer/pytest/product/ffmpeg/watchdog/cron/
    heartbeat; all evidence timestamps after their corresponding tests.

Any red gate returns to its exact owner. Do not run broad gates while micro or
static gates are red. A command-not-found, missing file or masked exit is RED.

## 8. One final push and terminal packet

Only after the whole fail-fast ladder is green, INT01 performs one non-force:

`git push origin HEAD:refs/heads/codex/s11-integration`

Then independently prove `git ls-remote` equals local final HEAD. Remote drift,
push failure or any unmerged verified task tip is terminal blocker; no force
push, reset, history rewrite or hidden follow-on commit.

Create under the new S11-C3 run root:

- `manager/REGISTRY.md` with exact session/model/commit/owner map;
- raw preflight, five probes, lane tests, static commands, broad ladder,
  process and Git outputs with per-command exits;
- per-lane prompt snapshots/dispatch logs;
- `manager/exit/EXIT_VERDICT.md`;
- `manager/exit/NEXT_REVIEW_PACKET.md`.

Packet maps every C2 finding to current source line, exact test, session and
commit; distinguishes Manager evidence from ordinary test temp output; lists
all skipped/conditional lanes; proves local==remote and zero active writer.

Green terminal only:

`S11-C3 = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`

Bắt đầu ngay: full rules load -> pinned preflight -> dispatch exact T03G/T06C
song song -> Manager verify -> conditional lanes only on real RED -> INT01 merge
-> fail-fast ladder -> one non-force push -> terminal packet -> stop.
