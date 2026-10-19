# Worker write-file collision destruction — prevention & detection

Incident: MotionForge2D S10-C6G (2026-09-02). A recovery worker destroyed its
own task's test file (`tests/test_s10_full_apply_api.py`, 2,547 lines → 278)
by issuing `write_file` with the NEW-section content against the REAL file path
(scratch-vs-target path collision). Full recovery playbook:
`hermes-session-forensics` (state.db patch replay + pyc ground truth).

## Prevention (encode in EVERY worker/resume prompt)
1. **No `write_file` on existing files.** Allowed edits on pre-existing
   production/test modules: `patch` replace-mode ONLY (old_string → new_string,
   context-unique). New files only via `write_file` to a NEW path.
2. Staged/additions content goes to the task's evidence dir
   (`output/s10/<packet>/<task>/**`) or `%TEMP%/...`, never to the module path.
3. If a full rewrite is genuinely needed, requirements change → stop
   `BLOCKED_DEPENDENCY / SCOPE_EXPANSION_REQUIRED` instead of rewriting.

## Detection (cheap, per-turn, Manager-side)
- At dispatch: record `wc -l` and byte size for EVERY file in the exclusive
  write-set (or sha256 — cheap enough for a handful of files).
- After each worker turn: re-stat. A large negative delta (`2547` → `278`) or
  a missing reference is a red flag — verify before running any pytest/evidence
  and before trusting `TASK_SUBMITTED`.
- Worker GUARDS (file-edit verifier tools) are advisory: C14's own verifier
  flagged "1 file NOT modified this turn" only AFTER the damage.

## If destruction already happened
1. STOP the worker; do NOT resume it for the same file until restored
   (same session MAY be resumed for OTHER code, but mark it high-risk).
2. Do NOT accept "rebuild from memory/evidence" proposals — not byte-identical.
3. Recover from `~/AppData/Local/hermes/state.db` (see `hermes-session-forensics`
   SKILL.md: base write_file + ordered successful patches + col-0 def blocks
   from drift-skipped patches + staged sections + `__pycache__` pyc ground truth).
4. Keep the destroyed file as `.bak`, write a RECOVERY_REPORT at the manager
   evidence path, append registry/LOG entry; escalate to Codex/user for
   disposition (align-helpers vs worker-resume with hard constraints vs
   regenerate).

## C14 follow-up: the guarded-resume recovery contract (2026-09-02)
The Codex PM decision (option 2) authorized ONE guarded resume of the ACTUAL
writer with a forensic Phase-A. Contract proven effective:
1. **Owner-ID correction is append-only, never a rewrite** — the stale
   `20260901_230235_b80d4b` ID in the registry stays as history; the addendum
   names the true writer `20260902_013803_4d5ce5` (88 msgs/41 tools from
   state.db, `mode=ro`). Prove zero live writer via process/cmdline scan +
   `end_reason` before resuming.
2. **Phase A = zero production edit.** Worker writes ONLY: recovery evidence
   (`output/.../recovery-t3/**`), append-only LOG/REPORT, and — only after an
   exact-hash candidate exists — the recovered test file via verified
   `apply_patch` hunks. The production route file and every other file stay
   frozen. No production edit before Manager R-GATE.
3. **Forbidden list in the resume prompt is literal**: no `write_file`,
   `Set-Content`/`Out-File`, shell redirection, heredoc, Python direct write,
   `Copy-Item`/`Move-Item` replace, editor save, memory rebuild, Git
   destructive recovery, pyc-as-source, skip/xfail/weaken.
4. **Candidate gate is binary hash** (`963ED50E...` for C14): similar line
   count / compiles / passes subset / matches docstrings are ALL insufficient.
   Exact-hash failure => `BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION`,
   keep candidates, touch nothing.
5. **One recovery message interval = the "missing payload" report**: if the
   exact hash cannot be reached, the guard-rails produce a precise
   "message interval N..M + payload shape" so Codex can rule fast instead of
   another guessing round.
6. **Any repeat unsafe write => `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`**
   — no third resume, no Manager-created replacement session.
