# S12-C2 W1→W4 wave execution — INT01 transport template + verify-then-chain loop (2026-09-09)

Canonical lineage this run: `ea78497` (C1 packet) → T01 `9d5cff7` merged `0bbb3b3`
→ W2 (T02 `08dc55d` docs-only + T03A `f25de2b`/`0740464` + T04A `6757b0f`) merged
`66299ed1` → W3 T03B `3340e64` merged `da7108b` → W4 T03C dispatched (base `da7108b`).

## INT01 wave-transport resume prompt (used 3× consecutively, ~5–10 min each, zero conflicts)

Same shape every wave — copy-paste with per-wave SHAs:

```
S12-C2 INT01 W<N>->W<N+1> transport (Git-only, exact INT01). RULES_LOADED rules
(277 lines) truoc tien. Model ocg/deepseek-v4-flash provider custom fallback OFF.
(1) Verify canonical codex/s12-integration HEAD <prev-sha> clean local==remote.
(2) Manager-verified <W commits: list owner + SHA + gate counts> tren branch
    codex/s12/s12-<t>-0907a — merge tung cai non-force --no-ff vao canonical,
    conflict thi abort + bao.
(3) Push origin non-force; verify ls-remote == local.
(4) Prep W<N+1> base: merge canonical moi vao branch codex/s12/s12-<next>-0907a
    (WT ..., tip <old-tip>) chi base delta, conflict abort.
(5) Bao HEAD moi, ls-remote, trang thai branch <next>.
Chi Git transport.
```

INT01 replies with per-merge `--no-ff` parent chains, `ls-remote == local`,
ff-only base delta for the next branch (`<old> → <new> — SẠCH`), and a ledger
validation line (fail row kept as pre-merge ancestry evidence = exit 1 expected).
Always verify afterwards yourself: `git rev-parse --short HEAD`, `git status`,
`git ls-remote origin codex/s12-integration | cut -c1-40` in the canonical
worktree + `git rev-parse --short HEAD` in the prepped task worktree.

## Manager verify-then-chain loop (3 waves green this run)

Per worker ping: (1) `git rev-parse --short HEAD` + porcelain in the task
worktree; (2) `git show --stat --oneline HEAD` — allowlist check (files belong
to the task; a docs-only commit for a verify-only pass is legitimate and has
zero production diff); (3) re-run the task's suite INDEPENDENTLY with explicit
short basetemp under the real Windows Temp + `ruff check --select F` +
`git diff --check`; (4) only then order INT01 merge; (5) dispatch the next wave
in the same turn the INT01 ping returns. Do NOT pre-verify before the worker
ping — verify the committed state, not the reported one.

## Worker first turn is often ANALYSIS-ONLY — plan for a second "IMPLEMENT" turn

A fresh prompt resume on a long contract frequently ends after preflight +
reading (log tail shows reasoning text, `session_id:` line, zero tool writes,
tip unchanged). Observed twice this run (T01 502-cut analysis turn; T03C W4
first turn = preflight + it read the WRONG review file). Do not count this as
worker failure; dispatch again with a tight IMPLEMENT turn:

- Fix path confusion by embedding the ABSOLUTE review/contract paths in the
  follow-up prompt: the T03C worker read the Luna demo review first
  ("This is the WRONG review file — that's the Luna demo review") because the
  generic instruction let it wander. State verbatim:
  `C:/Users/Admin/Documents/Codex/2026-09-05/files-pasted-by-the-user-codex/outputs/s12-c1-review-20260909/REVIEW.md (F01–F11, N lines)`.
- Order: `repro <named counterexample> truoc, roi fix <Fxx list> + rows
  <Cxx list>, commit LOCAL allowlist + TASK_SUBMITTED + SHA. KHONG push/merge.`
- The IMPLEMENT turn then runs to completion in one go (T01 commit `9d5cff7`
  38 passed; T04A `6757b0f` 64 passed; T03B `3340e64` 32 passed).

## Cross-wave contract consumption (why wave prompts must name upstreams)

After W1, every later wave works against NEW contracts from earlier waves:
T01-C2 authority (`docs/contracts/s12-export.md` §8, 18 reason codes,
server-owned response fields), T03A real-DB CAS + fencing, T04A
source-locked `SourceReference`/`AudioReference`, T03B byte-identity chunks.
Wave prompts MUST list which upstream contracts to consume read-only and
which FORBIDDEN files belong to whom — workers otherwise reimplement or
miss the new interface (T04A consumed T01 authority fields; T03C consumes
T04A source_locked + T03A CAS + T03B private-candidate).

## Collection-conflict rename as a real fix (F11), not a gate workaround

T03A-C2 included `git mv tests/s12/s12-t03a/test_c1_closure.py
tests/s12/s12-t03a/test_s12_export_c1_closure.py` (100% rename, zero content
change) so full-tree collection stops colliding on duplicate basenames.
Unique test-file names per package are now the standing convention for new
correction waves — prefer renaming at the SOURCE lane instead of per-dir
gate loops downstream.
