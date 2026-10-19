# Incident C14-T3 — forensic recovery NEGATIVE result (2026-09-02)

The follow-up to `incident-c14-testfile-recovery.md`. Same incident (MotionForge2D
S10-C6G: C14 worker `20260902_013803_4d5ce5` destroyed `tests/test_s10_full_apply_api.py`,
2,547 → 278 lines via `write_file` msg 146796/146797), but this session ran the
**full Phase-A forensic recovery per Codex option 2** and proved byte-exact recovery
was IMPOSSIBLE. Terminal: `BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION`.

## What the worker (session `20260902_102609_ee5195`, 197 msgs) found

Left-click identity: Codex PM decision already established the true writer is
`20260902_013803_4d5ce5` (88 msgs/41 tools), NOT the stale registry
`20260901_230235_b80d4b` (4 msgs/1 tool). Read-only state.db queries:
`SELECT id, source, model, started_at, ended_at, end_reason, message_count, tool_call_count
FROM sessions ORDER BY rowid DESC` and per-session
`SELECT role, tool_name, COUNT(*) FROM messages WHERE session_id=? GROUP BY role, tool_name`.

Pipeline (scripts + manifests, all in `output/s10/c6g/t01c-c14/recovery-t3/`):
`discover_test_sources.py` → `extract_read_pages.py` → `walk_ops.py` →
`build_linemap.py` → `replay_history.py` → `replay_newstring.py` →
`stitch_final.py` → `composite_authority.py` → `feasibility.py` →
`authority_audit.py`.

### Numbers (all verified by Manager independent re-check)
- Read pages: 116 total; 114 carry line numbers; max line seen 2548.
- Composite coverage: 2204 distinct lines present; **344 lines MISSING** —
  gaps `642–694, 702–710, 742–906, 1046–1078, 1178–1182, 1191–1195, 1845–1894,
  2160–2172, 2310–2320`. Manager re-check: for every gap interval, ZERO pages
  fully covered it (independent script over `read_pages_manifest.json`).
- Ops targeting the file: 64 (61 patch + 3 write_file). `effect_disposition`
  populated on 1/72,096 tool rows → unusable; used tool-result unified diffs
  instead (57/61 `success:true`).
- Diff replay stopped ~line 1239 (38 applied / 24 drift-skip).
- `new_string` replay = SHA `F72B499A…` = the EARLY 28-test v3 variant, not target.
- Git: file untracked (never in HEAD); no stash/reflog/refs carried the pre-C14 bytes.
- Pyc: original 538,546 B clean pyc NOT preserved; current pyc (584,642 B @09:48)
  regenerated from reconstructed bytes — invalid as source truth.
- Target pre-C14 SHA `963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`
  (57 tests, 2547 lines) = C13-final, confirmed at msgs 146192/146286/146332.
- Candidates produced (none matched target): candidate_exact `024c38be…`,
  candidate_newstring `f72b499a…`, candidate_stitch `4bfff3ec…`,
  composite_candidate `4acc4e65…`.

## Why byte-exact was impossible (deterministic argument, not guesswork)
1. 344 lines had zero read coverage from ANY session (all reads since session start).
2. Remaining lines belong to 28+ different file versions — page overlaps are
   version-fragmentary, so stitching cannot be a single consistent snapshot.
3. Patch replay blocked at the drift boundary (~1239); no deterministic path to 2547.
4. No git history (untracked file), no valid pyc ground truth.
⇒ NO candidate can equal `963ED50E…`. Producer of this conclusion correctly did
NOT touch the main test file (kept `DAD70AE3…`, 2692 lines, 64 textual defs /
63 collected, duplicate `test_submit_distinct_on_changed_checkpoint`,
unresolved `_C10BoomService` 10 refs / 0 def).

## Manager-independent verification checklist that made the claim trustworthy
- `sha256sum tests/test_s10_full_apply_api.py` → `DAD70AE3…` unchanged.
- `sha256sum app/api/routes/s10_full_apply.py` → `6ADCC48A…` frozen.
- `git status --porcelain | wc -l` → 66; HEAD `d3f6f796…`; branch `codex/s08-integration`.
- Coverage re-check: 9/9 gaps had zero fully-covering pages.
- New-session check: `SELECT count(*) FROM messages WHERE session_id=? AND id>146913`
  → 0; real continuation `20260902_102609_ee5195` found via `sessions ORDER BY rowid DESC`.
- Process scan: no live worker; task ports free; state.db untouched (mode=ro).

## Outcome & next steps
- Terminal: `S10-C6G = BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION`.
- Evidence: `output/s10/c6g/manager/recovery-t3-prep/{PREP_INCIDENT,MANAGER_VERIFY_T3}.md`
  + registry append 10:56 + worker evidence under `recovery-t3/`.
- Awaiting Codex decision among: (a) accept non-byte-exact reconstruction
  (DAD70AE3 already has all 64 defs; only helper-generation/dedup drift),
  (b) supply alternate source (VSS snapshot 08-30? copy in another repo/backup),
  (c) formally close C6G as BLOCKED_TEST_AUTHORITY.

## Reused next time
- Read-coverage feasibility gate BEFORE investing in stitching (see SKILL.md §3).
- `effect_disposition` unreliable → parse tool result JSON (`success` + `diff`).
- After ANY `hermes --resume`, re-query `sessions` for the real continuation id.
