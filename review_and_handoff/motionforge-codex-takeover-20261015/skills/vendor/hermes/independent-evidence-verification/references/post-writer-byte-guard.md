# Post-writer byte guard — verify a lane's write-set and scope before you read its gates

Companion to the "machine-check your own packet" rule. Run this **after the lane's writer is terminal**
(commit landed / process exited) and **before** you read or trust its gate output. Recipe proven
2026-09-27 across 4 lanes (each lane: guard `0 problems` + an independent Manager re-run of the decisive
test file).

## 0. Preflight manifest — capture BEFORE dispatch

Per allowlisted + protected file, record: absolute path, tracked/dirty attribution (`git ls-files`,
`git status --porcelain -- <path>`), sha256, bytes, logical line count. For critical **untracked** files
(ones with no git recovery path — e.g. new tools written in a previous round) copy the bytes into the
evidence root and assert `sha256(snapshot) == sha256(source)` immediately. Snapshot the append-only
ledger's rows + its prefix digest at the same time.

## 1. Post-writer checks (all must hold; emit JSON, `problems: []` is the PASS condition)

| # | Check | Detail |
|---|---|---|
| 1 | write-set files still exist | a missing non-NEW file is an immediate stop (`BLOCKED_TEST_AUTHORITY` territory) |
| 2 | **growth-only** | for pre-existing files: `delta_bytes >= 0` and `delta_lines >= 0`; a shrink is a destructive-shrink stop. New files are `NEW`, not a delta |
| 3 | READONLY/PROTECTED files unchanged | recompute sha256 vs preflight; e.g. the QC detector `silhouette_clipping.py` must stay byte-identical (`5298643…`) when the packet made it read-only |
| 4 | NEW files now exist | and are untracked-at-preflight (a NEW path that was already tracked means the packet's assumption was wrong) |
| 5 | **porcelain ⊆ allowlist ∪ pre-existing-untracked** | see trap below — without the pre-existing set the guard fabricates violations |
| 6 | frozen-name coverage | regex `def <row-prefix>_\w+` over the new test file; the count must equal the matrix's frozen row count (8/10/13 measured this round) |
| 7 | commit scope | `git show --stat HEAD` touches only allowlisted paths; `git rev-parse <commit>^` equals the recorded preimage commit; `git branch -r --contains HEAD` is EMPTY when push was forbidden |

## 2. Then re-run the decisive check yourself

Independently execute the lane's frozen test file (cheap: 1–2 s for the micro file) and compare to the
lane's claimed counts. `23 passed` / `10 passed` / `13 passed` measured by the Manager matched the lanes'
reports — that is what makes "verified" honest rather than quoted.

## 3. Traps (measured)

- **Pre-existing untracked files are not violations.** A lane tree that already carried 7 untracked tools
  + 1 untracked dir before the round will make a naive `porcelain ⊆ allowlist` check report 8 false
  `OUTSIDE ALLOWLIST` hits. Freeze the pre-existing untracked set in the preflight manifest and subtract it.
- **Never strip the whole `git status --porcelain` stdout** — leading spaces are significant; strip per line
  after slicing `line[3:]`.
- **A dirty tree after a lane "committed" can be legitimate**: 7 untouched round-I1 files plus the lane's own
  3 committed files. Distinguish by comparing against the preflight set, not by assuming clean.
- **The guard must be re-runnable and deterministic**: exclude its own output by name, and re-run it after
  any late write; a guard whose result changes without inputs changing is a bug.
- Do not "fix" a guard failure by editing the lane's artifact — the guard reports; the lane's owner (or a
  new authorized delta) repairs. Disclose cosmetic mismatches in the report instead.

## 4. Reporting shape that survived review

Per lane: `guard_<LANE>.json` in the manager evidence dir with `files[{rel, role, bytes, delta_bytes,
delta_lines, sha256}], porcelain[], frozen_names{count, expected}, problems[]`, plus the Manager's own
re-run command + count. Reference the file in REPORT/MATRIX so a reviewer can re-derive every number.
