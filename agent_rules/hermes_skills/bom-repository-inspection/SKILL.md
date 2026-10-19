---
name: bom-repository-inspection
description: Inspect an existing repository before changing it.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: coding
    tags: [repository, inspection, coding]
---

# bom-repository-inspection

## When to Use

- Starting work in an unfamiliar or existing codebase.
- The task may affect several files, build tools, or runtime behavior.
- A reliable baseline is needed before implementation.

## Required Inputs

- Repository root or active workspace.
- Requested outcome and explicit constraints.
- Available project instructions, tests, and build commands.

## Procedure

1. Read repository-level instructions first: README, AGENTS.md, CONTRIBUTING, package manifests, and CI files.
2. Map the top-level structure and identify the runtime, package manager, entry points, test framework, and build command.
3. Search for the feature, symbol, route, UI component, or error mentioned by the user.
4. Inspect only the most relevant files first; widen scope only when evidence requires it.
5. Run the smallest safe baseline check that demonstrates the current state.
6. Produce a concise repository map, affected-file hypothesis, risks, and next action.

## Decision Rules

- Do not modify files during inspection unless the user explicitly requested immediate execution.
- Prefer project-defined commands over invented commands.
- Do not read entire large files when search, line ranges, or targeted reads are sufficient.
- Treat generated files, vendor folders, build output, and lockfiles as low-priority unless directly relevant.

## Pitfalls

- Jumping into code before reading project instructions.
- Recursively dumping the whole repository into context.
- Assuming a package manager or framework from filenames alone.
- Calling the baseline healthy without running a relevant check.

## Verification

- The runtime and package manager are identified from evidence.
- Relevant instructions and tests are located.
- The proposed affected files are supported by search results.
- No unnecessary repository-wide output was loaded.

## Output Format

- Repository summary.
- Relevant files and commands.
- Current baseline.
- Risks and next recommended step.
