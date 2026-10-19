# DV3-R2 T00 dispatch liveness + gating notes (2026-09-08)

Session: NEW demo-only Manager `20260908_165201_c0780f`, lane MF-DEMO-V3-R2.
Worker route: `ocgfree/muse-spark-1.3-contributor-free`, reasoning max, fallback OFF
(same model as the manager chat, per user instruction).

## 1. Zero-byte dispatch log ≠ dead worker

- `dispatch-T00-R1.log` stayed **0 bytes for the whole run** (shell `>>` redirect
  buffering); the worker's final report + `EXIT-T00-R1=0` flushed only at process exit.
- Meanwhile disk truth grew: 11 evidence files 17:18–17:25 (+07), a new worker
  session `20260908_171606_cc8417` in `hermes sessions list`, wrapper process alive.
- Rule (extends the skill's truncated-log guidance): even ZERO bytes can be healthy.
  Liveness = evidence-dir mtimes + wrapper process + sessions list — never log size
  alone. Kill only on the real stall signature (frozen log AND frozen evidence,
  leaf-CPU creep check first).

## 2. Bounded completion watchdog instead of manual polling

- A manager sharing the same model/upstream as its worker must not poll in tight
  loops (burns in-flight budget → 402 contention on the shared router).
- Pattern used: one bg watchdog polling `T00/REPORT.md` for the `STATUS:` marker
  every 60s, 90-min cap, `notify_on_complete=true`, self-exits on marker (fired
  after 2 min here), START/END rows in `commands.jsonl`.
- Not a 24/24 watcher: bounded, single-run, no recurrence — task packs forbidding
  permanent automation stay honored while the user's "chay lien tuc" (keep chaining
  without re-asking each step) is satisfied by immediate same-turn chaining on EXIT.

## 3. ETA answers ("bao lau thi xong")

- Lead with current status, then a table with DATE anchors (VN + UTC), per-milestone
  conditions, buffer for worker-death + reasoning-max included, and a promise of
  instant-notify on slip. Never give a bare duration.

## 4. Mechanism-proven vs actor-unproven (F05 shape)

- Drift confirmed + mechanism identified (S01 pre-upgrade backup 04:48:59 UTC hash ==
  baseline, upgrade landed 04:49:00 UTC: +20 empty tables, `artifact` +width/height,
  311296→1011712 B, zero data-row change) but the launching actor UNPROVEN.
- Correct close: name the EXACT missing evidence (4 items in DB_DIFF.md), keep the
  finding OPEN, keep code activation blocked for a PM decision, never
  rebaseline-to-hide. A bounded mechanism is not attribution.

## 5. Model-id transposition probe

- User-typed `ocgfree/muse-spark-contributor-1.3-free` vs session-exact
  `ocgfree/muse-spark-1.3-contributor-free` — both ponged. Dispatch used the
  session-exact id taken from `agent.log turn_context` for the manager session;
  the probe matrix went into the registry as route evidence.
