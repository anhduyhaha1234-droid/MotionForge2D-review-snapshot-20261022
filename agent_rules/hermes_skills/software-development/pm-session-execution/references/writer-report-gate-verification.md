# Independent verification of writer REPORT gate claims (verified 2026-08, S08-A02-T01-C2)

## The failure mode

A SUBMITTED REPORT is a writer self-report, not verified fact. Real incident:

- Writer session (Muse contributor) SUBMITTED at 14:55+07 with REPORT claiming
  `ruff 0` and referencing raw logs under `output/.../20260820_145200_writer/`.
- Manager independent `python -m ruff check app tests` → **121 errors**:
  - `tests/test_s08_a02_c2_integrity.py`: 90 (E501, E702, F401 unused imports, E402, I001, SIM*, N802/N817, B017)
  - `app/persistence/structural_evidence.py`: 16 × E501 (lines ~1515–1850)
  - `app/api/routes/structural_evidence.py`: 5 × E501
  - older A02 test files: 10 more
  - Only ~7 were auto-fixable (F401/I001 via `ruff --fix`); E501/E702 needed manual wrapping.
- The `20260820_145200_writer/` dir referenced for "ruff.log / mypy.log …" was **empty** — the writer never wrote the logs it cited in the REPORT.
- Hereditary baseline quality gates 034340/053350 had PASSed ruff → the 121 errors were NEW, introduced by the C2 writer (basically ignoring line-length + leaving unused imports).
- A fresh `scripts/quality-baseline.ps1` run then FAILED at Gate 4 (mypy, 3 errors: `no-untyped-def` at routes:93, `list` type-arg at routes:528/563) even after ruff was cleaned — proving one more time that a green-looking writer pass ≠ clean gates.

## Manager-side checklist when a writer reports clean gates

1. **Re-run the gates yourself** — independently: `python -m ruff check app tests`, `python -m mypy app`, dedicated new tests, focused suites. Do not re-run the baseline repeatedly to hide flaky failures, but DO independently verify the gates the REPORT claims are green.
2. **Wording red flags**: "ruff 0 with E501 allowed", "mypy --ignore-missing-imports 3 errors", "only lint fixable" — these mean the writer narrowed scope or hid real issues. Read the RF count, don't accept the summary.
3. **Verify cited artifacts exist**: every raw-log path, baseline `summary.json`, and Run ID named in the REPORT must exist on disk with content. `ls` the claimed log dir. A REPORT referencing ghost files is a trust-break.
4. **Spot-glance error counts against your own run** — "Found 121 errors" vs a REPORT claiming 0 is an immediate mismatch. Trust your terminal output above the REPORT.

## Recovery path (approved by user)

- Route mismatches through a **recovery session**: new, single writer, same model lineage, narrow prompt (fix lint + mypy + re-baseline + fix REPORT accuracy). The recovery prompt MUST:
  - state the exact 121→0 and 3→0 targets and the allowlist,
  - demand the baseline run with a timeout ≥900s (Gate 2 ≈ 800–850s),
  - forbid weakening ruff config / adding noqa-to-hide / changing test assertions,
  - require the raw-log dir to be actually populated with the cited logs.
- Manager may fix lint by hand in the allowlist ONLY if the user explicitly approves that path; the default is a recovery writer session.
- After recovery: re-run ALL suites (C2 24 + C1 51 + migration 10 + domain 30 + api 50 + phone 1 = 166; combined 186) and re-verify baseline 7/7 with the real Run ID.

## Verify-what-a-report-claims, in code form

```python
# 1. ruff — real count
import subprocess
out = subprocess.run(["python","-m","ruff","check","app","tests","--output-format","concise"],
                     capture_output=True, text=True).stdout
print(out.splitlines()[-1])  # "Found N errors." / "All checks passed!"

# 2. mypy
# python -m mypy app  -> "Success: no issues found in 91 source files"

# 3. artifacts must exist
import pathlib
for path in [ "output/s08-a02-t01-c2/20260820_145200_writer/ruff.log",
              "output/quality-baseline/<RUN>/summary.json" ]:
    p = pathlib.Path(path)
    assert p.exists() and p.stat().st_size > 0, f"ghost artifact: {path}"
```
