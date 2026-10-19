# S10-C4A T04A-C4-R3 — long-path consumer-read fix (finding-02)

Verified 2026-08-30. T04C-C3 R6 exposed a P0 production defect AFTER the
finding-01 lineage-hash fix was in: the structural-compare gate could not
read >260-char artifacts. Same class as the T01C-C6 root-containment fix but
on the READ side — keep both variants in mind when a deep-root test fails.

## Symptom

Run1 on a C4A-mandated deep runtime root (nested `segment-00..08` dirs,
artifact absolute path 267–293 chars) rendered 24/24 verified chunks with
real correction applied, but `POST /full-apply/{run}/structural-compare {}`
returned:

```
200 {status: BLOCKED, failures:[RENDERED_FILE_MISSING]}
```

`REVIEW_REQUIRED` was unreachable pre- AND post-correction — binary rule
(REVIEW only from real measured evidence) unsatisfiable.

## Root cause

`app/api/routes/s10_full_apply.py` structural_compare_gate built the
artifact path PLAIN:

```python
abs_path = _Path(managed_root) / str(art.relative_path)   # :1010
if not abs_path.is_file():                                  # :1011
    return _blocked("RENDERED_FILE_MISSING", ...)
```

while every producer write uses extended-length `_lp()` (`\\?\` prefix):

- `app/workflow/s10_full_apply_jobs.py` — `_lp` def :107, forced root
  normalization :516, write paths 181/215/321/423/441/739/745/787/814/943/945
- `app/services/s10_recompute.py:927` — `managed_root = _lp(Path(managed_root), force=True)`

On Windows (`LongPathsEnabled=0`), `Path.is_file()` on the plain form returns
False for >260 paths even though the file exists; the `\\?\` form returns
True. The gate file even DEFINES the helper `_win_long_path()` at :69-74
(mirror of s09_demo_jobs) and uses it correctly in the validate-managed-
artifact branch (:107 `_hash_file(Path(_win_long_path(abs_p)))`) — the gate
branch just forgot it. Finding-01 (content-hash lineage) had already PASSED
in the same repro: derived `sha256("pub:{run}:{art_sha}") == DB content_hash`
— the defect was strictly the file-read branch after it.

## Fix (bounded, T04A write-set only)

```python
abs_path = _Path(_win_long_path(_Path(managed_root) / str(art.relative_path)))
```

One wrap at :1010 makes EVERY subsequent file op (is_file :1011, hash :1022,
stat :1032, decode :1070, timebase probe :1076) see the extended form.
Fail-closed branches unchanged. Do NOT touch the producer `_lp()` contract.

## Regression tests — deep-root emulation trap

Verification trap discovered while writing the tests: `Path.mkdir(
parents=True)` with a `\\?\` prefix fails `WinError 123` at >=24 level
nesting, while direct write/hash/decode on the extended path works fine.
So the tests must NOT build the deep tree via mkdir chains — they must:

1. helper `_lp_p()` — pad the relative path so `len(abs) > 259` without
   hard-coding an absolute integration path (seed deep dir segments);
2. write + hash-tag the artifact THROUGH the extended form (emulate the
   producer `_lp` form), using repository helpers with a `rel_override`;
3. assert green → REVIEW_REQUIRED, missing file → RENDERED_FILE_MISSING,
   tampered bytes → RENDERED_TAMPERED (all on >260 abs path).

New tests: `test_c4_deep_root_publication_green`,
`test_c4_deep_root_missing_file_blocks`, `test_c4_deep_root_tampered_file_blocks`.

## Verification (Manager-independent after worker exit)

- T04A focused 63/63 ×2 fresh roots (37.4s/37.9s) — 54 prior + 9 deep-root
- Retained regressions 117 passed (T01C 32 + T03 18 + T02 46 + T01A 47;
  Manager re-ran all and wrote `pytest_retained_manager.log` because the
  worker bundle omitted the T01C/T02/T01A logs — see
  SELF-DISCLOSED MISSING EVIDENCE LOGS in SKILL.md)
- Ruff `--select F` 17-file set: All checks passed
- mypy 9-file literal: `Success: no issues found in 9 source files`
- J1-v4 13/13 + EOL PASS; alembic single head a10b11c12d3e; diff-check 0;
  `git status --porcelain` 45 = S10 write-set only; staging orphans 0

## Class rule

When a >260 path test fails, probe WHICH SIDE lacks the prefix on the SAME
artifact:

```python
plain = Path(managed_root) / rel
ext   = Path(_win_long_path(plain))
print(plain.is_file(), ext.is_file())   # (False, True) => consumer-read gap
```

- producer write wiring gap → T01C owner (write paths not via `_lp`)
- consumer read branch gap → T04A owner (gate built plain path)
- root containment gap → handler root normalization (renderer_contract:542
  containment failed: root and children must share the same prefix form)