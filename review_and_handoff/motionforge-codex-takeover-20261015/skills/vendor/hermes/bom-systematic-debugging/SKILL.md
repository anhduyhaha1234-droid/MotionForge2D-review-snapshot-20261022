---
name: bom-systematic-debugging
description: Diagnose failures before applying a minimal fix.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: coding
    tags: [debugging, root-cause, errors]
---

# bom-systematic-debugging

## When to Use

- A reproducible error, failing test, crash, or incorrect behavior exists.
- Previous fixes failed or the cause is unclear.
- The user needs a root-cause fix rather than a workaround.

## Required Inputs

- Exact error, screenshot, log, or failing command.
- Expected behavior.
- Environment and recent changes when available.

## Procedure

1. Reproduce the failure using the smallest reliable case.
2. Capture the exact command, input, environment, and complete relevant error.
3. Classify the failure as input, configuration, environment, dependency, logic, state, or external service.
4. Form one evidence-backed hypothesis at a time.
5. Run a discriminating check that can confirm or reject the hypothesis.
6. Apply the smallest root-cause correction.
7. Re-run the original reproduction, then targeted and regression checks.

## Decision Rules

- Do not repeat an unchanged failing command more than twice without new evidence.
- Do not delete data, caches, lockfiles, or dependencies as a first response.
- Separate environment failures from implementation failures.
- Preserve the original error evidence until the fix is verified.

## Pitfalls

- Shotgun changes across many files.
- Treating correlation as root cause.
- Hiding errors with broad exception handling.
- Stopping after the symptom disappears once.

## Verification

- The original failure is reproducibly gone.
- The explanation accounts for the observed error.
- Relevant regression checks pass.
- The fix does not rely on an unexplained manual step.

## Output Format

- Reproduction.
- Root cause.
- Fix applied.
- Verification evidence.
- Prevention recommendation.
