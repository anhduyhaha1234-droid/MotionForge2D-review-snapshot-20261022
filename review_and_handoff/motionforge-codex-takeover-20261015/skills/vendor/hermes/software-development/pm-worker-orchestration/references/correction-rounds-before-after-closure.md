# Correction rounds: immutable BEFORE/AFTER evidence, closure matrix, recovery owner

Proven across C6D/C6E/C6F (MotionForge2D S10 sprints). Covers the protocol codified in
rules §4 (context health + recovery) and the Codex-mandated closure protocol.

## Manager-owned BEFORE/AFTER repros (RED-first evidence)

- Pattern: a pytest file that reuses the real route + real `JobService` + one fresh
  isolated SQLite per sequence. Reuse test helpers via importlib (`_load_tests_module`,
  `_make_client`, `_payload`) — `tests/` is NOT a package, so plain `import` fails.
- Root discovery: `_ROOT = next(p for p in Path(__file__).resolve().parents if (p/"tests"/"test_..._api.py").exists())`.
  NEVER `parents[N]` — evidence dir depth changes between rounds (C6C file at depth 5,
  C6D/C6E before/<case>/ at depth 7) and the cached N silently breaks.
- The before-repro asserts the CORRECT (post-fix) contract, so it FAILS pre-fix —
  the failure + result-JSON sidecar IS the defect evidence (class RED_DEFECT).
  Exit assertions must be implication-shaped for tamper/fail-closed cases:
  `C1 = (not replay_ok) or (not mismatch)` — a 409/422 fail-closed is correct
  behavior, NOT a test failure. A "replay must succeed AND match" assertion is
  wrong for tamper rows.
- Never re-run before-repros while the worker may be editing the same test helpers
  (importlib execs the file mid-edit → nondeterministic evidence). Guard: compare
  write-set mtimes vs dispatch baseline; if unchanged, re-run is safe and deterministic.
- "verification stale" hook on these scripts: don't repair them — their fix is the
  worker's. Re-run fresh, show the identical deterministic defect, state RED-by-design.
- Post-fix: `cp` scripts → `after/<case>/` with evidence filenames renamed
  (`result_before_*` → `result_after_*` via sed). Never reuse paths/filenames; before/**
  stays immutable. Manager owns the flip verdict, never the worker's REPORT alone.

## True-concurrency proof (barrier semantics)

- Barrier INSIDE the production method via subclass:
  `class _Wrap(JobService): def create_job(self,*a,**k): barrier.wait(); reached.append(1); return super().create_job(*a,**k)`.
- Proof by COUNT, not set(): `threading.Barrier` auto-resets after passing, so a
  post-run `barrier.wait(timeout=0.1)` always times out (false negative), and
  TestClient portals execute both participants on same-named worker threads
  (`set(reached)` collapses to 1). `len(reached)==2 and no thread errors` is the proof.
- Sequential A-then-B is NOT a race. Audit any test named barrier/race/concurrent for
  `threading|Barrier|Event|Thread|.start(|.join(` — zero matches = STRUCTURAL_GAP,
  binary fail in Manager gate even if pytest is green.

## Worker blocker-claim triage (SCOPE_EXPANSION)

- When a worker claims "needs migration/schema/global index": verify feasibility
  BEFORE accepting BLOCKED. Typical closure: two paths that must be mutually
  exclusive can arbiter on the SAME row with disjoint CAS predicates
  (`failed→pending` vs `failed/cancelled/completed→cancelled`, rowcount-gated) —
  SQLite single-writer makes them mutually exclusive; no migration needed.
- Route back with the concrete design direction (C6E: worker's migration claim was
  disproved in one routed-back turn). Only accept the blocker with exact repro after
  the directed attempt genuinely fails.

## 401 auth-server transient (router auth flake)

- Symptom: `401 {"error":{"code":"","message":"鉴权服务请求失败: .../v1/internal/auth/verify": context deadline exceeded`}.
  This is the 9Router auth service timing out — transient infra, NOT a model/config
  blocker. Probe the same session/model ("reply exactly PROBE_OK"); if OK, resume.
  Wait ≥5 min per rules; unlimited cycles; never switch model to dodge it.
- Survivability trick: instruct the worker to append LOG.md/REPORT.md/STATUS as its
  FIRST actions in the turn. Appends persist even when the final response 401s
  (turns kept dying on the last request otherwise).

## Recovery owner (rules §4 — context broken)

- Zero-live-writer proof: the scan command itself contains the session IDs → counts
  itself (got "4 processes" that were all the scan). Use a .ps1 run with `-File` and
  `-and $_.ProcessId -ne $self`; COUNT=0 is the proof.
- Session-ID capture: `--pass-session-id` does NOT print the ID to the dispatch log.
  Query `~/AppData/Local/hermes/state.db`:
  `SELECT id, session_key FROM sessions ORDER BY rowid DESC LIMIT 1` and
  `session_model_usage` for the effective model. The probe session counts as the ONE
  new recovery session (clean context) — dispatch C13 into it with `--resume <id>`.
- OWNER_TRANSFER registry line: old lineage (original + effective continuation ids),
  context-health metrics (dump bytes / messages / user turns / tool entries), reasons
  (repeated contract misses, false scope claim, repeated serial-labeled-concurrent),
  zero-writer proof + timestamp, new session id, "no old-lineage resume; zero
  concurrent writer".
- Handoff prompt = compact: current verdict, landed-byte hashes, open findings with
  file:line, write-set, acceptance, remaining gates. Never recap the full history.

## Worker terminal-claim verification (TASK_SUBMITTED false positives)

- `grep "STATUS: TASK_SUBMITTED"` can match (a) the prompt template text inside the
  dispatch log, or (b) the STALE status line from an earlier round still sitting at
  the tail of REPORT.md. Never trust a grep hit alone.
- Real proof: LOG.md/REPORT.md mtimes ≈ turn end (if mtime is hours old, nothing
  landed), the STATUS line is the LAST line of the file, and the round marker
  (e.g. `C13`) appears with count > 0 in the appended section.
- Worker turns end mid-flight with EXIT=0; the log may also carry a
  "file-mutation verifier: N file(s) were NOT modified" warning + `[patch] Found 2
  matches` — the claimed edit did NOT land. The continuation prompt must include:
  "verify current file state, complete the failed edit with UNIQUE context (the
  fuzzy matcher needs disambiguation), then re-run"; never assume the patch applied.

## Model override churn (per-prompt, latest user instruction wins)

- Worker model is per-prompt, not global: C6C=GLM → C6D/C6E=BAI/deepseek-v4-flash-vision-exp
  → C6F=comboBAI exact-case. The newest user message/packet supersedes. When a new
  packet arrives, read its model section FIRST and re-probe (fresh + resume) with the
  new selector; keep evidence in `manager/prep/model/**`.
- Heartbeat cron model is set separately: `hermes cron edit <id> --model X --provider Y`
  (comboBAI aliases need `--provider custom`). When the user asks "why is worker X
  still running Y model", scan LIVE process command lines (Get-CimInstance, exclude
  self-PID) — registry/history entries are not evidence of what is running.
- comboBAI selector: effective upstream member is router-internal; CLI logs expose
  only the selector. Record the ledger honestly ("selector comboBAI; member per
  9Router combo; no false per-upstream attribution"), never claim a single member
  handled all traffic without router evidence.

## CLOSURE_MATRIX + phased gates (C6F pattern)

- Lock matrix (`.md` + machine-readable `.json`) BEFORE dispatch. Each row: Closure ID
  (stable, never merge), Requirement (binary invariant), Current source (file:line),
  BEFORE evidence (path + actual HTTP/counts), BEFORE class, Worker test
  (`TO_ADD` if missing), AFTER evidence (PENDING), Exit assertion (exact HTTP, row
  counts, mutation count), Status (`LOCKED_PENDING_FIX` → only Manager sets `CLOSED`).
- Classes must be honest: reproduced defect = RED_DEFECT; already-correct on current
  bytes with green evidence = RETAINED_CONTROL (never fake RED); validation exists but
  mandated isolated test missing = STRUCTURAL_GAP. Any `TO_ADD` row without exact
  acceptance = BLOCKED (CLOSURE_MATRIX_INCOMPLETE) — no prose-only dispatch.
- Gate order (fail-fast): MICRO (after-repros + race tests + source-structure audit)
  → CLOSURE-MATRIX-100% (only Manager closes rows, 0 PENDING/OPEN/TO_ADD) →
  FOCUSED (new tests ×2 + retained ×2 + ruff/mypy/diff-check) → FINAL-BROAD once
  (full suite ×2 + alembic/OpenAPI/J1-v4/validator/protected-SHA/porcelain). No broad
  runs between continuations; any production edit after broad invalidates it.
- Live UI check: ports MUST match the baked build origin (NEXT_PUBLIC_API_URL =
  http://localhost:8201 → S10_BACKEND_PORT=8201, S10_FRONTEND_PORT=3000), else the
  page shows "Failed to fetch" and every test fails on selectOption. Use the sprint's
  own playwright config (globalSetup seeds EXEC/NOAUTH/PROD-E2E; missing it →
  "project S10-C6A-EXEC not found").

## Repro-hygiene: false-green and manual-row pitfalls (C6G-proven)

- **A repro can "pass" without touching the defect.** G2's first run returned
  `1 passed` because the exercised helper raised `TypeError` (wrong signature:
  `_s10_retry_claim_predecessor(session, run_id, workspace_id)` was called with
  `(real_svc, run_id)`); both claim calls recorded `{"claim": None, "error": ...}`,
  so `claims.count(True) <= 1` was trivially True. Rule: after a run, PRINT the
  recorded values (claims/results), not just the assert outcome; any `claim: None /
  error` entry means the script didn't exercise the path — the pass is vacuous.
- **Discover internal-helper signatures BEFORE calling them** (grep
  `def _s10_retry_claim_predecessor` → read args). Passing a service instance where
  a Session is expected is a silent TypeError.
- **Manual INSERT into a real table needs every CHECK/constraint.** Inserting a
  second job row with `revision=0` fails `CHECK constraint failed:
  ck_job_revision_positive` — the whole test errors BEFORE writing the result JSON,
  leaving the evidence file missing. Copy the original row's constrained columns
  (`revision>=1, attempt, max_attempts, priority, resource_class, ...`) from a
  `SELECT *` of the real row; keep created_at/updated_at CURRENT_TIMESTAMP.
- After fixing a repro script, re-run and confirm the JSON sidecar is written AND
  the defect values are the expected ones (e.g. `claim: true, true`), not errors.

## No-op same-state CAS is not an ownership token (G2 invariant)

- A claim CAS that writes the SAME state (`cancelled → cancelled`) makes SQLite
  report one affected row, so every caller believes it won exclusivity — verified:
  `claim1=true, claim2=true` on an already-cancelled predecessor. Rowcount is NOT
  proof of mutation.
- Fix directions (choose one, bounded): real state/version transition
  (`failed → cancelled` only for failed; cancelled uses a different token), OR make
  the atomic unique successor-run/natural-key INSERT the ownership point and convert
  `IntegrityError`/domain collision into stable 409 with clean rollback.
- Tests must assert the WINNER COUNT at the ownership point, not just final rows;
  "final rows unique because the DB backstop fired" is not evidence the claim
  contract was fixed (Codex explicitly rejects this masking).

## Matrix arithmetic consistency + append-only addendum (G4-D1)

- Every artifact must carry IDENTICAL counts: CLOSURE_MATRIX.md table + .json rows +
  .json summary + worker REPORT + LOG + registry + EXIT. C6F was rejected solely
  for "15 rows / 6 retained controls" in REPORT/evidence/registry vs "14/5" in the
  binding matrix — a documentation-integrity finding (P2), no code involved.
- Fix via APPEND-ONLY addendum naming the wrong lines (file:line) and the correct
  numbers; never rewrite history. Then re-verify every artifact with a grep of the
  count strings, not by memory.
- Row-count arithmetic rule of thumb: N rows = RED_DEFECT + STRUCTURAL_GAP +
  RETAINED_CONTROL; when building the matrix, count rows from the JSON array (not
  prose) and mirror that number everywhere else.

## Parallel reader lanes after TASK_SUBMITTED (C6G DAG)

- After worker terminal + stable hashes, Manager MAY launch exactly 3 isolated
  read-only readers concurrently (each with own DB/temp/output, no source writes):
  Reader A identity/ambiguity after-repros; Reader B retry-ownership/CAS after-repros
  + real-race assertions; Reader C source-structure audit + Ruff/mypy/diff-check.
- JOIN all three before MICRO verdicts; any reader failure reopens exactly its
  matrix rows and routes ONE combined failed-row packet to the same owner (not one
  message per test). Focused/full gates remain serialized; never run broad before
  micro + matrix closure.
