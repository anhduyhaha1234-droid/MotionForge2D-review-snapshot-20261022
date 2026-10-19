# INT01 merge + per-dir gates + F-OBS-01 stale-test trap (S12-C1)

Session: S12-C1 closing the real export path (MotionForge2D). All C1
corrections TASK_SUBMITTED; Manager ran INT01 (Git-only integration owner):
merge 3 correction commits into canonical, run final gate, push, packet.

## 1. Worker "ack-but-no-progress" loop — the fix pattern

This session hit the recurring failure: an exact-owner worker resumes, prints
`RULES_LOADED` / `TARGET checklist` / a one-line ack, then goes silent for
30 min+ with no gate output and no commit. Re-nudging with the same open-ended
prompt just produces another ack. This burned hours across T03C, T06A, T06B.

What worked (Manager-side, without touching implementation bytes):
1. Stop re-sending open prompts. Manager self-runs the gates in the worker's
   worktree (read-only verify is the Manager's job — not a role violation).
2. Send a "COMMIT-ONLY / COMMIT-VERIFIED" prompt that states the exact gates
   the Manager already ran + their real numbers, and instructs the worker to
   do ONLY the git add/commit with an exact message and report SHA + porcelain.
   Phrase it as "Manager đã tự chạy 3 gates thật … việc của bạn CHỈ LÀ: git add
   … + git commit -m '…' + báo SHA". This is dramatically more reliable than
   "do the task now".
3. When a worker says it saw an error (e.g. "Lỗi tool C22"), have it give a
   precise 4-line triage (which tool, which command, which file, traceback)
   before reacting — C22 turned out to be a stale terminal-call artifact, not
   a test failure, and the worker's own suite was green.

## 2. pytest full-tree collection fails on duplicate basenames

`tests/s12/s12-t0X/test_c1_closure.py` appears in many task dirs. Some dirs
lack `__init__.py` (T01/T02/T04A), so `pytest tests/s12/` dies at collection
with `import file mismatch: imported module 'test_c1_closure' ...`.
`--import-mode=importlib` then fails differently (`ModuleNotFoundError:
conftest`). The clean fix without touching code: run per-directory with a
SHORT basetemp under `%TEMP%`:
`pytest tests/s12/s12-t0X -q --basetemp=C:/Users/Admin/AppData/Local/Temp/s12_<t0X> -p no:cacheprovider`
and sum the per-dir results for the final-gate number. Also: long basetemp
paths (deep evidence trees) cause `FileNotFoundError [WinError 3]` on tmp_path
mkdir — always use a short temp root.

## 3. Stale-test trap after a cross-owner fix

T06B `test_f3_provenance_decides_not_filesize` asserted the OLD buggy behavior
of `classify_source_kind` (dims-only → `native_4k`, documented as F-OBS-01
"route to owner T01"). T01-C1 then FIXED the bug in production
(`preflight.py` now returns `upscale_4k` for bare dims ≥3840x2160). After the
merge, T06B's own suite failed on the integrated tree even though it passed on
the worker's branch.

Lesson: when a verifier/acceptance test documents an open finding
("F-OBS-01, don't fix, assert current behavior"), and the owning task later
lands a fix, the verifier test MUST be updated by its owner in the same
correction wave or it will break the final INT01 gate. The Manager should grep
for "F-OBS-01 / known-finding assertions" during merge-gate and route the
test update to the test owner (never edit the test yourself).

## 4. INT01 merge sequence that worked

- Verify canonical clean local==remote (0d2e063), then
  `git merge --no-ff <correction>` per task in DAG order, porcelain 0 + diff-check after each.
- Full-tree pytest collection is unreliable (see #2) → per-dir short-basetemp gates.
- After merge + gates green → push, verify `ls-remote == local`, write packet.
