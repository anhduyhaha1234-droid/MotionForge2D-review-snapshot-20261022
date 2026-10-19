# Structured terminal contract + invocation runtime (adopted 2026-10-11, MF2D R4)

Replaces prose/substring classification of worker outcomes. Measured failure that forced it:
a classifier that took the LATEST marker occurrence in the log read `self_review_pass_pending_codex`
out of a FORWARD-LOOKING sentence ("after all gates -> SELF_REVIEW_PASS_PENDING_CODEX") while the
real terminal was `CONTINUE_REQUIRED` — and `exit 0` had already been proven meaningless (context-
exhausted runs exit 0). Rule: no prose token is ever a verdict; require a structured record whose
binding comes from the IMMUTABLE dispatch ledger, and fail closed to `NEEDS_RECONCILIATION`
on anything missing/mismatched.

## Record schema (adopt verbatim)

Binding fields (must equal the expected binding, never self-declared): `run_id`, `task_id`,
`revision`, `owner_sid`, `invocation_id`, `packet_sha256` (64-hex).
Result fields: `schema_version="1.0"`, `status ∈ {CONTINUE_REQUIRED, TASK_SUBMITTED, USER_STOP,
BLOCKED}`, `reason` (nonempty), `remaining_work: list`, `artifacts: [{kind, path, sha256}]`,
`matrix: {Q01..Q12 -> PASS|FAIL|UNKNOWN}`. Pydantic strict (`extra='forbid'`); parse with
`object_pairs_hook` that raises on duplicate keys.

Model rules: CONTINUE_REQUIRED requires nonempty `remaining_work`; TASK_SUBMITTED requires empty
`remaining_work`, exactly keys Q01–Q12 all PASS, and exactly one artifact of each required kind
(master / comparison / matrix / checkpoint / receipts; extra `other` allowed).

Validator rules (`validate_result(path, expected, allowed_root, invocation_terminal, exit_code,
infrastructure_error)`): fail closed unless invocation_terminal AND exit_code==0 AND not
infrastructure_error; record under `allowed_root`, ≤1MB; artifact paths absolute/under root/not
the record/unique with sha256 recomputed; the `matrix` artifact's content must equal
`{"rows": result.matrix}`. Decisions: CONTINUE_REQUIRED→PENDING_SAME_OWNER_CONTINUATION;
TASK_SUBMITTED→VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA; USER_STOP→VERIFY_USER_STOP_AUTHORITY;
BLOCKED→VERIFY_EXTERNAL_BLOCKER; else NEEDS_RECONCILIATION. `quality_accepted` is ALWAYS false —
a structured result is eligibility for Manager QA, never acceptance.

## Where the binding comes from

Dispatcher (consumer #1) mints `invocation_id`, writes the receipt + an append-only ledger
`dispatch` row BEFORE spawning, and substitutes `{{INVOCATION_ID}}` / `{{PACKET_SHA256}}`
placeholders into the packet text it sends. `packet_file_sha256` = sha256 of the raw packet FILE
bytes (that is what the worker echoes into the record); the legacy `packet_sha256` of the final
prompt stays as a separate field. The worker writes the record atomically (tmp + os.replace) to
`<allowed_root>/evidence/terminal/<invocation_id>.json` on EVERY terminal — including yields
(CONTINUE_REQUIRED) and BLOCKED. Keep the old prose classifier result only as
`legacy_prose_outcome` (reference), and drop nothing.

## Adversarial matrix the consumer tests MUST cover (measured green, 70/70)

Dispatch (run the REAL dispatcher as a subprocess):
- future / quoted / negated PASS prose + valid CONTINUE_REQUIRED record → CONTINUE_REQUIRED
  (assert `legacy_prose_outcome.class` shows the old trap value — proves the trap is still detectable).
- prose-only (no record at all) → NEEDS_RECONCILIATION (behaviour change vs legacy classifier).
- truncated JSON / duplicate JSON keys / wrong owner / wrong invocation / wrong packet /
  missing artifact / matrix-artifact mismatch / exit0 + "API call failed after 3 retries" /
  nonzero exit / empty remaining_work → all NEEDS_RECONCILIATION.
- TASK_SUBMITTED happy path (5 artifacts, all-PASS matrix) → VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA.

Heartbeat (consumer #2, `--once` over a fixture ledger):
- validated record → outcome class == record status, `source: structured_terminal`.
- open invocation + LIVE child pid in `child_spawned` row → `llm_worker_alive: true`,
  `outcome: INVOCATION_OPEN`; active lease row shows child `ALIVE`.
- REAL legacy receipt bytes from an old round → `LEGACY_NO_STRUCTURED_TERMINAL`,
  never the old prose class as authority (keep the prose class in `legacy_prose_class`).

Controller lock: a second live controller must be REFUSED (rc=4, `dispatch_refused` ledger row,
no child spawned). Lease: detached live child keeps the lease (`released:false`, `detached:true`);
after child death + quiet render probe → `released:true`.

## Controller lock + GPU lease (invocation_runtime module)

- Controller lock: `filelock` on `manager/locks/controller.lock` + meta JSON with holder identity
  (pid, create_time via `wmic_like`, name). Holder DEAD (identity False) → `break_lock()` and
  supersede; holder UNKNOWN (AccessDenied) → REFUSE (fail closed). Release writes
  `released_utc` + outcome into meta.
- GPU lease: one file per invocation (`manager/leases/gpu_lease.<invocation_id>.json`) with
  run/owner/invocation/job + child identities. Release ONLY when every child identity is DEAD
  AND the render probe is quiet (Comfy `/queue` empty AND no
  `-B ...p4_wan_run*/wan_run*/render_run*/r4_render*/r4_build*` process — the watch list must
  cover the batch naming you INSTRUCT workers to use). Detached child / UNKNOWN probe / active
  queue → keep ACTIVE, set `detached:true`, append to `release_attempts`. Controller exit NEVER
  frees a busy GPU lease. Prove with `scripts/lease-runner-probe.py`; later same-day tail
  additions (heartbeat one-tick closure lag, census self-match, detached-batch resume pattern):
  `references/structured-terminal-records-and-consumer-patching.md`.
- Identity: psutil `pid + create_time (+name)`; NoSuchProcess→gone `{}`; AccessDenied→UNKNOWN,
  never read as dead. `wmic_like(epoch)` formats `YYYYMMDDHHMMSS.ffffff+HHMM` so legacy ledger
  rows (wmic-sourced strings) still verify; compare with ±2 ms fraction tolerance.

## Patching legacy consumers (recipe)

1. Copy the validator module verbatim into the harness tools dir; record its source sha256.
2. Patch consumers with byte-exact anchored replacements scripted in Python with `count(old)==1`
   assertions per anchor (safer than chaining 10+ fuzzy `patch` calls). Preimage copy first;
   emit a unified diff (pre vs post) + py_compile + before/after sha/lines deltas as evidence.
3. If you later fix a patch, regenerate the diff against the ORIGINAL PREIMAGE and append a
   `fix1` note — never silently rewrite the old diff.
4. Both consumers import the SAME validator module; the heartbeat delegates identity checks to
   the shared runtime so semantics cannot drift apart.

## Testing actual consumers (scaffold)

Add a root-override env (`MF_RUN_ROOT`) to both consumers, derive every path lazily, then run the
REAL scripts as subprocesses against a temp scaffold: `<T>/manager/{locks,leases,DISPATCH_LEDGER.jsonl,
HEARTBEAT.jsonl}`, `<T>/tasks/<task>/`, `<T>/<allowed_root>/evidence/terminal/`. Use the existing
argv-prefix override (`DISPATCH_HERMES_ARGV_PREFIX='["<python>","<fake_child>"]'`) so tests never
touch the real CLI; the fake child parses the binding OUT OF THE PROMPT exactly like a real worker.
Starter: `templates/fake-terminal-worker.py`.

## Pitfalls (all measured this round)

1. ENV-OVERRIDE MAPPING TRAP: when adding a root env override to a legacy script, map it to the
   SAME semantic the existing variable already had. Here the variable named `RUN_ROOT` actually
   pointed at `<run>/manager`; mapping the env to the run root silently sent the LEDGER to the
   wrong directory. The refusal test caught it BEFORE any real dispatch. Rule: follow each derived
   variable to where it is actually WRITTEN and assert resolved paths in a dry run first.
2. venv `python.exe` is a redirector: it spawns a base-interpreter child with the same command
   line → TWO pids, identical cmdline (parent→child). Do not read it as a duplicate loop; check
   the ppid chain. (Explains "two heartbeat processes" scares.)
3. Manager-owned rows (e.g. Q11) reference Manager evidence OUTSIDE the worker's allowed root —
   the artifact-scope check rejects cross-root references. Publish the evidence, give exact paths
   + existence note, and instruct the worker to COPY the files into its own root before submission
   (kind `other`, hashes recorded). A worker's "evidence not available" often means it looked
   before the file existed — re-point with the exact path.
4. Swap legacy monitor loops via a STOP file + identity census, never pattern-kill: write STOP,
   poll until the recorded pids are gone (identity check), DELETE the STOP file, then start the
   new loop; keep before/after census in evidence.
5. Guard cadence: PRE manifest of the whole protected set BEFORE the first dispatch; MID manifest
   at each invocation boundary WHILE the worker is idle; POST at round end; diff against
   ALLOWED_NEW_PREFIXES (verdict CLEAN = 0 changed / 0 removed / 0 unauthorized added). Hashing
   ~38k files takes minutes — run scans in background.
6. Manager re-verification after every terminal: re-run the validator on the record bytes +
   recompute every artifact sha + check lease release — never trust the receipt's cached verdict.
   (Script pattern: a small `*_verify_invocation.py` writing `INV_VERIFY.json`.)
