# S11-C4-R3 Independent PM/Code Rereview — 2026-09-06

## Verdict

`S11-C4-R3 = CHANGES_REQUESTED / NOT_APPROVED`  
`S11 = NOT_CLOSED`  
`S12/S13 = BLOCKED`

The R2 production lock and rollback mechanism remains materially correct, and
all fresh functional gates run by Codex are green. R3 also removed the old
post-thread repair call and added durable KeyboardInterrupt/SystemExit
coverage. Sprint closure is still blocked by one finite durable-test defect and
one closure-packet defect: the committed race test can claim that caller B was
blocked without proving B reached the production lock, it does not compare the
returned revision map or final four-field registry snapshot with exact expected
values, and the superseding evidence root lacks the required command/session
ledger and a true pre-R3 writable-test baseline.

No production or test bytes were changed by this review.

## Review boundary

- Time: 2026-09-06, Asia/Bangkok.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Branch/HEAD: `codex/s11-integration` at
  `4f2c787124001c9f93043669d95b689935281058`.
- Canonical porcelain is empty and HEAD equals
  `origin/codex/s11-integration`.
- R3 worker commit:
  `d9c439b6fd9ada3a3d1e39d6c3396e4cc02980cf`, integrated by no-ff merge
  `67b4acfe32f16cb3e9cf01fa0928a42cfa2b1c7f`; INT01 docs commit is
  `4f2c787`.
- R3 diff is test/docs only: the C4R1 test plus append-only T03G LOG/REPORT.
  Production bytes are unchanged from R2.
- Superseding Manager packet reviewed:
  `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260906-001500-R3-final`.

## Independent positive evidence

- Fresh C4R1 module on canonical: `6 passed`, exit 0.
- Fresh all-three-module T03G matrix: `152 passed`, 293 warnings,
  180.48 seconds, exit 0.
- Fresh T05A consumers: `14 passed`, 21 warnings, 15.47 seconds, exit 0.
- Fresh dedicated T12 runs on two distinct basetemp roots: `1 passed` plus
  `1 passed`, both exit 0.
- Fresh Ruff `--select F` on the five binding paths, two-file binding mypy,
  `git diff --check 7751598..HEAD`, and Alembic sole-head check all pass.
- Manager-retained T06 12, T01 64, S10 270, S10 API 71 and direct OpenAPI
  274-path/340-operation/zero-duplicate logs are green.
- Read-only Hermes state confirms exact implementation owner
  `20260905_192221_6da09b` used
  `cmc/meta/muse-spark-1.3-contributor` with reasoning max/300 iterations.
  No third implementation session exists on the R2 worktree. The competing
  `20260905_192249_150b51` row remains silent at 39 messages, and current OS
  inspection found no pytest or implementation writer.
- The five untracked competing-owner incident files remain present and
  unstaged on the R2 worktree; no tracked-byte collision was found.

## Findings

### P1 — the durable race test does not prove B reached the production lock

Locations: `tests/test_s11_t03g_qc_check_c4r1.py:346-360`.

R3 starts thread B, sleeps for one second, then defines
`b_blocked_before_release` as B having no result while `tb.is_alive()` is true.
There is no event or instrumented lock-acquire marker showing that B has called
`ensure_full_band_registered()` and attempted `_BOOTSTRAP_LOCK`. The loop at
lines 355-357 is also ineffective for that purpose: its condition is
`while "b" in outcomes`, which is false before B returns.

Codex ran a non-writing negative-control mutation that inserts a two-second
sleep at the beginning of `caller_b`, before its bootstrap call. The current
test still reported `b_blocked_before_release=true`, A failed as expected, B
later succeeded, and every committed assertion passed. Therefore the test can
label scheduler delay as production-lock contention.

Required correction: instrument the lock attempt inside the subprocess. A
test-only wrapper around the real `handler._BOOTSTRAP_LOCK` may signal
`b_lock_attempted` from B's `__enter__` immediately before delegating to the
real lock. Wait for that bounded marker while A is paused inside real explicit
registration, assert B has not returned, then release A. `Thread.is_alive()` or
a fixed sleep alone is not acceptance evidence.

### P1 — “exact ten revisions/four-field snapshot” is asserted only by shape

Locations: `tests/test_s11_t03g_qc_check_c4r1.py:338-342` and `:515-528`.

Caller B stores only `len(revs)`, so the test accepts any ten revision values.
The final assertions compare detector names/order and require non-empty string
types for entry point/version, but never compare the complete
`(name, entry_point, version, description)` rows against an exact expected
snapshot.

Codex ran a second non-writing negative-control mutation that corrupts the
first detector's entry point, version and description after both threads finish
while preserving names/order. The current test function still passed. This
directly disproves the packet's claim that exact revisions and an exact
four-field snapshot are durably asserted.

Required correction: capture or derive the exact clean expected revision map
and exact four-field snapshot before clearing the registry for contention;
return B's complete map and compare it exactly; compare the immediate final
snapshot exactly. No bootstrap/repair may run between the thread joins and the
final snapshot.

### P1 — the R3 closure packet is not the complete packet required by R3

The R3 prompt required `commands.jsonl`, raw session/route evidence, complete
indexing of every pass/fail and a baseline captured before the worker resumed.
Actual disk state shows:

- `commands.jsonl` is absent;
- `manager/route-probe.log` and `manager/session-audit.log` are absent;
- `lanes/r3-resume/` exists but contains zero files;
- the historical `129 failed, 9 passed, 13 errors` run and message 176346 are
  summarized in `NEXT_REVIEW_PACKET.md` but are not copied/indexed as raw
  artifacts under the superseding root;
- `PREFLIGHT_DECISION.md` records that the worker was already executing and
  the writable test was already dirty at 20,741 bytes before the final root's
  baseline. `baseline_manifest.csv` and `postimage_manifest.csv` therefore
  contain the same final test hash `95eb2e5d...`; they do not form a true R3
  test preimage/postimage pair;
- `final-git-quiescence.log` records `QUIES_EXIT:0 (1=clean)`, an internally
  inconsistent marker, although fresh Codex process inspection found no
  active implementation writer.

The gate logs themselves are useful and mostly carry command envelopes, but
the missing ledger and after-the-fact baseline prevent the packet from proving
ordered provenance and exact R3 scope. R4 must supersede this packet rather
than edit or retroactively relabel it.

## Session opening proposal

Status: `PROPOSED_ONLY / R4_TEST_AND_EVIDENCE_CORRECTION`.

- Continue the current exact Manager session
  `20260905_162953_5a5cda`; do not create a new Manager loop.
- Resume exact implementation owner `20260905_192221_6da09b` for the same
  Task ID `S11-T03G-C4-R2-RECOVERY`; never create a third worker.
- Keep competing session `20260905_192249_150b51` and prior owners frozen.
- Exclusive implementation write-set remains the C4R1 test plus append-only
  T03G LOG/REPORT. Production remains frozen.
- Keep exact Muse route, max reasoning and fallback OFF.
- Build one fresh external R4 root before resume, with a true preimage,
  append-only command ledger, raw session audit and truthful supersession map.
- Re-run the corrected node/module/T03G matrix and bounded downstream gates,
  integrate through exact INT01, then stop at Manager-submitted for Codex.

Complete next prompt:
`docs/pm/prompts/S11_C4_R4_DETERMINISTIC_LOCK_EVIDENCE_CLOSURE_MANAGER_2026-09-06.md`.

