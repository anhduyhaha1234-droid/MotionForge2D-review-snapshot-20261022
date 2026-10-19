# S01-T03 - PM Review

**Decision:** APPROVED  
**Reviewed:** 2026-08-03  
**Reviewer:** PM/Codex

## Required corrections

1. `restore()` currently accepts a manifest anywhere under the managed root. The contract requires validation of Trash containment, so both the manifest and its trashed file must resolve strictly under the configured Trash root, not merely under managed root.
2. Add regression tests where a syntactically valid manifest and payload are inside managed root but outside `.trash`; restore must reject them. Also cover a manifest under `.trash` whose payload resolves outside the same Trash entry.
3. Ensure validation itself does not create the Trash directory as a side effect when it does not exist. Keep existing recovery/overwrite behavior unchanged.
4. Re-run targeted tests, Ruff, mypy, full seven-gate baseline and diff check; append LOG, update REPORT and resubmit.

## Final review

Correction completed in the same session after switching Hermes to MAX reasoning. Restore now requires manifest and payload containment strictly beneath the configured Trash root without creating Trash during validation. PM independently reran 46 targeted tests, Ruff and mypy; all passed. Resubmission evidence records quality run `20260803-171812` with 7/7 gates PASS. S01-T03 is approved and releases S01-T04.
