# S11-C2 — Codex Independent PM/BA/Code Rereview

**Review date:** 2026-09-04 17:34 +07  
**Reviewed tree:** `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`  
**Branch / local HEAD:** `codex/s11-integration` @ `7474eb7af412fa1a1148f03f3786d1b2728566d9`  
**Remote HEAD:** `origin/codex/s11-integration` @ `7474eb7af412fa1a1148f03f3786d1b2728566d9`  
**Submission claim:** `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`  
**Codex verdict:** `CHANGES_REQUESTED / NOT_APPROVED / S11_NOT_CLOSED`

## 1. Decision

C2 is a substantial improvement: the mixed-history limit bug is fixed, the
targeted restart test now executes the real correction/`RECOMPUTE_OBJECTS`
path, the real T05A owner produced the consumer correction, the canonical tree
is clean and the remote equals local. The current covered suites are green.

S11 still cannot close. Five fresh real-DB tamper rows are accepted as a valid
completed full run, the restart test still overclaims two parts of its proof,
and the Manager pushed a terminal tree after its own static log showed a mypy
failure and an OpenAPI command targeting a nonexistent test file. A follow-on
mypy fix exists as `e7e9242` on the T03G branch but was not integrated.

## 2. Positive evidence retained

- Canonical porcelain is empty; local and GitHub both resolve to `7474eb7`.
- `git diff --check 7751598..7474eb7` exits 0.
- Codex independently reran current bytes:
  - T03G job/API modules: `98 passed, 197 warnings in 121.57s`;
  - T05A readiness/next-action modules: `14 passed, 21 warnings in 14.82s`;
  - the real targeted correction/recompute restart node twice on separate
    roots: `1 passed` in 3.43s and `1 passed` in 3.38s.
- The restart evidence shows one queued then completed `RECOMPUTE_OBJECTS`, one
  correction, one attempt, role-A output under the recompute job and no role-C
  publication. No current production defect has yet justified T04B dispatch.
- The submitted broad counts (outer 12, inner 380, T01 64, S10 71) are credible
  regression evidence for the paths they cover.
- The T05A/T04D ownership incident is now disclosed and the real T05A owner
  `20260903_203404_4a4548` produced `caf8dcf`.
- No S11 watchdog/writer remained at the Codex snapshot.

## 3. Findings

### [P1] Completion authority still accepts internally inconsistent identity

**Locations:**

- `app/persistence/qc_check_runs.py:310-361`
- `app/persistence/qc_check_runs.py:420-440`
- `app/persistence/qc_check_runs.py:491-541`

The C2 gate correctly validates required counts, interrupt flags, detector
membership and non-empty revision values. It does not validate all identity
fields the producer writes:

- manifest `schema_version` and `policy_id` are not checked;
- completion `source_artifact_id` and `source_artifact_fingerprint` are not
  matched to the manifest/current source;
- manifest/completion `source_generation` can agree with each other while
  contradicting the evidence fingerprint and the job input generation;
- detector revision values only need to be non-empty; they need not equal the
  server-owned registry revisions.

Codex used a fresh Alembic-head SQLite DB and current production helpers. Every
row below should fail closed (`failed`/readiness `not_run`) but returned
`completed`:

```text
completion_source_identity_mismatch: run_state=completed
detector_revision_value_mismatch: run_state=completed
manifest_policy_id_mismatch: run_state=completed
manifest_schema_version_mismatch: run_state=completed
generation_vs_evidence_inconsistent: run_state=completed
```

This is the same authority boundary as C1, not a new feature request. A stored
completion is trusted to unblock export readiness, so partial identity checking
remains a P1 false-ready risk.

**Exact owner:** T03G session `20260903_170546_0d42f6`.

### [P1] Targeted restart test does not prove its affected/QC-read claims

**Locations:**

- `tests/test_s11_t02_t06_acceptance.py:1958-2010`
- `tests/test_s11_t02_t06_acceptance.py:2057-2074`

The test now runs the correct production path and is valuable. However:

- `affected-recomputed` only checks that role A has at least one artifact;
  role A already had two artifacts before the correction. The test never saves
  the affected preimage or proves new recompute-job artifacts are associated
  with role A and differ from the preimage.
- `no-unaffected-republish` proves new rows are not associated with role C, but
  does not positively bind those rows to role A.
- the “fresh reads” assertion reads only the Job and ObjectCorrection. It does
  not re-read the QCItem or the computed readiness state despite the docstring
  and C2 contract claiming both.

The current output strongly suggests the product path works, so T04B remains
conditional. C3 should strengthen executable assertions first and dispatch
T04B only if those assertions reveal an actual product defect.

**Exact owner:** T06C session `20260903_223530_b90853`.

### [P1] Terminal gate was declared green after recorded failures

`s11-c2/manager/raw/pre-push-static.txt` contains:

```text
app\persistence\qc_check_runs.py:98: error: Returning Any from function
declared to return "str"  [no-any-return]
ERROR: file or directory not found: tests/test_openapi_no_duplicate_routes.py
STATIC_DONE=0
```

The last line captured only a later successful shell exit; it did not propagate
the earlier mypy/pytest failures. Codex reran the retained mypy command and got
the same failure. The correct OpenAPI inspection is not that nonexistent test;
a direct `app.openapi()` scan on current bytes reports 274 paths, 340 operations
and zero duplicate operation IDs.

The T03G owner later committed the narrow mypy correction as
`e7e9242d862001ae89c852d91e2c6587da4ceeb4` at 16:42 +07. Canonical final/push
HEAD `7474eb7` was created at 16:29 +07 and does not contain that commit. Thus
the packet overclaims both static closure and integration completeness.

**Exact owners:** T03G for the source/type correction; INT01 session
`20260903_112116_35051c` for verified transport.

### [P2] Model/evidence reporting is not exact

The binding C2 prompt pins `ocgfree/muse-spark-1.3-contributor-free`, custom,
max requested, fallback off. Read-only `session_model_usage` confirms Muse for
the T03G and T06C implementation turns and an initial T05A attempt, but T05A
then hit a `FreeUsageLimitError`; later records on T05A/INT01 are stored as
model `meta`. The exit packet instead says “cmc 1.3” and does not map that claim
to the durable usage rows. This does not by itself reject good code, but C3 may
not silently switch models or report a route that the ledger cannot prove.

The T06C test also writes every rerun to a hard-coded S11-C2 evidence directory.
Codex's independent reruns consequently created post-submission files in that
directory. C3 must use an explicit evidence-root environment variable for
Manager evidence and a temp-local default for ordinary reviewer/test runs.

## 4. Quality assessment

Muse 1.3 was fast and materially better at executing the intended workflow:
T03G built a broad adversarial matrix and T06C replaced the neighboring
full-QC scenario with a real correction/recompute restart. Its remaining
weakness is exact negative-contract closure: it checked that identity fields
were present/non-empty without binding every value to server authority, and it
used assertions that were adjacent to the promised affected/QC proof.

Recommendation: keep Muse for the bounded C3 correction, but retain Codex-style
adversarial probes and fail-fast gate aggregation. Do not treat speed or broad
green counts as a substitute for the finite closure matrix.

## 5. Session opening proposal

`AUTHORIZED_TO_DISPATCH` only for bounded `S11-C3`; S12/S13 remain blocked.

- Open one **new compact Manager session**. Do not resume the C2 Manager: it
  lost a post-gate commit and allowed failed commands to collapse into a green
  summary.
- Run at most two isolated owners in parallel:
  - resume exact T03G `20260903_170546_0d42f6`, starting from clean task tip
    `e7e9242`, for the five authority rows plus retained mypy fix;
  - resume exact T06C `20260903_223530_b90853` for affected/QC/readiness proof
    and hermetic evidence output.
- T04B `20260903_183246_706d31` remains conditional on a new executable product
  failure. T05A is read-only unless a new T03G consumer regression is real; in
  that case resume only `20260903_203404_4a4548`.
- Resume exact INT01 `20260903_112116_35051c` only after both lanes are
  Manager-verified. Merge all verified tips conflict-free, run a fail-fast
  ladder, then perform one non-force push and prove local == remote.
- Per the user's latest override, every new C3 worker turn uses exact custom
  9Router model `cmc/muse-spark-1.3-contributor`, requested reasoning `max`,
  fallback off. A route error is a declared model blocker, not authority to
  switch silently.

Binding prompt:
`docs/pm/prompts/S11_C3_EXACT_IDENTITY_RESTART_PROOF_FAIL_FAST_EXIT_MANAGER_2026-09-04.md`.
