# S11-C4-R1 Independent PM/Code Rereview — 2026-09-05

## Verdict

`S11-C4-R1 = CHANGES_REQUESTED / NOT_APPROVED`  
`S11 = NOT_CLOSED`  
`S12/S13 = BLOCKED`

R1 closes the original ghost-registration case and adds a real clean-process
subprocess test, but the bootstrap transaction is still not failure-atomic for
ordinary Python exceptions and is not serialized across concurrent callers.
The exact recovery owner also violated the binding patch-only guard by writing
tracked source/test files through `Path.write_text()` heredoc scripts. The R1
packet remains incomplete and overclaims one static gate. No production or test
bytes were changed by this review.

## Review boundary and authority

Review boundary: 2026-09-05 19:11 +07. Canonical worktree
`C:\Users\Admin\MotionForge2D-worktrees\s11-integration`, branch
`codex/s11-integration`, HEAD
`e98ccd93066db4a2bd5a925306c7ed75bc5bfe09`, porcelain empty and local equal to
`origin/codex/s11-integration`. Owner commit
`8c42a323a28d64efa11a0f29a41b679ed8ae5529` is an ancestor of canonical HEAD.

The current user instruction explicitly authorizes
`cmc/meta/muse-spark-1.3-contributor`. Read-only Hermes state reconciles the
Manager as `20260905_162953_5a5cda`, the exact recovery owner as
`20260905_043139_01a91f`, and the successful alias probe as
`20260905_163747_de1a1f`; all three session rows name the authorized alias.
Therefore the old exact-route finding is closed by the newer user instruction,
not by rewriting historical evidence. No project writer, pytest, ffmpeg or
ffprobe process was active at the review boundary.

Authority hashes read in this turn include:

| Authority | SHA-256 | Lines |
|---|---|---:|
| `docs/pm/HERMES_AUTOPILOT_RULES.md` | `c9b068b2195461b1f867a5ec95714cea3ab09881757f5607094574d15dda428f` | 277 |
| `AGENTS.md` | `9208e0dea247b32f54ae24ed9fda8b85de79fcd0b4b3f54a2ae8b7d81218c4e6` | 7 |
| `frontend/AGENTS.md` | `e3447d84251880fb34cfae09131cb4c57471529bbfe60976a3245793cf621627` | 5 |
| `docs/pm/SESSION_PROTOCOL.md` | `e100656c8b2a8959c595234dfe51ebb832fbb5f8763f2243ad0423a62955eda6` | 188 |
| prior C4 verdict | `eb90db049ef2ddb6956681ef2af71487329a67e7a373d0bc1027f4dbe02986a2` | 191 |
| binding R1 prompt | `6ab546dd3808b651cd33a130c56087daa8920b99519680126b2abec10e9caefe` | 150 |

## Positive independent evidence

- Fresh three-module T03G run: `148 passed`, 293 warnings, 175.62 seconds,
  exit 0.
- Fresh T05A consumers: `14 passed`, exit 0.
- Fresh targeted T12 on two separate basetemp roots: `1 passed` + `1 passed`,
  both exit 0.
- New durable clean-process test starts with an empty registry, imports ordinary
  app code, constructs the real `JobService`, and observes the exact ordered
  ten-detector band.
- Ruff `--select F` on the six C4/R1 paths passes. Two-file binding mypy
  (`qc_checks_handler.py` + `qc_check_runs.py`, `--follow-imports=skip`) passes.
  `git diff --check` passes.
- Alembic has one head `f9a0b1c2d3e4`; direct OpenAPI has 274 paths, 340
  operations and zero duplicate operation IDs.
- Manager-retained T06, T01 and S10 outputs are green, but a broad suite cannot
  waive the red mechanism rows below.

## Findings

### P1 — rollback excludes ordinary exceptions and concurrent callers corrupt state

Locations: `app/workflow/qc_checks_handler.py:251-482`, specifically import
handling at `:307-327` and explicit registration at `:431-456`; the mutable
singleton has no transaction primitive at
`app/services/qc_checks/registry.py:52-128`.

Contract: every import/explicit-registration/conflict failure must restore the
complete pre-call registry snapshot, and concurrent `JobService` constructors
must not let one caller's stale rollback overwrite another caller's success.

Mechanism: the function catches only `QcRegistryError`; a detector import or
`register()` raising `RuntimeError` bypasses `_restore`. The snapshot/mutation/
verification sequence also has no lock around the whole transaction. Individual
dict operations and the Python import lock do not serialize this multi-step
registry transaction.

Fresh isolated reproductions on `e98ccd9`:

- Simulated import side effect followed by `RuntimeError`: exception escapes;
  pre-state `[]`, post-state contains `import_side_effect`; `import_restored =
  False`.
- Simulated explicit registration side effect followed by `RuntimeError`:
  exception escapes; the ten-entry pre-state becomes nine binding entries plus
  `explicit_side_effect`; `explicit_restored = False`.
- Deterministic two-thread reproduction: caller A reports success, caller B
  raises `RunQcChecksError`, both join, but B restores its stale nine-entry
  snapshot after A succeeds. Final registry has 9 entries and is missing
  `contact_break`.

Test structure confirms the omission: `tests/test_s11_t03g_qc_check_c4r1.py:53-129`
covers only ghost, entry conflict, version conflict and clean idempotence. It
does not inject import failure, explicit-registration failure or concurrent
constructors, despite all three being binding R1 rows.

Impact: a startup/import defect or concurrent service construction can leave a
process-global registry poisoned after a reported success/failure; later full QC
may fail or run against incomplete authority. Required correction: one
process-wide critical section for the complete bootstrap transaction, rollback
on arbitrary exceptions, stable error wrapping, and durable adversarial tests
for both exception paths and a two-live-thread failure/success race with bounded
joins and exact final-registry assertions.

### P1 — recovery owner violated the byte-safe patch-only contract

Read-only Hermes state records tracked-file direct writes by recovery session
`20260905_043139_01a91f`: message/tool-call IDs `174611`, `174613`, `174621` and
`174940` run heredoc Python using `Path.read_text()`, `str.replace()` and
`Path.write_text()` on `app/workflow/qc_checks_handler.py`; ID `174973` does the
same to `tests/test_s11_t03g_qc_check_job.py`. The worker also created and ran
`r1_patch2.py` as a direct-write applier. This directly contradicts rules §8.2
and the R1 prompt, which prohibit heredoc/script direct-write for existing
source/test files and require bounded patch tools with preimages.

The canonical files are currently recoverable and did not shrink, so this is
not a new P0 authority-loss incident. It is nevertheless a repeated safety
violation in the already-recovered S11-T03G lineage. Per the context-health
rule, the current recovery owner must be frozen from further writes and the
next correction requires an evidence-backed owner transfer with zero concurrent
writer. Resuming this session again is not authorized.

### P1 — R1 closure packet is incomplete and overclaims static status

Evidence root:
`C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-093200-R1-routegate`.

- Missing required `REGISTRY.md`, `NEXT_REVIEW_PACKET.md`, post-worker guard
  result, quiescence log, final Git/local-remote log, and individual ruff/mypy/
  diff-check command logs.
- `baseline_manifest.csv` covers only five files and omits absolute path,
  tracked/dirty attribution, protected set and required byte snapshots.
- `manager-verify-t03g.log` contains a retained failed run (`2 passed, 146
  errors`, exit 1), while `C4_R1_EXIT_VERDICT.md` reports only the later green
  rerun and does not disclose the failed orchestration attempt.
- The EXIT says “mypy 3 files — Success”. A fresh exact run over the three
  named production files exits 1 at `job_service.py:542` and `:727` with two
  `no-any-return` errors. The historically accepted two-file binding scope is
  green, but that does not make the three-file claim true.
- Most gate files retain only pytest/tool output, not the required exact command,
  start/end timestamps, duration, exit and resource-root tuple. The Manager's
  self-dispatched `CODEX_R1_REVIEW_RAW.log` is incomplete and produced no
  `CODEX_R1_VERDICT.md`; it is not an independent approval.

Impact: the packet cannot prove guard compliance, run ordering, or the exact
claimed static boundary. Required correction: create a new immutable run-root,
retain every red and green attempt, run the project guard correctly, and index
all rows with truthful arithmetic and exact raw commands.

## Session Opening Proposal

Status: `PROPOSED_ONLY / BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`.
Do not dispatch from this review alone.

- Open one new compact Manager only after explicit user authorization.
- Freeze recovery writer `20260905_043139_01a91f`; never resume frozen old
  owner `20260903_170546_0d42f6`. After proving both have zero active writer,
  create exactly one new S11-T03G recovery owner from immutable canonical
  `e98ccd9` in a fresh clean worktree/branch.
- Maximum implementation wave: 1. Exclusive write-set:
  `app/workflow/qc_checks_handler.py`,
  `tests/test_s11_t03g_qc_check_c4r1.py`, and append-only T03G session docs.
  Manager-only evidence follows writer terminal; INT01 remains Git-only.
- New Manager/recovery worker route: custom 9Router through provider `muse`,
  `cmc/meta/muse-spark-1.3-contributor`, reasoning `max`, fallback OFF. Existing
  INT01 retains its already-bound session route unless the user explicitly
  overrides that exact session.
- S12/S13 remain blocked until R2 is independently approved.

The complete proposed next Hermes prompt is saved at
`docs/pm/prompts/S11_C4_R2_BOOTSTRAP_TRANSACTION_OWNER_TRANSFER_MANAGER_2026-09-05.md`.

