# S12-C1 W4 T03C — unmocked repro fix + lightweight session-switch re-anchor (2026-09-08)

Context: user switched to a fresh lightweight session mid-sprint
("doi session cho do nang context") = explicit owner-transfer authorization.
New session `20260908_141259_24fac4` re-anchored live state before continuing;
T03C owner `20260907_144542_7d5dbf` still alive (active 3m before check).

## 1. Session-switch re-anchor (new session must do this FIRST, no memory)

- Canonical moved while old context was away: `e1474af` → `0d2e063`
  (C1 merges T01-C1 + T02-C1-fix + T03A-C1 + T04A-C1 + T03B-C1 all landed,
  local==remote, porcelain 0). Never dispatch off the previous session's pins.
- Task tips advanced independently — re-read every tip + porcelain:
  T01 `0d5bc77` / T02 `81793a8` / T03A `39442d1` / T03B `bd3d9d5` /
  T04A `d60de45` CLEAN; T03C still @ `8f80fe3` + ONE untracked
  `tests/s12/s12-t03c/test_c1_repro_typeerrors.py` (89 lines, repro in flight);
  T05 `4a3630a` / T06A `ddc5d05` / T06B `48bf514` CLEAN.
- Owner liveness: `hermes sessions list` default shows ~22 rows and HIDES
  older owners — absence from the short list is NOT death. T03C owner active
  minutes ago ⇒ resume exact owner, never open a replacement worker.
- Old Manager `20260905_162953_5a5cda` absent from the short list after
  switch; transfer was explicitly user-authorized, so no rival-integrator
  conflict — record verbatim order + old→new IDs in ERRATA/registry same turn.

## 2. T03C unmocked-repro recipe (publication suite mocked `_load_chunks`)

Repro file `tests/s12/s12-t03c/test_c1_repro_typeerrors.py`, outcomes:
- R1 PASS (caught real TypeError): `ChunkSpec.__init__() missing 1 required
  positional argument: 'content_hash'` — `publication._load_chunks`
  built `ChunkSpec(...)` without `content_hash` (row HAS `row.content_hash`).
- R1b FAIL-useful: `_load_chunks` checks file existence BEFORE constructing
  `ChunkSpec`, so a fake `chunk_dir` raises
  `PublicationError: verified chunk file missing` first — repro needs a REAL
  chunk file in `tmp_path` to pass the gate and reach the constructor.
- R2 PASS (caught real TypeError):
  `File "publication.py", line 141, in _require_ready` —
  `compute_project_readiness(session, workspace_id, project_id)` raised
  `TypeError: takes 1 positional argument but 3 were given`
  (signature is `(session, *, workspace_id, project_id)`, keyword-only).

Fixes (both in `app/services/s12_export/publication.py`, T03C allowlist):
- `_require_ready`: call with keywords
  `compute_project_readiness(session, workspace_id=..., project_id=...)`.
- `_load_chunks`: pass `content_hash=str(row.content_hash)`
  (+ `attempt=int(row.attempt)`) into `ChunkSpec(...)`.
- Fix R1b repro to create a real chunk file, re-run repro + full task suite
  + `ruff check --select F` + `git diff --check`, commit LOCAL allowlist,
  then TASK_SUBMITTED + SHA. NO push/merge (INT01 owns integration).

## 3. Rule restated

Every publication/wiring lane needs ≥1 test driving the REAL loader + REAL
readiness chain on an isolated DB. A green suite with those seams mocked is
not closure evidence. First correction nudge orders the unmocked repro
(exact test name + last 20 traceback lines + root cause) BEFORE any fix.
