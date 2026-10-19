---
name: bom-verified-implementation
description: Implement changes and prove the result works.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: coding
    tags: [implementation, testing, verification]
---

# bom-verified-implementation

## When to Use

- Creating or modifying code in an existing repository.
- The user expects a working result, not a code suggestion.
- The result can be tested, built, rendered, or inspected.

## Required Inputs

- Approved goal or clear request.
- Repository instructions and baseline.
- Acceptance criteria.
- Available test and build commands.

## Procedure

1. Inspect the relevant code path and reproduce current behavior when possible.
2. Choose the smallest coherent change that satisfies the acceptance criteria.
3. Implement one logical unit at a time while preserving existing conventions.
4. Run targeted tests after each material unit.
5. Run typecheck, lint, build, or broader regression checks defined by the project.
6. Inspect the produced artifact directly: run the app, open the file, query the endpoint, or render the UI.
7. Summarize changed files, verification evidence, limitations, and any unresolved blocker.

## Decision Rules

- Do not claim completion from a zero exit code alone when output can be inspected.
- Do not suppress tests, errors, or warnings merely to make checks pass.
- Avoid unrelated refactors unless required to complete the task safely.
- Reuse existing libraries and project patterns before adding dependencies.

## Pitfalls

- Editing before reproducing the problem.
- Running only one narrow test after cross-cutting changes.
- Leaving debug code, temporary files, or secrets.
- Reporting success without opening or executing the output.

## Verification

- Requested behavior is demonstrated.
- Relevant automated checks pass or failures are explicitly documented.
- The final artifact exists and can be used.
- Unrelated files were not changed without justification.

## Output Format

- Completed change.
- Files changed.
- Commands and tests run.
- Observed result.
- Remaining risks.
