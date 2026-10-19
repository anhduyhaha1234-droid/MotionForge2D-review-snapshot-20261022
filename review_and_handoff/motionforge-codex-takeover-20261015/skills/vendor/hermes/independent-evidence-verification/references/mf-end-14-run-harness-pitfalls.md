# MF-END-14 run-harness pitfalls (measured 2026-09-28)

Context: a GPU evidence run reused the DELIVERED pytest file's `validate_graph`/`save_node_ids`
inside the run harness (single source of truth for validation).

## 1. The pinned runtime venv has no pytest — importing the delivered test module aborts the run

Measured: `sa_run.py` (run under the ComfyUI venv python) died with
`ModuleNotFoundError: No module named 'pytest'` BEFORE any job; server came up and shut down
cleanly, but the harness lost the whole attempt (no jobs). The venv is read-only/pinned — do NOT
`pip install` into it.

Fix pattern: import the module from a python that HAS pytest (e.g. the system python that runs
the test suite), or stub the symbols the module touches at import time:

```python
try:
    import pytest  # noqa: F401
except ModuleNotFoundError:
    import types
    stub = types.ModuleType("pytest")
    class _Mark:
        @staticmethod
        def parametrize(*a, **k):
            return lambda fn: fn
    stub.mark = _Mark()
    stub.skip = lambda *a, **k: None
    sys.modules["pytest"] = stub
```

Corollary: keep attempt-1 records (`run_record_attempt1_failed.json`) so the abort is disclosed.

## 2. `SaveImage.filename_prefix` basename == the output filename — comparison tables must use it

Measured: the harness wrote prefixes `mf_shot_anchor_v1/tensor_preview/key_comp` (from
`nid.lower()`) but its inline comparison looked for `key_composited_00001_.png`; all 7 rows read
"missing" and a GREEN run exited RC=1. The actual files were `key_comp_00001_.png` etc.

Rules:
* derive the expected filename from the prefix basename: `<prefix.split("/")[-1]>_00001_.png`;
* prefer recomputing the comparison from the RECEIPT-FROZEN output files instead of rerunning the
  GPU job: verify each file's sha256 == the receipt's recorded sha256 FIRST, then compare pixels
  (record that provenance explicitly in the run record);
* when a harness's headline exit code is 1 but the receipts are all green, read the per-row detail
  before rerunning anything — the bug may be in the comparison table, not the job.

## 3. `rc=$?` after `cmd | tail` reports tail's rc — use `set -o pipefail` for evidence capture

Measured: `python -m pytest ... | tail -2; echo rc=$?` printed `rc=0` for the pipeline tail; the
canonical broad-wave capture was rerun once with `set -o pipefail` so `rc=0` is pytest's own.
Cheap to get right the first time; a wrong rc sentinel poisons the whole evidence file.
