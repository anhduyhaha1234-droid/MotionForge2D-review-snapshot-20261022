# Combined-candidate gates, superseded expectations, guard re-baselining, multi-lane 502 recovery

Session-earned patterns (S12-R7 two-manager wave: 5 lanes VAL/RETRY/B01/BRIDGE/QA + integration, 2 Managers).
These are class-level: apply to any multi-lane wave that transports lane commits into one frozen candidate.

## 1. Combined-candidate gate law
Per-lane green ≠ combined green. The final gate on the merged tip WILL catch cross-lane interactions
that no lane can see alone. Real case: B01's own test (`test_B01_F…full_apply_executable`) passed 6× on
its lane, then failed on the combined candidate because BRIDGE's frozen semantics (no boxed geometry →
typed ineligible) invalidated the test's geometry-less fixture expectation.

Diagnosis order (never guess):
1. Read the RAW assert + actual values from the gate log (`grep -B5 -A45 <node>` then extract `E` lines).
2. Classify: **expectation superseded by a frozen contract** vs **real production bug**.
   - Superseded: the assert encodes behavior a sibling lane deliberately changed under an authorized
     freeze (eligibility, renamed nodes, new required fields). The message usually contains the new
     typed reason/code — that is the fix working as intended.
   - Real bug: values disagree with the frozen contract itself → stop, file exact repro + zero-mutation
     counts; do not patch around it in tests.
3. Fix routing by WRITE-SET membership:
   - File inside the failing owner's write-set → dispatch that owner a BOUNDED correction
     (fixture/assert only; forbid production edits; re-run full module on the combined worktree).
   - File outside every write-set → file an exact finding (file path, failing node, asserted vs actual,
     why superseded, proposed bounded exception + proposed owner) and route to the deciding authority.
     NEVER a silent edit, never weaken assertions.

## 2. Guard re-baselining after transport (false-alarm class)
Pre-wave `guard-protected-pre.json` / `guard-allow-pre.json` manifests are captured at the OLD wave base.
Once the same worktree is `merge --ff-only`-synced to the combined tip (so the owner codes against the
combined code), guards will report the OTHER lanes' legitimate transported changes as
`protected_file_changed`. That is expected, not drift.

Correct proof per correction round:
- `git diff --name-only <parent>..<new_commit>` == EXACTLY the allowed paths (e.g. test + docs only).
- SHA-attribution: protected diffs' post-hashes equal the hashes recorded in the other lanes' reports
  (e.g. `61916B71…` == BRIDGE's reported `s09_approval.py` hash) → attributable 100%.
Then re-capture manifests at the new base (`guard-*-crNbase.json`) for any future rounds, and record the
re-baseline rationale in evidence.

## 3. Superseded-expectation family (recurring across reviews)
An authorized semantic change makes historical tests red. Known sub-classes and handlers:
- Stale target revision pinned in a migration test → split `TARGET_REV` vs `CURRENT_HEAD` constants,
  assert both edges; never blind-replace the constant (bounded exception, test file in write-set).
- Fixture relied on a bug that got fixed (points-only executable, geometry-less segments) → flip to the
  frozen semantics + add a positive control with the new required input (boxed geometry).
- Static inventory references pre-rename nodes (after an authorized rename) → programmatic diff of
  inventory names vs delivered names, rename rows only; provenance assertions stay byte-intact.
Rule: keep an explicit FINDING doc per instance (file, node, asserted vs actual, class, proposal, owner)
and list them in the packet under "test compatibility corrections" with which are authorized vs pending.

## 4. Multi-lane 502 flapping recovery (upstream-only failure)
Signature: several lanes die within the same minute with `API call failed after 3 retries … [502] fetch
connect timeout`, while `GET /models` on the local gateway returns 200 in ~0.1s → local gateway fine,
upstream completions flapping (burns every ~15–20 min during a bad spell).
Recovery cycle (repeat indefinitely; never a terminal state):
1. Verify byte-safety of every dead lane FIRST (worktree status: uncommitted edits intact, commits clean).
2. Probe: a real inference (`hermes chat -q "Reply exactly: X_OK" …`). A 240s timeout = still down —
   wait and probe again; do NOT resume lanes against a dead upstream (they just die again).
3. Wait until ≥5 min past the last death. Embed `sleep 30` at the start of each resume command so the
   mark passes even on fast dispatch.
4. Resume the SAME session/route/scope with a continuation nudge: state pointers (what is already done,
   what is uncommitted), "verify state, continue from stop point, DO NOT redo completed parts", same
   model/provider, fallback OFF.
5. Log one INCIDENT doc with per-lane state-at-death + recovery actions; do not re-file per retry.

## 5. Two-manager split mechanics (authority-bridge waves)
- Two Manager chats, disjoint lane ownership; record the split in BOTH registries; B never touches A's
  worktrees/owners and vice versa.
- A publishes `EXPORT_HANDOFF.json` in its evidence root (lane_commits with exact SHAs, diffstats,
  per-lane guard results, no-active-writer evidence, limits/non-claims). B's INT activation gate =
  handoff file exists + all B lanes terminal/verified.
- A produces NO Git integration; the sole INT worker transports in the frozen order, one merge per lane
  (`--no-ff`, message `Merge commit '<sha>' into <branch>`), verifying per-lane allowlist + owner
  porcelain BEFORE each merge; conflict → abort to exact owner, zero manual fixes.
- SHA typos happen (a 41-hex literal): resolve by branch tip + parent + diffstat match, record the
  correction explicitly; never trust a literal over the repository.

## 6. Env-dependent gate tests
Tests that read env (e.g. candidate-root/expected-SHA provenance checks) fail inside the broad gate when
the env is not exported. Run them in a SEPARATE documented invocation with exact env values at the
CURRENT tip (+ verification of root/branch/clean first). The packet must show both runs (broad without
env + dedicated run with env), not hide the split. If the dedicated run still fails, read the raw assert:
inventory/name-sync issues are their own finding class (see §3), not env problems.

## 7. Provenance-pin re-freeze recipe (drift that is AUTHORIZED)
When a pinned hash (`IN_REPO_IMMUTABLE`, guard manifest entry, doc digest) fails AFTER an authorized
change touched that exact file — the pin did its job; the drift is authorized, so re-freeze it:
1. Enumerate ALL pins programmatically; diff vs actual files. `unexplained_drift` MUST be `[]` — any
   drift NOT attributable to an authorized commit → STOP + report (that is real drift).
2. Git-prove attribution per failing pin: `git show <authored_commit>^:<path> | sha256` == the OLD pin
   value, AND `<authored_commit>` touches that path (`--name-only`). Both must hold.
3. Update ONLY the proven pins; keep every other assertion byte-intact. Record preimage/postimage
   digests + the authoring commit in LOG/evidence.
4. Negative control: re-run with a WRONG expected SHA → must fail-closed (proves provenance not weakened).
5. Commit message names the finding/exception lineage (e.g. "re-freeze provenance pins for authorized
   R5-sync changes (finding R7-B2 addendum)"); then transport as its own INT round + re-gate.
Pitfall: fixing the SOURCE file is not enough — the pin lives in a DIFFERENT file's test constants; both
sides (doc + constants) must sync or the test compares Counter(actual)==Counter(expected) and fails.

## 8. Reviewer-probe re-run harness (hash-identical, frozen copy)
Re-running immutable reviewer probes against a new tip (independent evidence for the packet):
1. `git archive <tip> -o tip.tar` + extract to a frozen copy dir; run probes with cwd=probe dir and
   PYTHONPATH pointing INTO the frozen copy — never run probes inside a lane worktree.
2. Copies must be hash-verified; cross-match their sha256 against lane handoffs and the reviewer's own
   runs (a probe sha identical across your copy / reviewer / lane handoff is near-irrefutable provenance).
3. PYTHONPATH = frozen root + `frozen/tests` + EVERY directory of modules the probes import by BARE
   name (`import test_s09_structural_lock_producer as base`, `test_r4_retry_execution`, …). One missing
   dir → `ModuleNotFoundError` at collection; enumerate imports first (`grep -n "^import\|^from" probe.py`).
4. Probes often require a review-output env var (e.g. `S12_REVIEW_OUT`) and write artifacts with mode
   `'x'` → FRESH output dir per probe per run, else re-runs crash with FileExistsError.
5. Old-world captured fixtures may now hit NEW gates by design (e.g. pre-timeline authority →
   `LEGACY_AUTHORITY_REAPPROVAL_REQUIRED`). NOT a regression: record an explicit interface-change
   mapping to the lane nodes that re-verify the same semantic intent; do NOT "fix" the probe to bypass
   the new gate, and do NOT count it as a pass.
6. Report per file: sha, exit, counts; label by-design failures distinctly from real failures.

## 9. Long-prompt dispatch pitfall (worker re-dispatch)
Packet-scale prompts passed via `hermes chat -q "$(cat file)"` inside a larger quoted command hit the
parser hard-block (nested `$(...)` inside quotes → "command parser limit or malformed executable
payload"). For any prompt this large: dispatch through a launcher file, or keep the `-q` argument as the
ONLY substitution in the command. Same class: inline `$(grep -c …)` inside `powershell … "…"` — split
into separate commands or write a script file.
