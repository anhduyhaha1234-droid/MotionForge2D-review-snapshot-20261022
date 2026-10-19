# S11-C4-R4 Independent PM/Code Rereview — 2026-09-06

## Verdict

`S11-C4-R4 = CHANGES_REQUESTED / NOT_APPROVED`  
`S11 = NOT_CLOSED`  
`S12/S13 = BLOCKED`

The production mechanism and the durable R4 test are now materially complete.
R4 closes both R3 test findings: the contention test proves caller B reached
the delegated acquisition boundary of the original production lock, and it
compares B's full revision map plus the immediate ordered four-field registry
snapshot with exact clean expected values. Fresh Codex gates and two mutations
of the actual committed test are green.

Formal sprint closure is blocked by one evidence-provenance defect only. The
R4 packet's `commands.jsonl` does not contain truthful live execution times,
and the raw gate files do not contain the missing command envelopes. This was
an explicit P1 acceptance row after R3's missing ledger, so it cannot be waived
or retroactively reconstructed. R5 is evidence-only: no worker resume, source
change, integration or push is required.

No production or test bytes were changed by this review.

## Review boundary

- Time: 2026-09-06, Asia/Bangkok.
- Canonical worktree:
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`.
- Branch/HEAD: `codex/s11-integration` at
  `1f5936d1167a55a583e8849ca67032e61297fe85`.
- Canonical porcelain is empty and HEAD equals
  `origin/codex/s11-integration`.
- R4 worker commit:
  `7c58c37e786f4b3fdf6b4a37800829bd0359bfda`, integrated by no-ff merge
  `7e474d44a5da8b59cd19b0a09a7f63fdfdbcd60b`; INT01 docs commit is
  `1f5936d`.
- R4 diff is test/docs only: `tests/test_s11_t03g_qc_check_c4r1.py` plus
  append-only T03G LOG/REPORT. Production remains frozen.
- R4 packet reviewed:
  `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260906-210700-R4-final`.
- Fresh process inspection found no implementation writer or pytest process
  after the review gates.

## Closed R3 implementation/test findings

### Lock-boundary proof is durable

Locations: `tests/test_s11_t03g_qc_check_c4r1.py:299-414` and `:534-565`.

- A clean bootstrap captures the exact expected revision dictionary and exact
  ordered `(name, entry_point, version, description)` snapshot before the race.
- `LockProbe` delegates to the original real `_BOOTSTRAP_LOCK`; for B's exact
  thread identity it signals `b_lock_attempted` immediately before delegated
  acquisition.
- A is paused inside real `contact_break.register` while the production lock is
  held. The test waits for B's boundary marker, verifies B has not returned and
  remains live while A is live, and only then releases A.
- `finally` releases the event and restores both the lock and registration
  patch. All joins are bounded.
- B returns its complete revision dictionary. The outer test compares it
  exactly, then compares the immediate final four-field snapshot and detector
  order exactly, with no repair bootstrap between joins and observation.
- A's exact `RunQcChecksError / QC_RUN_BOOTSTRAP_CONFLICT` and `RuntimeError`
  cause checks remain present. KeyboardInterrupt/SystemExit rows also remain.

Codex mutated the actual in-memory test payload in two independent runs. A
mutation delaying B before the lock marker was rejected, and a mutation
corrupting snapshot fields while preserving names/order was rejected. Both
negative controls exited 0 only after confirming the committed test failed the
mutant as intended.

## Independent positive evidence

- Fresh C4R1 module: `6 passed`, exit 0.
- Fresh all-three-module T03G matrix: `152 passed`, 293 warnings,
  178.86 seconds, exit 0.
- Fresh T05A consumers: `14 passed`, 21 warnings, 15.39 seconds, exit 0.
- Fresh dedicated T12 on two distinct basetemp roots: `1 passed` and
  `1 passed`, both exit 0.
- Fresh Ruff `--select F` on the test and four binding production paths:
  clean.
- Fresh two-file binding mypy: success with no issues.
- Fresh `git diff --check`: clean.
- Manager raw output logs report T06 `12 passed`, post-merge T03G
  `152 passed`, Alembic sole head `f9a0b1c2d3e4`, and OpenAPI 274 paths / 340
  operations / zero duplicate IDs / nine QC operations.
- Protected production hashes in the R4 manifests are unchanged, and the true
  R3→R4 test pre/post hashes differ as expected.
- Route/session artifacts identify exact Manager `20260905_162953_5a5cda`,
  exact resumed owner `20260905_192221_6da09b`, Muse 1.3 contributor/max and no
  third implementation owner. The competing owner remained unchanged.

## Remaining finding

### P1 — `commands.jsonl` is reconstructed, not a truthful live ledger

Location:
`C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260906-210700-R4-final\commands.jsonl`.

Rows 5 through 21 all record the identical start and end timestamp
`2026-09-06T14:33:30+00:00`. This includes, among other sequential actions, a
T03G run reported as 172.63 seconds, T05A at 14.63 seconds, T06 at 385.62
seconds, integration, a second 172.85-second T03G run, Alembic, OpenAPI and
negative controls. Those commands cannot all have zero duration at the same
instant.

Filesystem times independently confirm the contradiction: raw gate artifacts
span 14:33:47 through 15:10:15 UTC, while `commands.jsonl` was last written at
15:10:33 UTC. Most raw gate files contain output plus an exit marker only and
do not independently preserve exact command, CWD, start/end time, HEAD and
isolated roots. Therefore they cannot repair the false ledger fields.

The guard evidence also contains an unreported failed attempt:
`guard_preresume.json` says Python could not open
`s11-c4-r2/docs/pm/tools/write_set_guard.py`, while
`manager/g11-guard-postpatch.log` contains only `GUARD_EXIT:0`, not the raw
verification or hash comparison. The separate manifests are useful and show
no product drift, but the packet overclaims this as a successfully captured
raw guard row.

R4 explicitly required real append-only records with exact start/end times and
raw envelopes, instructed that failed attempts be indexed, and prohibited
reconstructing commands as if they ran in R4. Because that row was the bounded
remedy for R3's evidence failure, formal closure is not supportable from this
packet.

## Session opening proposal

Status: `PROPOSED_ONLY / R5_LIVE_LEDGER_EVIDENCE_ONLY`.

- Continue exact Manager `20260905_162953_5a5cda`; create no Manager and no
  worker session.
- Do not resume implementation owner or INT01. Make no source, test, PM-session,
  migration, UI, config, Git, commit, merge or push change.
- Create one fresh external R5 evidence root before the first gate.
- Use a wrapper stored and hashed in that root to append a START event before
  each command and an END/final ledger row in `finally`, preserving exact
  command, CWD, timestamps, duration, HEAD, environment roots, exit and raw
  stdout/stderr path.
- Re-run the finite closure ladder on the already-integrated canonical commit,
  capture truthful before/after protected hashes and all failed attempts, then
  stop at Manager-submitted for one final Codex review.

Complete next prompt:
`docs/pm/prompts/S11_C4_R5_LIVE_LEDGER_EVIDENCE_ONLY_MANAGER_2026-09-06.md`.
