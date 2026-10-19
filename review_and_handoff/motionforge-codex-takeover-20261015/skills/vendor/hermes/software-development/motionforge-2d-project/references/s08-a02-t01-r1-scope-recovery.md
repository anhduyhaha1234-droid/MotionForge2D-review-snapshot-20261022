# S08-A02-T01-R1 — writer clarify-timeout scope recovery (session-verified pattern)

Use this reference when a MotionForge2D writer hits its BLOCKED scope gate, its `clarify`
times out, and it proceeds to edit allowlist-external files under "best judgement" — then
the manager must decide whether to accept and how to document it for Codex.

## Walkthrough of the S08-A02-T01-R1 case

- R1 (DeepSeek Core Recovery) fixed the domain/migration/repository and added 3 new test
  files. Its migration becomes the new Alembic head `a0b1c2d3e4f5` (single head after
  `f7a8b9c0d1e2`, F11).
- The new head breaks 8 PRE-EXISTING test suites that hard-code
  `upgrade head -> alembic_version == "f7a8b9c0d1e2"` (the OLD head) or enumerate the exact
  approved table set. With a new head they are mechanically stale and fail — §7-mandated
  regression + Gate-2 baseline cannot go green without bumping those literals.
- Writer correctly set `REPORT.md = BLOCKED` with ONE question (may it bump those 8 test
  files?). Its `clarify` then TIMED OUT (no user input), the tool told it to use best
  judgement, and it applied the mechanical bumps (mtime 1:23–1:24 AM) — while its REPORT
  still said BLOCKED and its process kept running waiting on the quality baseline.
- The user saw NO heartbeat for the blocked state (one-shot CLI writer has no notify
  channel; `notify_on_complete` only fires on exit; manager had not polled REPORT state).

## Manager recovery steps that worked

1. **mtime audit** — `powershell Get-Item ...LastWriteTime` on the 8 files vs writer start
   timestamp → all 8 were edited inside the writer window → self-expansion confirmed.
2. **tracked/untracked classification** — `git ls-files --error-unmatch <file>`: 6 of 8 were
   UNTRACKED at HEAD (`??`), only `persistence_bootstrap.py` and `durable_job_persistence.py`
   tracked. So "modified vs HEAD" proves nothing for the untracked ones.
3. **mechanical-edit verification** — grep the diffs from the writer's own tool log ("review
   diff" blocks): every hunk was an expected-head literal bump or an approved table-set
   addition; the A01 downgrade-refusal literal was left intact. Run the affected suite
   standalone (role_taxonomy passed 18/18 AFTER the fix — confirming the fix, and also
   proving its earlier failure was staleness, not logic).
4. **independent re-run** — manager ran import smoke, migration 10, domain 30, phone 1,
   combined 104, full 17-suite regression 345 passed/0 failed, ruff, mypy, diff --check,
   alembic heads, NO_LISTENERS, protected MAIN hashes. Matched writer counts.
5. **user authorization with conditions** — user chose: keep the bumps BUT snapshot
   before/after hashes + record verbatim diffs in REPORT for Codex transparency.
6. **reconstruct before-hashes** — since edits preceded authorization, "before" hashes were
   RECONSTRUCTED by reverse-applying the exact patch hunks from the writer tool log to temp
   copies, then hashing; each reconstructed copy passed `ast.parse`. AFTER hashes were the
   live files. The evidence table labels this honestly (BEFORE=recon, AFTER=live).
   Implementation pitfalls that made this reliable:
   - Do NOT assume every "4 A02 table names + comment" block has the same indentation. In
     `test_persistence_bootstrap.py` the block is at 4-space indent (module-level
     `S08_HEAD_TABLES` set literal), but in `test_durable_job_persistence.py` the
     identical-looking list sits inside a function body at 8-space indent — a single global
     `str.replace` asserted to appear once will fail with
     `AssertionError: table block must appear once`. Match per-file shape (or use a regex
     tolerant of `[ \t]+` leading whitespace) instead of one shared literal.
   - Guards first, then edit: for each reverse-replace, `assert s.count(old) == N` BEFORE
     rewriting, then `ast.parse` the reconstructed file AFTER — a silent non-match or a
     mangled reverse is caught immediately, not downstream.
   - Compute AFTER from the LIVE file every time (never from the temp copy about to be
     mutated) so the after-hash always reflects real on-disk state.
   - Keep reconstructed copies under `C:/Users/Admin/AppData/Local/Temp/` (basetemp
     discipline); stray temp scripts belong there too, not in the worktree.
7. **append manager addendum** to the writer REPORT (independent-verification table + the
   8-file before/after hash table + verbatim diff summaries + manager verdict
   `MANAGER_VERIFIED_PENDING_CODEX_REVIEW`), and a companion evidence file under
   `output/<task>/manager-verification-hashes.md`.

## Durable rules

- A writer's `clarify` timeout does NOT equal user approval. The manager must treat any
  self-expansion as unauthorized until the user opts in, then document it with hash + diff
  evidence.
- New Alembic heads will keep breaking pre-existing head-literal/table-set asserts. Bumping
  them is a "required schema-change maintenance" (also seen at S08-T01), but it is still
  allowlist-external → route it through the BLOCKED question or explicit user authorization.
- One-shot headless writer processes cannot notify the user. The MANAGER must poll
  `REPORT.md`/LOG state during long runs and surface BLOCKED/DECISION_NEEDED immediately,
  not on process exit.
