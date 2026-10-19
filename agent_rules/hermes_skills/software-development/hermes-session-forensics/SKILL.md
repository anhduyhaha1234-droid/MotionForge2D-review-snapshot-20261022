---
name: hermes-session-forensics
description: "Recover lost files from Hermes session DB and pyc truth."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [recovery, forensics, session-db, sqlite, patch-replay, pyc]
---

# Hermes Session Forensics & Source Recovery

## Trigger
- A worker/subagent overwrote/truncated a file (e.g. `write_file` with the wrong path clobbered a 2,547-line test file down to a 278-line fragment).
- You need the exact edit history of a file across agent turns (audit, evidence, "what did the worker actually do").
- A session claims something ("57 tests pass") and you need independent ground truth.
- A manager prompt demands an EXACT-HASH candidate gate ("recover bytes matching SHA X") — that is a forensic replay job, not a semantic rewrite.

## Core insight
Hermes persists **every tool call with full arguments** in `~/AppData/Local/hermes/state.db`:
- `messages` table: `role='assistant'` rows carry `tool_calls` (JSON array; each element has `function.name` + `function.arguments` — JSON-encoded args including **full `write_file` content**, `patch` old_string/new_string, `execute_code` source, `terminal` command text).
- `role='tool'` rows carry `tool_call_id`, but **`effect_disposition` is often NOT populated** — proven case (C14-T3, 2026-09-02): only **1 of 72,096** tool rows had a value. Do NOT rely on it as the success signal. The reliable signal is the tool result JSON itself: `{"success": true, ...}` + presence of a `diff` field (57/61 patches carried it). Join tool rows to their assistant `tool_calls` row via `tool_call_id` to match call → result.
- `sessions` table: session ids (`20260901_230235_b80d4b` style) and `session_model_usage` (selector/provider/billing).
- Older context may also exist as `request_dump_*.json` in `sessions/` (full conversation payloads).

Every successful `patch` on a repo file is therefore replayable: base content (earliest `write_file`) + ordered successful patches == the pre-destruction file. Patch `old_string` may stop matching mid-chain (generation drift) — but the **`new_string` of those "skipped" patches contains the full new function bodies**; extract them as top-level `def` blocks.

## Recipe (recovery of a destroyed file)
1. **Ground truth first**: `__pycache__/<file>.cpython-311-pytest-9.1.1.pyc` (or plain `.pyc`) is a complete compiled module from the last successful import. Verify its mtime is BEFORE the destruction and its size is plausible (e.g. 538KB for a 2.5k-line test module).
2. Extract authoritative symbol set from the pyc:
   ```python
   import marshal, types
   code = marshal.loads(path.read_bytes()[16:])  # 3.11 header = 16 bytes
   names = set()
   def walk(c):
       for k in c.co_consts:
           if isinstance(k, types.CodeType):
               if k.co_name.startswith("test_"): names.add(k.co_name)
               walk(k)
   walk(code)
   ```
   Compare against `^def (test_\w+)\(` in the reconstruction — **0 missing = strong proof**.
3. Find the base — try READ PAYLOADS FIRST. `role='tool'` + `tool_name='read_file'`
   results whose content holds the target file in line-numbered form (`N|...`) are
   byte-exact snapshots at read time. But FIRST check feasibility — this is NOT a
   guaranteed path. Proven case (C14-T3, 2026-09-02): 116 read pages existed (114
   with line numbers, max line 2548) yet **344 lines had ZERO coverage from ANY
   session** — the composite coverage was only 2204/2548, with 9 gap intervals
   (642–694, 702–710, 742–906, 1046–1078, 1178–1182, 1191–1195, 1845–1894,
   2160–2172, 2310–2320) where no single page (nor any page union, because pages
   overlap) covered the range. The remaining lines were interleaved across **28+
   different file versions** (each edit produced new reads of overlapping slices),
   so cross-page stitching could never be byte-exact. BEFORE stitching: export
   every read page's line-number span into a manifest, compute the union vs
   `1..TOTAL`, and print `"COVERED 1..2547"` OR the exact gap list — if any gap
   exists, byte-exact recovery from reads is IMPOSSIBLE and the correct terminal
   is `BLOCKED_TEST_AUTHORITY / PENDING_CODEX_DECISION` (do not silently fall
   back to a semantic rebuild and claim authority). Fallback: earliest
   `write_file` call whose args path == target file (query `messages` for
   `tool_calls LIKE '%<file>%'`), then ordered patch replay.
4. Replay: iterate `role='assistant'` rows containing the file + `"patch"` in rowid order; resolve success via `tool_call_id → effect_disposition`; apply `old_string→new_string`. For patches whose `old` is NOT found: collect every top-level `def (test_\w+|_c6\w+|\w+)` block from `new_string` (split on `\n(?=def )`).
5. Sections may live OUTSIDE the file: `write_file` to `%TEMP%/...py` (worker staged additions then pasted), `execute_code` with triple-quoted `api_tests = '''...'''` string constants, `terminal` heredocs.
6. Assemble: imports/header from base + replay + col-0 def blocks (dedup by name, keep LAST = newest) + staged sections. Then `py_compile` + name-set check vs pyc.
7. Do NOT overwrite the real file until the reconstruction compiles AND a representative test subset runs. Rename with underscores (`_recovered.py`) — **dots in the filename break pytest collection** (dotted module semantics).

## Owner/session forensics — identify the ACTUAL writer (read-only)

Registry/ledger session IDs can be stale. Proven case (S10-C6G C14, 2026-09-02):
the registry/ledger named `20260901_230235_b80d4b` (4 msgs / 1 tool) while the
true writer was `20260902_013803_4d5ce5` (88 msgs / 41 tools, `end_reason=agent_close`).
Always prove the owner from the DB BEFORE resume; open the DB with a READ-ONLY
URI connection (`mode=ro`), never a write-capable one, and record state.db
size/mtime as evidence.

```python
import sqlite3
con = sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro', uri=True)
cur = con.cursor()
# sessions columns (query by name, NOT SELECT * and NOT 'profile'):
#   id, source, user_id, session_key, chat_id, chat_type, thread_id, display_name,
#   model, model_config, parent_session_id, started_at, ended_at, end_reason,
#   message_count, tool_call_count, cwd, git_branch, billing_provider,
#   estimated_cost_usd, title, profile_name, archived, pinned ...
cur.execute("SELECT id, model, billing_provider, started_at, ended_at, end_reason, message_count, tool_call_count FROM sessions WHERE id=?", (sid,))
# per-role/tool histogram — proves which tools the candidate actually used
cur.execute("SELECT role, tool_name, COUNT(*) FROM messages WHERE session_id=? GROUP BY role, tool_name", (sid,))
# chronological bounds of the session = safe export window
cur.execute("SELECT MIN(id), MAX(id), datetime(MIN(timestamp),'unixepoch','localtime'), datetime(MAX(timestamp),'unixepoch','localtime') FROM messages WHERE session_id=?", (sid,))
# sanity: expected message IDs must be inside the live range
cur.execute('SELECT MAX(id) FROM messages')  # == sqlite_sequence row for 'messages'
```

The decisive discriminator between a stale registry ID and the real writer:
`message_count`/`tool_call_count` — the destructive writer had 88/41, the stale
one 4/1. A candidate with ≤5 messages cannot be the author of a destroyed file.

## Pitfalls (learned the hard way)
- **`is_ok()` on patch tool result content is wrong**: the returned unified diff contains words like "error"/"failed" inside test code → false negatives. Use `effect_disposition` only.
- SQL `%`-LIKE inside `%`-formatted Python strings: ValueError "unsupported format character" — parameterize with `?` placeholders only.
- `threading.Barrier` auto-resets after pass — verifying rendezvous by calling `barrier.wait()` afterwards reports False; count entries inside the wrapped call instead.
- TestClient portal threads can share a thread name — `set(reached)` collapses two participants; count entries, not names.
- `wmic`/PowerShell process scans match their own command line; exclude `$PID` before concluding "no process". Write `.ps1` files and run with `-File`.
- **PYC regeneration trap (C14, 2026-09-02)**: after ANY pytest/import run on the worktree post-destruction, `tests/__pycache__/<file>.cpython-311-pytest-9.1.1.pyc` is REGENERATED with a NEW mtime and a size that tracks the CURRENT (damaged/reconstructed) file — a plain `-cpython-311.pyc` variant may also exist and regenerate separately. Trust ONLY a pyc whose mtime PREDATES the destruction; a post-destruction pyc is good for symbol-name enumeration at best and NEVER as old-source authority. Enumerate BOTH variants (`ls tests/__pycache__/ | grep <module>` + `stat -c '%s %y'` each) before choosing ground truth; the original 538,546 B / 23:34 pyc was the only pre-destruction artifact, and by review time only regenerated 584,642 B pycs remained.
- mkdir the log dir BEFORE `> redirect` (bash fails on missing dir and the run looks like a 0-byte hang).
- **`hermes --resume <id>` of a closed session spawns a NEW session id (C14-T3, 2026-09-02)**: resuming `20260902_013803_4d5ce5` (which had `end_reason=agent_close`) produced a fresh session `20260902_102609_ee5195` (197 msgs) — the old id gained **0 new messages**. Verified by:
  ```python
  cur.execute("SELECT count(*) FROM messages WHERE session_id=? AND id > ?", (old_sid, last_known_id))  # → 0
  # then find the real continuation:
  cur.execute("SELECT id, source, model, started_at, end_reason, message_count FROM sessions ORDER BY rowid DESC LIMIT 8")
  ```
  Lesson: after ANY resume, re-query `sessions` ORDER BY rowid DESC to find where the work actually landed; never conclude "worker didn't run" from the old session id alone. This is also why registry/ledger IDs go stale — a ledger entry naming the previous session is a *pointer*, not a guarantee.
- The same incident class has a PREVENTION side: reference `worker-write-file-collision-destruction.md` under `pm-worker-orchestration` (forbid `write_file` on existing files in worker prompts; post-turn byte/line-count checks).

## Byte-guard violation proof — heredoc/`write_text()` on tracked files

When a prompt bans direct writers (`write_file`, heredoc python, `Path.write_text()`,
redirection over tracked files) and you must prove a violation from the DB read-only
(proven S11-C4-R2, 2026-09-05 — R1 owner wrote `app/workflow/qc_checks_handler.py`
via `python - <<'EOF'` + `p.read_text()`/`p.write_text(t)`):

- There is NO `tool_calls` table (`pragma table_info(tool_calls)` → empty columns;
  `SELECT ... FROM tool_calls` → "no such table"). Payloads live in
  `messages.tool_calls` (JSON array; `function.name` + JSON-encoded `function.arguments`
  with the full `terminal` command text) on `role='assistant'` rows — and those rows'
  `content` is often EMPTY, so filter/dump on `tool_calls`, never on `content` alone.
- Exact-ID proof: `SELECT tool_calls FROM messages WHERE id=?` for each reported
  message id; SHA-256 the returned payload string per id and record
  `id → sha256 → mechanism` (`python - <<'EOF'` + `read_text`, `write_text(t)`,
  `spec_from_file_location` applier script, etc.).
- Screening query on `content LIKE '%write_text%' OR content LIKE '%heredoc%'` catches
  discussion/skill text (noisy — most hits are skill bodies), so always follow up by
  dumping `tool_calls` for the exact neighboring assistant ids; the payload JSON is
  the decisive evidence, not the content match.
- Open read-only with `mode=ro&immutable=1` URI; never copy, vacuum, or mutate the DB.

## VSS shadow copies — byte-exact historical source (third recovery lane)

Before declaring byte-exact recovery impossible, check Windows Volume Shadow
Copies. Proven (S10-C6H, 2026-09-02): the destroyed file's ancestor existed in
ALL 3 shadow copies with IDENTICAL SHA-256 (`5b312719…`, 24,542 B) — a clean
pre-destruction snapshot, unlike pyc (regeneration trap) or read pages (gaps).

1. Enumerate: `vssadmin list shadows` (needs admin) — note the
   `HarddiskVolumeShadowCopy<N>` device names.
2. Access from git-bash/MSYS WITHOUT admin: the path is
   `//?/GLOBALROOT/Device/HarddiskVolumeShadowCopy<N>/<full path>` (e.g.
   `//?/GLOBALROOT/Device/HarddiskVolumeShadowCopy2/Users/Admin/.../tests/test_x.py`).
   `ls`/`sha256sum`/`cp` all work on it; PowerShell `Test-Path '\?\GLOBALROOT\...'`
   also works. No drive-letter mounting needed.
3. Hash-compare each shadow's file against your target SHA before extracting;
   pick the first match (order is oldest→newest). Extract with `cp` into a
   manager evidence dir and re-verify `sha256sum` 1:1.
4. Read the file in LINE-NUMBERED or raw form, then diff against the live file
   to reconstruct what changed post-snapshot. This gives true byte authority
   for the ancestor even when every other lane (git, pyc, read pages) failed.
5. NOTE: VSS is a system-managed snapshot — treat it as authoritative evidence
   only if the shadow's creation time PREDATES the destruction; record
   `vssadmin list shadows` output (IDs/dates) in the evidence file.

## When byte-exact is impossible → REBASELINE evidence (finite name-set method)

When the feasibility gate fails (gaps exist), a rebaseline decision needs a
finite, auditable node list (e.g. "retained 57 tests"), NOT a reconstruction
guess. Build it from ranked evidence sources (proven C6H):

1. **Anchored arithmetic in REPORT.md/LOG.md** — worker reports like
   "57 = 51 retained C8/C9 + 6 C10" give the count AND the composition; grep
   `-o "test_[a-z0-9_]*"` REPORT/LOG and dedup (filter file/module noise:
   `test_s10`, `test_api`, `test_workflow`, `test_c6f`, `test_s10_full_apply_api`
   are MODULE references, not node names).
2. **Read-pages name set** — `^\s*\d+\|\s*def\s+(test_\w+)` from the exported
   read-pages content (the file is `N|...` line-formatted; plain `def\s+(test_\w+)`
   matches 0 rows — the line-number prefix breaks the regex).
3. **Shakeout/pytest warning names** — test names that appear in pytest logs of
   runs against the pre-destruction file (e.g. targeting `-k "submit or
   authority"` ×2) are direct witness of existence.
4. **Set math** — union of sources = candidate list; `REPORT ∪ LOG - pages` ≈
   the names inside the uncovered gaps; document 9/9 gap intervals with no
   covering read page as proof the list is evidence-based, not fabricated.
5. **Patch/contract-proven names** (4th source, accepted by Codex in C6H
   2026-09-02): a name is retained even with ZERO read-page coverage if a patch
   `new_string` payload provably contains it. Query `ops_manifest.json` (or
   `messages` rows with `tool_calls LIKE '%patch%'`), find ops whose
   `new_string` contains `def <name>`, record msg_id + new_string_len
   (proven: a single 17,463-char patch at msg 137694 carried 7 names; plus
   msg 139874 and 145257 → 9 patch-proven names total).
6. **Deterministic disposition**: obsolete test = added in patch msg A,
   removed/replaced in msg B (A<B), ABSENT from all authoritative read pages,
   and superseded by a replacement visible in late reads (late-read msg ids as
   witnesses). Duplicate name = keep the FIRST current definition; mark the
   second as stale reconstruction duplicate when pre-destruction read evidence
   shows exactly one definition.
7. **Arithmetic & persistence**: `retained = pages_names + patch_proven_names`;
   `target = retained + C6G_names`; sanity check: current textual defs −
   obsolete − dup = target (C6H: 48 + 9 = 57; 57 + 5 = 62; 64 defs − 1 obsolete
   − 1 dup = 62 ✓). Persist `AUTHORITY_SOURCE_LEDGER.md/json` (per-test
   msg_ids/sessions provenance, byte counts, SHAs) + `RETAINED_<N>_MATRIX.md/json`
   (N rows: node, evidence source, setup/action/expected, durable-state
   invariant, disposition) IN THE SAME TURN — a progress report without these
   artifacts is a stall, not progress (Codex verdict: `PREP_R_STALL`).
8. Emit the verdict as `RETAINED_<N>_MATRIX` (or similar) with per-node source
   provenance, and record it as the R-GATE ground truth for the rebaseline.

## Support files
- `scripts/recover_patch_history.py` — parameterized replay: auto-detect base write_file, replay successful patches, extract col-0 def blocks from drift-skipped patches, emit recovered file + diagnostics.
- `references/incident-c14-testfile-recovery.md` — full worked case (MotionForge2D C6G): message ids, pyc ground truth, read-payload stitching, owner-identity discriminator, results and the residual helper-generation mismatch lesson.
- `references/incident-c14-t3-forensic-negative.md` — the T3 negative result: read coverage feasibility gate, 344-line gap forensics, `effect_disposition` unusability, resume-spawns-new-session pitfall, Manager verification checklist, BLOCKED_TEST_AUTHORITY terminal.

## Verification checklist
- [ ] pyc ground-truth symbol set extracted BEFORE touching files
- [ ] reconstruction compiles (`py_compile`)
- [ ] symbol set: 0 missing vs pyc
- [ ] representative test subset actually runs (not just imports)
- [ ] original destroyed file preserved as `.bak` before overwrite
- [ ] recovery provenance appended to project registry/LOG
