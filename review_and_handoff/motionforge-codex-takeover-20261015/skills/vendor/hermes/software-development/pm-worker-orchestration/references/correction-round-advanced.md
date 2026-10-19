# Correction-round advanced playbook (S10-C6E proven, 2026-09-01)

Detail bank for the SKILL.md correction-round sections — concrete C6E cases
behind each rule. Companion to `gate-calibration-and-prevalidation.md`
(the C6D before/after immutable-repro discipline lives there).

## 1. 401 auth-service transients kill worker turns LAST

Symptom: dispatch wrapper exits 0, log ends with
`[401]: {"error":{... "鉴权服务请求失败: Post ...ainft-chat-service.../v1/internal/auth/verify": context deadline exceeded ...}}`,
no `STATUS:` line, no final response.

Triage by the MESSAGE, not the code:
- **Transient infra** (internal cluster auth-service deadline/timeout in the
  message) → treat as connection-class error per rules §7: RUNNING_RETRY_WAIT,
  probe route, wait ≥5 min (already elapsed if a probe is quick), resume SAME
  session/model. Unlimited cycles allowed; do NOT re-auth or change model.
- **Config-class 401** (provider key/route error in the message) → real
  blocker; diagnose config, never loop.

Practical facts:
- The 401 hits the LAST request of a turn after all work landed (T3 evidence
  + shakeout written, then died) or sometimes the FIRST (T4: zero landed).
- Distinguish by **write-set mtimes**: mtimes newer than dispatch = work
  landed before the 401; unchanged = turn died before acting.
- Liveness probe between retries (same resume command, tiny prompt):
  `PROBE_OK` / `PROBE_EXIT=0` = route healthy, resume immediately.
- **Docs-first continuation prompts**: when only documentation remains and
  401s keep killing turns, instruct the worker to append LOG/REPORT/STATUS as
  its FIRST actions ("làm ngay, trước mọi thứ khác"), then reply — appends
  survive a dying final call. If a T5-style doc turn also 401s, re-probe and
  resume again; do not hand-write worker-owned LOG/REPORT yourself (Manager
  never writes worker docs; append-only sets are worker-owned).
- Registry/heartbeat: re-arm the heartbeat script's PID + dispatch-log path
  after EVERY turn (sed the script) so liveness monitoring stays truthful.

## 2. Barrier-proof concurrency repros (true "concurrent", not serial)

Codex P1 F4-type findings reject serial calls labeled concurrent. The C6E F1
repro that PASSED review used:

```python
barrier = threading.Barrier(2, timeout=30)
reached: list[str] = []

class _BarrierWrap(JobService):           # test-only barrier, real job logic
    def create_job(self, *a, **k):
        barrier.wait()
        reached.append("ok")              # count entries, NOT thread names
        return super().create_job(*a, **k)

def _replay(name):
    c = TestClient(app, raise_server_exceptions=False)
    results[name] = {"status": resp.status_code, "body": _safe(resp)}
t1 = threading.Thread(target=_replay, args=("A",)); t2 = threading.Thread(...)
t1.start(); t2.start(); t1.join(60); t2.join(60)
barrier_reached = len(reached) == 2 and not errors
```

Pitfalls learned:
- **Do NOT prove rendezvous via `set(thread_names)`** — TestClient runs the
  app on its own portal thread(s); both requests may execute under the SAME
  thread name, so a set has size 1 and falsely reports "not concurrent".
  Count entries reached (`len(reached) == 2`) + zero thread errors instead.
- **Do NOT re-wait a Barrier after the fact** — a `Barrier(2)` auto-resets
  once both parties pass; a post-run `barrier.wait(timeout=0.1)` blocks then
  raises BrokenBarrierError, falsely reporting rendezvous failure. Record
  reach at the wait site.
- Place the barrier INSIDE the real production call (create_job) so both
  participants are simultaneously in the race window; barrier before the
  route call does not serialize the DB write.
- Evidence JSON must include barrier_rendezvous, both HTTP bodies, ALL
  run/job rows with `idempotency_key` + `input_generation` (the nullable/-
  generation values are what Codex checks).
- Repeat the case on fresh DBs/roots; each iteration asserts exactly one
  run/key/job + one active work + zero publication/checkpoint.
- **SQLite lock contention ≠ failure**: an early atomic-barrier test hung
  (93s / 180s timeout) and was removed as flaky. With the correct
  CAS-arbiter fix the loser fails fast (409), so the deterministic barrier
  test passes in ~2-5s. A hanging race test is a design smell, not proof
  a migration is needed.

## 3. Scope-expansion claim triage (worker says "needs migration")

Worker claimed `BLOCKED_SCOPE_EXPANSION` ("§6.3 at-most-one-active-per-lineage
cannot be achieved without a lineage unique index migration"). Manager
verification BEFORE accepting:

1. Read the actual DB backstop: the unique index may be
   `(workspace_id, idempotency_key, input_generation) UNIQUE` with a partial
   WHERE + **nullable** `input_generation` — SQLite treats NULLs as distinct,
   so omitting generation (all-NULL) destroys the backstop. That's exactly
   why the concurrent defect existed.
2. Ask: can the two racing paths CAS the SAME shared row with
   **mutually-exclusive predicates**? C6E: replay-repair CASes
   `failed→pending`; retry CASes `failed|cancelled|completed→cancelled`
   rowcount-gated BEFORE creating any successor/job. Either order, exactly one
   wins, the loser sees rowcount=0 → 409 zero-mutation. Closed in bounded
   routes, NO migration — the claim was disproven.
3. Route the finding back to the worker with the exact direction
   ("thử CAS arbiter trên run row; sau turn này nếu vẫn bất khả thi thì mới
   BLOCKED với evidence file:line") — do not accept the blocker on the
   worker's word, and do not write the fix yourself.
4. Verify the worker's fix independently: run the race tests + the after-repro
   yourself (2 passed 4.91s), read final DB rows, THEN conclude.

## 4. Timestamp-scar triage (don't panic at "future" mtimes)

`ls -la --time-style='+%H:%M:%S'` hides the DATE. A FORBIDDEN file appearing
to have been touched "21:38" (hours in the future) read as a scope violation
but was actually `2026-08-28 21:38:48` — pre-existing dirty, untouched.
Rules:
- For any protected/forbidden file in a suspicion: `stat -c '%y' <file>` for
  the full timestamp and `sha256sum` vs the latest baseline. **Hash is the
  truth; mtime display is a hint.**
- `git status --porcelain -- <file>` distinguishes pre-existing tracked
  modifications (S10 domain files are dirty from earlier sprints) from new
  writes — compare hash vs your own baseline, not vs HEAD.

## 5. Porcelain attribution for bounded write-sets

Count deltas per round: baseline 59 → 60 when the worker touched the bounded
`app/persistence/jobs.py` (previously unmodified tracked file). Attribution
recipe: `git status --porcelain | grep "^ M"` (tracked modified) vs `??`
(untracked); untracked S10 domain files (routes, factories, docs sessions) are
normal; the ONLY new modified-tracked file must match the packet's bounded
write-set, and protected files (frozen completion-CAS, models.py, frontend)
must be SAME vs your own baseline hash.
