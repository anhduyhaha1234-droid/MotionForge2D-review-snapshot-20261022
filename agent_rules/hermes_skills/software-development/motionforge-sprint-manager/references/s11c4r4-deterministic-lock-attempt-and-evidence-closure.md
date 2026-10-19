# S11-C4-R4 — Deterministic Lock-Attempt + Evidence Closure (2026-09-06)

Class pattern: test-only correction of a true-contention race + hermetic R4 evidence root.
Source: S11-C4-R4 preflight in Manager `20260905_162953_5a5cda`, canonical `4f2c787`, worker tip `d9c439b`.

## 1. Manager identity binding (must precede all dispatch)
- R4 prompt pins exact Manager session; verify `HERMES_SESSION_ID` env equals it.
- Mismatch => `BLOCKED_MANAGER_IDENTITY`, no dispatch, no new manager/watchdog/poll loop.
- Verified here: env `20260905_162953_5a5cda` matched; `hermes sessions list` showed it live.

## 2. Fresh R4 root before any worker message
- Path: `C:/Users/Admin/MotionForge2D-evidence/s11-c4/<ts>-R4-final/` with `manager/`, `snapshots/`, `lanes/r4-resume/`.
- Before resume create: `REGISTRY.md`, 14-row `baseline_manifest.csv` (path/attrib/dirty/SHA/bytes/lines/mtime),
  guard `capture` 10 entries + verified snapshots, raw guard JSON, real append-only `commands.jsonl`.
- `commands.jsonl` row shape: seq, exact cmd, cwd, start/end ISO UTC, reviewed HEAD/tree,
  DB/basetemp/cache/port/output roots, numeric exit, raw stdout/stderr artifact path.
  Index failed attempts too; never reconstruct old commands as if run in R4.

## 3. Dirty-attribution guard (5 untracked incident files)
- Worktree `s11-c4-r2` intentionally retains 5 untracked files under
  `docs/pm/sessions/S11-T03G/evidence/c4r2/` (1 `guard_baseline.json` mtime 20:04:12 + 4 snapshots mtime 19:20).
- Enumerate each absolute path + SHA-256 + bytes + logical lines + mtime; byte-snapshot into
  external R4 root only. Never delete/modify/move/stage/commit; never clean/stash/reset/restore.
- Baseline must show CURRENT committed test hash before R4 patch (here `95eb2e5d` 20741B 554L),
  not an already-patched image.

## 4. Zero-writer + route proof (read-only DB)
- `state.db` only via `mode=ro&immutable=1`; never copy/vacuum/mutate.
- Reconcile stale `ended_at=NULL` rows against live `ps` (pytest/ffmpeg/hermes-chat) + tip/porcelain:
  owner `6da09b` terminal TASK_SUBMITTED (182/84), competing `150b51` frozen at baseline (39/21),
  R1/R0 frozen, INT01 waiting.
- Route: fresh `/v1/models` catalog (142 IDs) => `cmc/meta/muse-spark-1.3-contributor` PRESENT;
  zero-write probe `PROBE_OK` (session `20260906_210511_2a8142`, exit 0). No 1.2/DeepSeek/ocgfree/auto.
- Record actual Manager + worker model/config rows read-only.

## 5. R4 test-only correction shape (nodes stay 6 / 152)
- Exclusive write-set: `tests/test_s11_t03g_qc_check_c4r1.py` + append-only LOG/REPORT. Production frozen.
- Keep A paused INSIDE real explicit-registration op while real `_BOOTSTRAP_LOCK` RLock held.
- Deterministic B-attempt proof (test-only): temporarily replace `handler._BOOTSTRAP_LOCK` in clean
  subprocess with a context-manager probe that delegates acquire/release to the ORIGINAL RLock and
  signals `b_lock_attempted` only for named B thread immediately before delegating. Restore in `finally`.
- Start B while A paused; bounded-wait `b_lock_attempted=True`; while A still owns real lock assert B
  not returned + still live. Only then release A. Fixed sleep / `is_alive()` alone / pre-bootstrap marker is NOT proof.
- Failure paths must release events + restore monkeypatches; all joins bounded.
- Before clearing registry, capture exact expected clean revision map + ordered four-field snapshot
  (name, entry_point, version, description). B returns COMPLETE revision dict; assert == expected 10-entry map.
- Immediately after both joins, BEFORE any repair/bootstrap/cleanup, assert final four-field snapshot ==
  expected + names == exact band order. Preserve A `RunQcChecksError/CONFLICT` + `RuntimeError` cause + R1/R2/BaseException rows.
- Arithmetic: exactly 6 C4R1 nodes, 152 all-T03G nodes. Any change => stop + explain.

## 6. Provenance to retain (never edit R2/R3 history)
- R2 first matrix fail `129 failed, 9 passed, 13 errors` + superseding green run (absolute path + hash or byte copy).
- R2 msg 176346 (2026-09-05 20:04:12 +07) creating the five files + selected session/message/tool rows
  proving exact owner/model/patch ops.
- R3 root inventory proving `commands.jsonl` absent + `lanes/r3-resume/` empty.
- Truthful R2→R3→R4 supersession map; state precisely no tracked production/test byte collision found,
  five untracked writes remain incident evidence.
