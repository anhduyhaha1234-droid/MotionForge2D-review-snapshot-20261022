# Git-managed read-pages reconstruction (S10-C6H PREP-R, 2026-09-02)

How to rebuild a destroyed test file's node inventory + provenance WITHOUT the
file, when the only ground truth is Hermes' own `state.db` read-pages. This
produced `AUTHORITY_SOURCE_LEDGER` (48 read-pages + 9 patch-proven = 57
retained) + `RETAINED_57_MATRIX` (57/57 rows) from the recovery evidence.

## Inputs (already extracted into `output/s10/c6g/t01c-c14/recovery-t3/`)

- `read_pages_manifest.json` — 116 records: `{assistant_msg_id, session_id,
  call_id, path, offset, limit, tool_msg_id, content, content_len,
  content_sha}`, where `content` is `N|line`-numbered read_file output.
- `ops_manifest.json` — 64 records: `{msg_id, session_id, kind (write_file|
  patch), mode, path, content_len, old_string_len, new_string_len, content,
  old_string, new_string, effect_disposition}`.

## Step 1 — name inventory with provenance (pages)

```python
prov = defaultdict(lambda: {'msg_ids': set(), 'sessions': set(), 'pages': 0})
for item in read_pages:
    for m in re.finditer(r'^\s*\d+\|\s*def\s+(test_\w+)\s*\(', item['content'], re.M):
        prov[m.group(1)]['msg_ids'].add(item['assistant_msg_id'])
        prov[m.group(1)]['sessions'].add(item['session_id'])
        prov[m.group(1)]['pages'] += 1
```
Gives unique name set + `msg first..last` range per name. NOTE: names are
deduped — `test_authority_fingerprint_equality_plan_manifest` appeared 4 times
pages/4 defs (re-reads), so pages count ≠ def count.

## Step 2 — patch-proven names

For each candidate name NOT in the pages set, scan `ops_manifest` for
`name in op['new_string']`; the op's `msg_id` is the provenance. A name whose
only appearance is inside a patch `new_string` is patch-proven.

## Step 3 — arithmetic reconciliation

- current file: `re.findall(r'^def (test_\w+)\s*\(', src, re.M)` → count
  defs, unique defs, duplicate names (`dup = [n for n in set if count>1]`).
- target = retained (48 pages + 9 patch) + C6G (5) = 62.
- obsolete name: added at msg 145447, removed/replaced 145471, absent in all
  pages, superseded by `test_c6e_replay_vs_retry_barrier_fail_closed`
  (present in late reads 146000/146518/146695).
- duplicate `test_submit_distinct_on_changed_checkpoint`: 2 defs in current —
  keep FIRST (semantic contract), drop second (stale reconstruction duplicate;
  pre-C14 read evidence has exactly one definition).
- Check `64 textual − 1 obsolete − 1 duplicate = 62` exactly.

## Step 4 — bodies WITHOUT the file

Extract def blocks from the CURRENT (modified) file for setup/action/expected
docstrings, and from `ops_manifest` `new_string` for the 9 patch-proven tests
(find `'def ' + name` in `new_string`, slice ~900 chars). The authoritative
read-pages give the ORIGINAL shape — always diff current vs pages, never
current vs current backup (circular).

## Step 5 — persist in the same turn (stall-avoidance rule)

`AUTHORITY_SOURCE_LEDGER.md` (13,880 B, SHA 8E4E91D7… in C6H) +
`.json` (24,096 B) and `RETAINED_57_MATRIX.md` (14,507 B) + `.json` (52,055 B)
under `output/s10/c6h/manager/prep/`; then `write_set_guard.py capture`
(route + test) BEFORE dispatch; registry append of the worker session id
BEFORE its first write.

## Key facts from this case (reusable invariants)

- P383 verification: test SHA must CHANGE (rebaseline is semantic, NOT
  `RESTORED_EXACT` — never say "restored exact" for a file rebuilt from
  evidence). Route SHA must STAY frozen.
- Guard manifest entries are `{exists, lines, path, sha256, size, snapshot,
  snapshot_sha256}` — `write_set_guard.py verify` after every writer stop.
- VSS ancestor (13 tests, SHA 5B312719…) is a separate evidence source — not
  the authority target (57), but its 13 rows must all be covered by the final
  file (subset check, not superset).
