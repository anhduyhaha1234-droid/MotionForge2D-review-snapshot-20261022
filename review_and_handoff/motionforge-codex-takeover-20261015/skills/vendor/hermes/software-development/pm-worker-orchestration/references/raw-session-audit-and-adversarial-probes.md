# Raw-session audit, gate-command recovery, and adversarial probes (S10-C6H R3-proven)

Manager post-worker evidence techniques for correction rounds. All read-only,
Windows/MSYS. These go AFTER worker exit, on frozen bytes.

## 1. Raw tool-call audit — exact state.db recipe

The `messages` table has NO `tool_input` column. Assistant tool calls live in
the `tool_calls` JSON column; tool results are `role='tool'` rows with
`tool_name` + `content`.

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
sid = '<effective worker session id>'
cur.execute(\"SELECT id, role, tool_name, tool_calls, content FROM messages WHERE session_id=? ORDER BY rowid\", (sid,))
for r in cur.fetchall():
    d = dict(r)
    if d['role'] == 'tool':
        # tool result: d['tool_name'], d['content']
        pass
    elif d['tool_calls']:
        for tc in json.loads(d['tool_calls']):
            fn = tc.get('function', {}).get('name', '')
            args = tc.get('function', {}).get('arguments', '')
            # flag: patch mode=replace, write_file on existing source,
            # cp/copy/move/restore, terminal redirection '> app/...' or '> tests/...'
"
```

Acceptance for "unified-patch-only" (what a compliant worker looks like, so you
don't false-flag it):

- **`git apply` hunks are a valid unified-patch mechanism** — pattern seen in
  R3: `git apply --check <hunk.patch> && git apply --whitespace=nowarn <hunk.patch>`,
  then immediately `sha256sum` + `stat -c %s` + `wc -l` + `python -m py_compile`
  per hunk, one hunk per call, EOL-preserving (CRLF test file stays CRLF).
  Intermediate hashes changing 2604→2601 lines across two hunks is normal
  (comment hunk then mechanism hunk).
- `patch` tool calls against `%TEMP%` probe files are NOT critical writes —
  only flag them when they target source/test paths.
- Evidence redirections (`> output/<round>/worker/*.log`) are fine; only
  redirections onto `app/` or `tests/` paths are forbidden.
- Zero `write_file`/`cp`/`replace` on critical files + exactly one worker
  process = audit PASSED even if the mechanism is `git apply` rather than the
  `patch` tool.

## 2. Recover exact historical gate commands from state.db

When LOG/REPORT/packets record counts ("broad 290/290 ×2") but omit the exact
pytest invocation, reconstruct it from the retired Manager session's tool calls
(its `tool_calls` JSON is kept in state.db): scan terminal calls for markers
like 'BROAD R2' and print the full `"command"` value.

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('file:C:/Users/Admin/AppData/Local/hermes/state.db?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute(\"SELECT tool_calls FROM messages WHERE session_id='<old manager id>' AND tool_calls IS NOT NULL ORDER BY rowid\")
seen = set()
for r in cur.fetchall():
    for tc in json.loads(r['tool_calls']):
        fn = tc.get('function', {}).get('name', '')
        args = tc.get('function', {}).get('arguments', '')
        if fn == 'terminal' and 'BROAD R2' in args and args[:60] not in seen:
            seen.add(args[:60]); print(args[:1100])
"
```

Use this to replicate the EXACT same file list/basetemp pattern for the next
round (S10 broad = 9 files: chunk_plan + full_apply_api + full_apply_domain +
full_apply_migration + full_apply_workflow + multi_role_apply +
partial_recompute + structural_compare + s09_t06_backend_authority; focused =
api + workflow).

## 3. Manager adversarial probe — different variant, real stack

Binding prompts require a Manager probe using a legal whitespace/format
combination NOT copied from the worker's test. Pattern that works:

- New pytest file under `output/<round>/manager/probe/` (manager-owned
  evidence, outside `tests/`).
- Load the writer test module AS A LIBRARY for its real-stack seeding helpers
  (real FastAPI route + JobService + fresh Alembic SQLite), then implement
  your OWN probe logic:
  `importlib.util.spec_from_file_location('wl', root/'tests'/'test_s10_full_apply_api.py')`
  + `sys.modules` registration (tests/ is not a package).
- Path depth gotcha: from `output/s10/c6h/r3/manager/probe/`, worktree root =
  `Path(__file__).resolve().parents[6]` (parents[0] is the file's own dir).
- Run with short basetemp `%TEMP%/mfc15r3probe` and `-p no:cacheprovider`;
  DB env UNSET.
- R3 example: worker test used `"run_id"\t:\t"<id>"`; Manager probe used
  `"run_id"\n:\n"<id>"` AND `"run_id"\r\n:\r\n"<id>"` (2 tests, 4.83s) —
  both fail-closed 409/422, same job id, zero replacement job.