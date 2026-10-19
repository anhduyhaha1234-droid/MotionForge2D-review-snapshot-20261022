# True-concurrency repros & immutable evidence (PM-gated race cycles)

Proven in S10-C6E (C12, worker BAI/deepseek-v4-flash-vision-exp). These are the
patterns Codex reviewers explicitly check (C6D F1/F4 findings): barrier
rendezvous proof, real DB rows, no serial-test-labeled-concurrent.

## Barrier rendezvous proof
- Two Python threads + `threading.Barrier(2, timeout=30)` placed INSIDE the
  production call under test (e.g. wrap `JobService.create_job`:
  `barrier.wait()` then `super().create_job(...)`), monkeypatch `deps._job_service`.
- Prove rendezvous by appending to a SHARED list inside the wrapper
  (`reached.append(1)`); `barrier_reached = len(reached) == 2 and not errors`.
- Pitfall 1: a `threading.Barrier` auto-resets after the parties pass — re-waiting
  on it to "check" times out / raises `BrokenBarrierError`. Do NOT verify that way.
- Pitfall 2: `TestClient` runs the app on its own anyio portal thread; two
  `TestClient` instances from two threads can share the SAME portal thread name
  → `set(reached)` collapses to 1 → false "no rendezvous". Count entries, never
  dedupe by thread name. (If the requests were truly sequential, the second
  party would break/timeout the barrier and produce an error — barrier
  semantics themselves prove simultaneity.)
- No `time.sleep` as correctness mechanism; Barriers/Events only.
- Sequential A-then-B is NOT concurrent — never label it so (Codex F4 finding).

## SQLite NULL-in-unique-index hole
- A UNIQUE index on `(workspace_id, idempotency_key, input_generation)` with
  nullable `input_generation`: SQLite treats NULLs as DISTINCT → two concurrent
  inserts with generation NULL both succeed → "database backstop" does NOT
  serialize. This is the root cause of "true concurrent replays create two jobs".
- Fix direction: deterministic non-NULL generation server-derived from the run
  (`s10:<run-id>`) passed by EVERY job-creation path (submit/repair/retry/resume),
  so the existing index serializes same-key+same-generation inserts.
- Catch the STABLE job-domain idempotency exception (repo converts raw
  `IntegrityError`), re-read the winner, converge; never compensate the shared
  winning run to failed, and never treat the conflict as generic enqueue failure.

## Concurrent TestClient threading pattern
- One `TestClient(app, raise_server_exceptions=False)` per thread (each owns a
  portal thread); patch `deps._job_service` once, module-level — both threads
  resolve it at request time.
- SQLite lock contention: a race test with a long read-then-create window hangs
  (seen: one run 93s, one 180s timeout). If a barrier test hangs/flakes, the
  DESIGN is wrong — the fix (CAS arbiter) makes the loser fail fast; don't
  delete the test, fix the design.

## Immutable before/after evidence
- `before/**` written pre-fix: assertions that FAIL = defect recorded (RED by
  design; pytest exit != 0 is the EVIDENCE, not a bug).
- `after/**` post-fix: COPY the before script (never reuse same path/filename),
  `sed` the evidence filenames (`result_before_*` → `result_after_*`), fix only
  assertions whose logic was wrong (e.g. tampered-manifest C1 must be the
  implication "success ⇒ exact match" — a 422 fail-closed is CORRECT, not a
  failure; asserting "success and match" is the wrong check for tamper cases).
- NEVER re-run `before/**` while the worker owns the same write-set: the repro
  importlib-loads `tests/` live and could grab a half-written module → noisy
  evidence. Single-writer wins.
- When the in-app verification hook flags "stale verification" on evidence
  scripts: re-run pytest ONLY after checking write-set mtimes show no worker
  landing; otherwise defer to the manager gate and say so explicitly.

## mtime audit false-alarm
- `ls --time-style=+%H:%M:%S` shows TIME ONLY. "21:38:48" on a file that's
  actually Aug-28 looked like a future timestamp → scope-violation panic about
  a forbidden file (models.py) that had NOT been touched (sha256 = baseline).
  Always use `stat -c '%y'` (full date+time) before concluding a file was
  touched; cross-check with sha256 vs baseline before any BLOCKED_SCOPE_*.

## Verifying "worker needs a migration" claims
- Worker claims a race cannot close without a unique-index migration. VERIFY
  yourself before stopping `BLOCKED_SCOPE_EXPANSION`:
  1. Reproduce independently (their repro + read final rows).
  2. Read the CAS predicates: if repair CASes `failed→pending` (rowcount-gated)
     and retry can CAS the SAME run row with a disjoint predicate
     (`failed|cancelled|completed → cancelled`, rowcount=1 wins / 0 → 409), the
     race closes with routes-only changes — no schema.
  3. Route the direction back to the exact owner (T3: "attempt CAS arbiter; if
     still impossible, prove it with file:line + why CAS is insufficient").
- Only accept BLOCKED after the owner proves impossibility; never trust
  "cannot be done without migration" from a report alone.

## Worker-wide model override ("đổi hết ...")
- Prove no old-model process remains: PowerShell `Get-CimInstance Win32_Process
  | Where-Object { $_.CommandLine -match '<model>' }` via a .ps1 FILE
  (inline `powershell -Command` breaks on quotes/`$_` in bash; `wmic | grep`
  commands get hardline-blocked).
- Update EVERY consumer including heartbeat cron:
  `hermes cron edit <id> --model X --provider Y`, verify via `cronjob action=list`.
- Old-model mentions in registry/review history are NOT running processes —
  say so when the user asks "why is X still running".

## Small gotchas
- `mkdir -p <logdir>` BEFORE any `hermes ... > log` redirect (else
  "No such file or directory", probe silently lost).
- Repo-root discovery in evidence scripts: walk parents until
  `tests/test_*.py` exists. `Path(__file__).resolve().parents[N]` breaks the
  instant the evidence dir depth changes between sprints.
