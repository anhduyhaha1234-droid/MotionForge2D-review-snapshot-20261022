# Pitfall: a bounded patch whose ANCHOR includes a line the REPLACEMENT does not re-emit silently deletes that line — and the file still GROWS, so size/line shrink guards cannot see it

Measured 2026-09-28 (MF-END-03, app/schemas/characters.py).

## What happened

Inserting a new class after an existing model with a byte-exact replacement:

```python
ANCHOR = CRLF.join([
    "    errors: list[str]",          # <-- last field of PackVersionValidationData
    "",
    "",
    "class CharacterData(BaseModel):",
])
NEW = CRLF.join([
    "", "", "class ReferenceArtworkData(BaseModel):", ...,
    "", "", "class CharacterData(BaseModel):",   # the errors line was NOT re-emitted
])
```

The anchor was chosen to be unique (it included the `errors` line). The
replacement re-emitted the two trailing blank lines and `class CharacterData`
but NOT the `errors: list[str]` line that was part of the anchor. Result:

* `errors: list[str]` was deleted from `PackVersionValidationData`;
* bytes 5,946 -> 7,901 and lines 194 -> 253: the file GREW, so a
  "destructive shrink" guard (bytes/lines must not decrease) reports GREEN;
* the OpenAPI schema for the endpoint silently lost the field, so the
  response body no longer carried `errors`;
* three PROTECTED neighbour tests went red with `KeyError: 'errors'`.

## Detection that worked

The protected neighbour suite run against the same file set on a pristine
`git archive <base>` copy (same 5 files): 90 passed pristine vs 87 passed /
3 failed on the patched tree. That comparison is what localised the defect —
the shrink guard could not.

## Rules

1. When the anchor of a bounded replacement includes ANY line you intend to
   keep, re-emit that line as the FIRST line of the replacement (or shrink the
   anchor to exclude it). Treat anchor and replacement as a diff: every line
   present in the anchor and absent from the replacement is a deletion.
2. After a bounded patch, DIFF the semantic surface, not just the counters:
   for a Pydantic model, assert `set(model_fields) == expected` (or grep the
   field list); for a route file, assert the OpenAPI path/fields; for a module,
   `py_compile` + import. Line counts cannot prove a field still exists.
3. Prove regression-vs-preexisting with a pristine copy, not with memory:
   `git archive <base> | tar -x -C <short-temp-dir>` then run the SAME command
   in both trees and compare counts. `git stash`/`reset` are forbidden on a
   task worktree; `git archive` is read-only and leaves no git state.
4. A run_cmd-style evidence runner that prints its stdout only AFTER the child
   exits will show an empty stdout when the child crashes inside the first
   print — read the log file, not the tail, before concluding "nothing ran".
