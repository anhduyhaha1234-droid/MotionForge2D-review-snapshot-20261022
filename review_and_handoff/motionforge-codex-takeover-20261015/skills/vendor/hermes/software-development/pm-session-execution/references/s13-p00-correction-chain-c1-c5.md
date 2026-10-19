# S13-P00 readiness correction chain C1→C5 (2026-08-23, verified)

Session trail for a long documentation-only correction series on ONE owner
session (`20260823_033031_3a5082`) over a 9-file synthesis package under
`output/s13-p00-readiness/20260823-0045-r1/`. Complements
`references/manager-role.md` §correction-round-series with this chain's
specifics. All rounds: resume SAME owner, route custom/alpha/max/no-fallback,
write allowlist = exactly the 9 existing synthesis files, lanes A/B/C read-only.

## Round ledger (verdict → findings → outcome)
| Round | Findings | Outcome |
|---|---|---|
| C0 (lanes A/B/C + synthesis D) | original readiness audit | TASK_MANAGER_VERIFIED |
| C1 | migration dir naming, task granularity→19 IDs, qa_stub purge, DB dual guard, zero-network | fixed; verified PASS |
| C2 | V15 ownership T04B→T04C exclusive; D4-4 OPEN→F-9 DEFERRED_COMPATIBILITY_CLEANUP; live-probe wording purge (D4-9 SUPERSEDED) | fixed; PASS |
| C3 | D4-7→F-10 freeze (golden set 12+10+8=30); DAG W9/W11 gates (T08A no roster at W9; N≥3 blind-human mandatory at T08B); X6 stale D4-3 ref→F-9; R7 PM-permission purge | fixed; PASS |
| C4 | add T01D+T03C (backend HTTP surfaces) → 22 active tasks; T04A real persistence+migration `f13a04a20268`; state mapping FROZEN F-11 (no persisted FAILED; retryable derived from Job taxonomy; UI "Thất bại — có thể thử lại" = view-model of REJECTED&&retryable); split T08C provider-evidence aggregation behind B13-PROVIDER-MEASURED-EVIDENCE; unconditional T08A write-set; DAG rebase W1..W11 | fixed; PASS |
| C5 | T04A dep DIRECTLY on T01B (mandatory candidate FK, no fail-open, live-head preflight); F-10 narrowed / all signing authority consolidated under F-12 (Codex-only C13-GOLDEN-TRUTH-SIGNOFF); T08A=W10, T08B=post-W11 gated window; T08B write-set single namespace results/**; P00-C1 accepted→S13-P00 APPROVED by Codex; risk dup →R15 unique | fixed; PASS |

## Frozen-decision ledger pattern that survived 5 rounds
Numbered decisions accumulate monotonically (F-9 compat cleanup → F-10 golden
freeze → F-11 state mapping → F-12 non-self-signable gates). Each round's prompt
carries a DO-NOT-REGRESS block listing every prior frozen fact as invariant, and
the manager's final gate greps BOTH new findings AND every prior one. When a new
round NARROWS an older decision (F-10 narrowed by C5-F2), the operative row keeps
its ID, gains "NARROWED per Cx-Fy", and the superseded phrasing is marked
SUPERSEDED/NON-OPERATIVE inline — never deleted from append-only REPORT/LOG.
Distinguish compliant residue from violations when grepping: prohibition notes
("NEVER hard-code <rev>", "NOT alembic/versions/**") and deletion-history lines
in LOG.md are compliant; the same strings in operative rows are not.

## Verification gates for synthesis-package corrections (all doc-only, no tests)
1. Per-round hash baseline `Cx_hash_baseline.txt` BEFORE dispatch; after exit
   `sha256sum -c` FAILED set must equal exactly the intended edit set.
2. Count gates: `grep -c '^## S13-T'` = active task count (19→22 evolution);
   NEW-SESSION RULE mentions ≥ task count; risk IDs `| RN |` each count=1.
3. Stale-language sweep with classification: operative grep must be ZERO for
   retired authority ("PM-reviewed/signed", "P00-C1 accepted", "if granted by
   PM", "(+ own e2e/spec artifacts)"), while history-section hits are labeled OK.
4. Cross-file consistency of decision IDs (`grep -c 'F-10'` per deliverable).
5. Terminal vocabulary: READINESS_REPORT/REPORT say PENDING_CODEX_REVIEW /
   NOT APPROVED NOT GO; REPORT tail = `STATUS: TASK_SUBMITTED`.

## C5 operational anomalies (both resolved without data loss)
1. **Two backend-restart worker deaths** (20:03, ~20:40): Hermes desktop/backend
   bounced mid-round both times, killing CLI workers AND wiping the manager's
   background-process registry (poll → not_found). Recovery each time: wait ≥5',
   resume SAME owner/route, multi-attempt markers EXIT/EXIT_R2/EXIT_R3 in ONE
   appended dispatch log. Partial writes across attempts are continuous — verify
   coverage of ALL findings at final gate only. See
   `references/manager-liveness-and-worker-process-audit.md`.
2. **External snapshot commit mid-chain** (`ee10e55` 20:46:52, 508 files): landed
   between attempt deaths, absorbed the 283-path dirty tree (porcelain→4),
   contained ZERO run-dir paths, dispatch logs contain zero git commands →
   attributed foreign-owned (user/Codex-side), recorded, NOT reverted; hash gates
   re-run under the new HEAD. Attribution recipe: commit timestamp vs attempt
   death/start times + commit-stat path grep + dispatch-log git-command grep.