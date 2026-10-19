---
name: worktree-integration-audit
description: "Use when auditing worktrees before sprint integration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [git, worktrees, integration, audit, readiness, read-only]
    related_skills: [background-worker-orchestration, ai-code-review-resilience, terminal-engineering-discipline]
---

# Worktree Integration Audit

Use when a project runs parallel sprints in separate git worktrees and the next
sprint (or a merge) needs an **integration base**: identify what each approved
tree changed vs the common base, where trees collide, what accidental copies
exist in MAIN, and propose — WITHOUT executing — the integration options.
Proven on MotionForge2D (2026-08): pre-S08 audit of S05 + S06 worktrees.

## Hard rules (read-only phase)

- NO writes: no product code, no PM docs, no commit/merge/push/rebase/
  cherry-pick/reset/checkout/restore/clean/stash/delete/file copy.
- Do NOT create worktrees/branches, do NOT stop QA servers, do NOT run a
  coding worker. Independent read-only audits are allowed.
- Do NOT read or hash user databases; only use PM-provided protected
  stat/hash (e.g. `channels.json` SHA) for comparison.
- Do NOT "clean up" accidental copies in MAIN — flag them for the authority.

## Audit steps (each is a real command, capture output)

1. **Per-tree status table** (MAIN + every worktree): root, branch, HEAD,
   full `git status --short`, then counts:
   ```bash
   git status --short | awk '{print $1}' | sort | uniq -c   # staged/unstaged/untracked shapes
   git status --short | wc -l                                # total dirty entries
   ```
   Expect ALL trees dirty (uncommitted sprint work) — a clean tree is the
   exception; note trees whose HEAD differs from the common base.

2. **Process table** — list writers/watchers/servers so nobody claims an idle
   machine:
   ```powershell
   Get-CimInstance Win32_Process | Where-Object {$_.Name -match "hermes|python|node|bash"} |
     Where-Object {$_.CommandLine -match "chat|watch-s0|uvicorn|run dev|quality-baseline"} |
     Select ProcessId,Name,@{N="Cmd";E={$_.CommandLine.Substring(0,[Math]::Min(110,$_.CommandLine.Length))}}
   ```
   Count Hermes writers (`CommandLine -match "chat"`) — must be 0 for audit.

3. **Delta vs common base** per tree (exclude evidence dirs; keep code/docs):
   ```bash
   git status --short | awk '{print $2}' | grep -v "^output/" | grep -v "^docs/pm/sessions/" | sort > /tmp/tree-files.txt
   comm -12 /tmp/s05.txt /tmp/s06.txt   # files BOTH trees changed → potential conflict
   comm -23 /tmp/s05.txt /tmp/s06.txt   # only in tree A
   comm -13 /tmp/s05.txt /tmp/s06.txt   # only in tree B
   ```

4. **Conflict severity** per overlapping file — count hunks, don't guess:
   ```bash
   diff treeA/app/x.py treeB/app/x.py | grep -E "^[0-9]" | head   # hunk ranges = real conflict
   ```
   Classify: 🔴 many hunks in product code = real merge; 🟡 status-line docs =
   trivial; ⚪ test artifacts (`.last-run.json`) = do not merge.

5. **MAIN incident comparison** — when a past agent wrote into MAIN by
   mistake, compare MAIN copies vs the final review tree:
   ```bash
   diff -q MAIN/path worktree/path   # GIONG / KHAC / only-in-MAIN / only-in-tree
   ```
   Report which MAIN copies match the approved tree, which are stale, which
   exist only in MAIN (quarantined test files). Never delete them yourself.

6. **Quality evidence verification** — do not trust status text alone:
   ```bash
   python -c "import json; d=json.load(open('.../quality-baseline/<RUN>/summary.json')); print(d.get('overall'))"
   grep -E "Decision|Run ID" docs/pm/sessions/<task>/PM_REVIEW.md
   stat -c "%y" REPORT.md   # submission older than its baseline run + review time
   ```
   Flag inconsistencies (e.g. ROADMAP still says SUBMITTED while PM_REVIEW
   says APPROVED; MAIN ROADMAP rows still PLANNED).

7. **Protocol conflict detection** — when user workflow differs from the
   written protocol, quote the EXACT lines/sections needing change (e.g.
   "task kế tiếp chỉ được dùng output đã APPROVED" vs manager-gated
   SUBMITTED → MANAGER_VERIFIED_PENDING_SPRINT_REVIEW → SPRINT_SUBMITTED).
   Never edit the protocol yourself; list it as a blocker for Codex/user.

## Integrated-base options (propose, do not execute)

For each option state: exact source tree/commit, files to copy, merge
conflicts (by file), git/file operations required, risks from dirty state
(untracked vs `AM`/`MM` index states), and the mandatory post-integration
validation (fresh 7/7 baseline + full pytest + tsc/eslint + Playwright smoke
on the integrated root). Prefer the tree with the most recent Codex review as
the base; copy per-file with `diff -q` per file — never whole-directory copy.

## Report contract

Deliver in chat as a named report (`PRE_<SPRINT>_INTEGRATION_READINESS_REPORT`)
containing: tree/branch/HEAD/status table; process table; authoritative-source
table (tree + baseline run + PM_REVIEW decision); overlapping/conflict table;
MAIN incident comparison; integrated-base options; protocol changes required;
dependency chain confirmation; blockers needing authority; recommendation.
Stop after the report — no code, no file writes, no new session/worktree.

## References

- `references/pre-s08-audit-example.md` — worked example from the first real
  audit (MotionForge2D S05/S06): tree snapshot shapes, delta/overlap outcome,
  MAIN-incident comparison table, baseline checks, report section titles.

## Pitfalls

- `git status --short` path column can contain spaces (e.g.
  `frontend/src/app/(app)/...`) — awk `$2` splits on the status code only when
  the status is a single char + space; verify counts before trusting them.
- A tree may share HEAD with MAIN but carry ALL its work uncommitted — HEAD
  alone never proves content; always combine HEAD + status.
- `summary.json` shape differs per run — print `d.get('overall')` and check
  `gates` list; do not assume key names.
- Deleting residue processes (old watchers, npm dev wrappers) is a WRITE —
  flag for the authority instead, per the read-only rule.
- **Post-transport guard "FAILED" is a false-alarm class**: pre-wave protected/allow
  manifests hold the OLD base hashes, so once sibling lanes' commits land (worktree
  ff-synced to the combined tip), every transported file reports
  `protected_file_changed`. Do NOT treat this as drift. Prove per-round correctness by
  `git diff --name-only <parent>..<new_commit>` == exactly the allowed paths, plus
  SHA-attribution of each protected diff to the other lanes' own reports, then
  re-capture manifests at the new base for future rounds. Full pattern:
  `pm-worker-orchestration` → `references/combined-candidate-gates-and-superseded-expectations.md` (§1–§9:
  combined-candidate interaction failures, superseded-expectation findings, fix routing
  by write-set membership).
- **Prove transported content by BLOB id — never by comparing worktree bytes across worktrees.**
  Measured 2026-09-24 (S12 transport): a cross-check of the integration tree against each source
  worktree reported **3 files "DIFFER"** while `git rev-parse <rev>:<path>` matched **4/4**. Cause:
  `core.autocrlf=true` with no `eol=lf` pin — the same blob checked out as **68,616 B LF-only** in one
  worktree and **70,237 B with 1,621 CRLF pairs** in the other. Rules: for content proof use
  `git rev-parse <rev>:<path>` (blob id) or `git diff <revA> <revB> -- <path>`; treat a worktree-byte
  mismatch as *unproven*, not as a difference; and state which of the two you measured. A blanket
  "N differ" on a check whose purpose is "nothing changed" is a bug signal (same family as a
  `194/194 corrupted` manifest verdict).
- **A tree HEAD that moved is not automatically drift — prove whether the advance was authorized.**
  An integration owner that merges verified ranges legitimately moves *another* lane's tree (here the
  QA tree was fast-forwarded to the frozen candidate on the Manager's instruction), and a naive
  baseline comparison reads that as `protected_tree_drift`. When you accept an advance, record the
  proof instead of weakening the guard: the new HEAD **contains that lane's own range tip as an
  ancestor** (`git merge-base --is-ancestor <lane-tip> HEAD` ⇒ true), the tree is `porcelain=0`, and
  no path outside the transported ranges changed since the lane's own commit
  (`git diff --name-only <lane-tip>..HEAD` ⊆ transported paths). Also scope the comparison to the
  paths a lane ACTUALLY touched: filtering by a parent directory two lanes share reports the other
  lane's added files as differences (measured: 5 phantom paths from `tests/product_p1` shared with a
  sibling lane).
- **A lane that measures a product-level blocker must have it encoded as an ASSERTED control, never
  patched into a pass.** Measured 2026-09-24: a QA lane found that an export-readiness gate is
  unreachable through public APIs (readiness demands a completed full-scope run that the fixture's own
  data can never produce), corroborated three independent ways (sibling test node, an e2e seeding
  script that hand-seeds the missing state, the server's own check-state payload). Correct handling —
  which the Manager should enforce before accepting the row: the gate accepts **exactly** the measured
  reason/field signature (`reasons == ['<THE_ONE_REASON>']` AND `failed == ['<the-one-check>']`), any
  other ineligibility still fails the node, and the finding is routed to the owning branch as a
  product gap. Never let a lane (or yourself) seed the missing state, loosen the gate, or relabel the
  refusal as success — that converts a real blocker into a fake green.
