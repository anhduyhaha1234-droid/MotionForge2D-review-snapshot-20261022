# Incident: test file destroyed by worker (MotionForge2D S10-C6G, 2026-09-02)

## What happened
Recovery worker session `20260901_230235_b80d4b` (C14 T1/T2) destroyed
`tests/test_s10_full_apply_api.py`: 2,547 lines (~57 test funcs) → 278 lines.
Mechanism: a `write_file` whose content was only the new C14 additions (14,583 B)
was issued with the MAIN test file path (path collision — intended as an
additions scratch file, landed on the real file). Worker later admitted the
destruction and proposed "rebuild from memory" — blocked by Manager (not
byte-identical; ends the evidence chain).

## Recovery sources discovered (all in `~/AppData/Local/hermes/state.db`)
| Source | Message id | Content |
|---|---|---|
| Base (earliest write_file) | 123043 (session 20260828_003035_859fe5) | 12,369 B initial module |
| C6D tests staged to %TEMP% | 144674 (write_file → `C:/Users/Admin/AppData/Local/Temp/mfc11_c6d_api_tests.py`) | 12,814 B full C6D test section |
| C10 tests in execute_code | 143501 (`api_tests = '''...'''` string) | 9,883 B full C10 tests |
| C14 additions (destroyer's own content) | 146796 / 146875 | 14,583 B `_c6g_run_rows` + 5 test_c6g |
| Ground truth bytecode | `tests/__pycache__/test_s10_full_apply_api.cpython-311-pytest-9.1.1.pyc` | 538,546 B, mtime 23:34:01 (pre-destruction), 57 test funcs via marshal walk |
| Success/failure of every patch | `messages.effect_disposition` joined by `tool_call_id` | the ONLY reliable signal |

## Results
- Reconstruction reached **63 test defs: 57/57 matched pyc ground truth** (0 missing)
  + 5 `test_c6g` + 1 extra; `py_compile` OK after removing junk fragments and
  restoring dotted-filename bug (`_recovered_final.py` → `_recovered.py`).
- Residual: 9 tests failed on **helper-generation drift** — `_make_client`,
  `_payload`, `_seed*` kept an old (C1-C6 era) body because their rewrite
  patches were drift-skipped; overlaying the longest available block fixed
  `_make_client`/`_payload` but the seed helpers still mismatch. Lesson: to
  finish a replay recovery, also overlay NON-test col-0 blocks (helpers) from
  skipped patch new_strings, newest/longest wins, and re-run a real subset.

## Incident escalation (Codex PM decision 2026-09-02) — the real owner + authority
- Read-only state.db proved the ACTUAL writer was **`20260902_013803_4d5ce5`**
  (88 msgs/41 tools, comboBAI; messages 146796/146797 = the destructive
  write_file) — the registry/ledger ID `20260901_230235_b80d4b` was stale
  (4 msgs/1 tool). Recovery must resume the actual owner; never the stale ID.
- The Manager's pyc-based reconstruction was **rejected as authority**:
  Codex ran the reconstructed module — 58 failed/5 passed in 68.12s,
  duplicate `test_submit_distinct_on_changed_checkpoint`, unresolved
  `_C10BoomService`, 64 textual defs/63 collected. Similar line count /
  matching names / compiling / passing some tests is NOT a substitute.
- The original 538,546-byte pyc was **no longer preserved** by review time
  (regenerated pycs mtime 09:48, 584,642 B — from reconstructed bytes).
- Decision: option 2 guarded resume. Phase A = forensic exact-hash recovery
  only, target pre-C14 SHA `963ED50E...` (57 tests); binary candidate gate
  (exact SHA or STOP `BLOCKED_TEST_AUTHORITY`); no write_file/redirection/
  copy-over/memory rebuild; only verified `apply_patch` after exact candidate.
  Second unsafe write ⇒ `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`.

## Read-payload stitching: the C14-T3 primary path (2026-09-02)
- Before destroying the file, the C14 worker had paginated-READ the 2,547-line
  test file (tool `read_file` results carry `N|...` line-numbered content).
- T3's exact-candidate gate therefore starts by exporting every
  `role='tool' AND tool_name='read_file'` row whose result mentions the target
  file, mapping each result back to its assistant `tool_calls` row
  (path + offset/limit) and computing line coverage (`COVERED 1..2547` or the
  exact gap list). Fully-covered paginated reads stitch into a byte-exact
  candidate with NO patch replay — strictly prefer over replay.
- Coverage check also catches the trap where the warned "only read through
  pagination" means the LAST page(s) were never read; if gaps exist, replay +
  col-0 def-block extraction remains the fallback.

## Prevention (see pm-worker-orchestration reference)
- Worker prompts: forbid `write_file` on EXISTING files; allow `patch`
  replace-mode only; staged additions must go to `output/s10/...` evidence
  paths or `%TEMP%`, never to the tracked/test module path.
- Post-turn cheap damage check: record `wc -l`/byte size of each write-set file
  at dispatch; after each worker turn, compare — huge negative delta = red flag
  before any verify/pytest runs.

## Evidence preservation
- Destroyed file kept as `.destroyed_278.py.bak`; recovered file as
  `test_s10_full_apply_api.recovered_final.py`; diagnostics in
  `output/s10/c6g/manager/RECOVERY_REPORT.md`; registry entry appended.
- C14-T3 Manager PREP (PREP_INCIDENT.md + sha256, registry owner-ledger
  addendum, RECOVERY_REPORT correction append) under
  `output/s10/c6g/manager/recovery-t3-prep/`.
