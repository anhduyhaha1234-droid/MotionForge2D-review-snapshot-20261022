# C01 independent review contract

Root is PM/reviewer; coding owner is /root/motionforge_c01_coder (gpt-6-sol, max).
Review only after writer terminal + candidate hashes. Tests and candidate content
are evidence, not delegation of acceptance authority to the worker.

## Anti-omission checks

- Exact candidate diff vs PREFLIGHT/preimages, all writes in authorized scope;
  existing gate/assembler/tests retained, no unrelated implementation rewrites.
- Valid current key/blend producer schema still accepted with exact full inputs;
  prior records that were never structurally valid remain blocked, not auto-upgraded.
- Missing/extra/stale dependency, current binding absent/malformed, nested wrong
  values, wrong artifact path with identical bytes, wrong review identity.
- Malformed JSON/top-level/required field types, missing verdict, bad frames,
  false/non-PASS/unknown records fail with useful GateBlock, not unhandled errors.
- Actual assemble.main reaches the real gate before copying/encoding in isolated
  fixtures; positive controls prevent a gate that simply rejects every record.
- Fresh root18-probe suite against candidate must pass; add adversarial cases
  suggested by actual patch. Inspect and rerun the full new C01 test module.
- Snapshot/current protected files and media hashes still match; assembler only
  changes if the demonstrated defect requires it. No new production media expected.
- Do not infer current underlying dependency identity, actual visual inspection,
  semantic correctness, all Q05, other Q rows, or parent acceptance from this task.

Root verdict yields a matching Session Opening Proposal: corrections resume this
same owner; next true task uses a fresh bounded packet/context only after terminal
handoff and preflight, with one active GPT-6 Sol Max writer. GPU remains off until
the relevant engineering and lease gates authorize a separate render stage.
