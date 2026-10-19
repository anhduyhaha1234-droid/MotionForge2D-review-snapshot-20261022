# Manager-Loop War Stories — MotionForge S08/S09 sprints (2026-08)

Session-specific evidence and patterns from running PM-gated correction loops
(S09-C1 fast-track, C2 correction round, C2 verdict→C3 setup). Condensed
lessons that back the SKILL.md; keep the SKILL.md as the procedure, this file
as proof/recipes. The full C2-verdict finding-by-finding record (F1 zero-
regeneration E2E, F2 freeze split-brain, F3 non-canonical hash, F4 long-path
GET 404, F5 downgraded cross-lane defects, F6 evidence hygiene) plus the C3
owner/DAG setup now lives in `references/s09-c2-verdict-to-c3.md`.

## Terminal-state protocol failure (C1, F1 finding)

Codex verdict on C1: `CHANGES_REQUESTED`, and the review explicitly stated the
correct boundary state was `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`, not
`TASK_MANAGER_VERIFIED`. Root cause: I03 measured run produced 2
FAIL_OPEN_QUESTIONs (f1_hard_cut, f5_group_occlusion had no route that could
measure them), but the Manager still wrote TASK_MANAGER_VERIFIED.

Rule that now lives in SKILL.md: any FAIL_OPEN_QUESTION / unmeasured required
class / unknown metric ⇒ terminal MUST be BLOCKED_WITH_FINDINGS. Honest
fail-open evidence is good work by the worker — the terminal label is the
Manager's job to get right.

## J1 freeze handshake — hash formula recovery (C1)

Worker claimed contract hash `46c6a41f…` but never recorded HOW it computed it.
Recovery path that worked:

1. `sha256sum` of each file separately did NOT match.
2. Concatenating file contents in different orders did NOT match.
3. Winning formula: **SHA-256 over `path + "\0" + content` for each of the 3
   files concatenated** (`path\x00content` × 3).

```python
import hashlib
h = hashlib.sha256()
for p in files:
    h.update(p.encode()); h.update(b"\x00")
    h.update(open(p, "rb").read())
print(h.hexdigest())  # matched 46c6a41f… exactly
```

Lesson: when a worker reports a multi-file freeze hash without showing the
command, try `path\0content` concatenation first. Better: require workers to
paste the exact hashing command into their REPORT (now in SKILL.md).

C2 upgraded this to a machine-readable manifest:
`output/s09/<run>/j1-c2/renderer_freeze_manifest.json` with path→SHA-256 per
behavior-critical file, verified before AND after every measured run. Drift ⇒
invalidate all downstream runs, resume the owner who drifted, re-freeze,
re-run. Never "fix" drift by editing a stored constant.

## C1 review findings F1–F7 → what C2 prompts had to say

| Finding | Class | C2 fix pattern |
|---|---|---|
| F1 two required classes unmeasured, wrong terminal | protocol | FOQ=0 required; fail-open ⇒ BLOCKED |
| F2 benchmark called private compositor, not production router | architecture | acceptance: instantiate public RendererRouter, call .execute(); ban private helper imports in benchmark |
| F3 freeze invalidated after measured run (lazy re-export edit) | process | recursive manifest incl. __init__.py; verify pre/post run; drift ⇒ full rerun |
| F4 downstream still hard-coded v1 artifact path | hygiene | rg gate for old artifact refs in production/frontend/active tests; archival docs exempt |
| F5 fixed 30fps retime, @identity suffix behavior, pre-encode hashes | correctness | typed rational fps/timebase in contract; identity via typed field not request-id suffix; output_frame_sha256 over canonical decoded frames of encoded output |
| F6 Windows MAX_PATH publication failure (≥260 chars) | platform | explicit long-path test in suite; atomic publish, no orphan .upload, no duplicate artifacts/artifacts path joins |
| F7 E2E lacked only-affected-loop-regenerates proof | test-design | snapshot all artifact IDs+hashes before correction; assert unaffected loops byte-identical after |

## Cross-session mypy trap: PEP 562 lazy re-export

`__getattr__(name) -> object` in a package `__init__.py` breaks static typing
for consumers doing `from pkg import name` (mypy sees `object`, then
`"object" not callable` at the call site — error appears in the CONSUMER file,
not the package). Fix inside the package's own write-set:

```python
if TYPE_CHECKING:
    from app.services.renderer_routes.adaptive_pose_swap import select_route, ...
# runtime __getattr__ stays as-is
```

This was needed twice (introduced during C1, re-fixed in C2 prompt explicitly).
If a sprint touches package `__init__.py` lazy exports, put the TYPE_CHECKING
requirement in the task prompt up front.

## Worker early-exit with good root-cause → resume packet pattern (C2 T06B-PREP)

Worker exited (EXIT=0, REPORT said TASK_SUBMITTED) but dry-runs were failing.
Its log contained a correct root cause: seeder filtered
`Job.job_type == "S09_DEMO_LOOP"` while durable rows store lowercase
`"s09_demo_loop"` → reset deleted nothing → pinned resubmit returned
200/reused instead of 201. Manager response: single resume to the same owner
session with a numbered fix packet (fix filter → re-seed ×2 asserting
`demo_jobs_deleted > 0` → Playwright ×2 → REPORT PREP status), preserving the
worker's own findings list. Do not rediscover what the worker already proved.

## Determinism verification recipe (I05 A/B runs)

Two same-seed benchmark runs are compared after stripping declared
nondeterministic fields (wall_runtime, vram, artifact_path which differs by run
dir). Implementation: deep-compare JSON trees, pop the declared fields first;
expect zero residual diffs. Any other diff = nondeterminism finding. Adversarial
control: re-encoded-source-without-replacement must FAIL every class it applies
to — proves the pipeline detects no-op passes.

## Evidence-path discipline that survived review

- All run outputs under `output/s09/<sprint>/<task>-c<N>/`, never into shared
  fixture trees (rendering into tests/fixtures/**/rendered then copying was an
  explicit C1 finding).
- Every REPORT pins exact commands + basetemp paths + exit codes.
- Manager independently reruns focused suites ×2 with DIFFERENT basetemp dirs.
- MAIN tree checked dirty for production S09 files at every gate (must be 0).

## Version-bump coherence trap (C2 I03-PREP, new)

Worker bumped `SCHEMA_VERSION = 3` in the harness script but left the fixture
`thresholds.json` at version 2 → all 8 subprocess tests failed with
`thresholds schema_version must be 3, got 2`, while its REPORT still said
TASK_SUBMITTED. Two durable lessons:

1. Any prompt that authorizes a schema/policy constant bump must ALSO name every
   data file carrying that version and require them bumped in the same change,
   with threshold VALUES frozen (version field only).
2. "Green STATUS line over a red suite" is this project's most common worker
   misreport. The manager's own focused-suite run before acceptance is the only
   thing that catches it — log-size liveness checks do not.

## Resume-packet hygiene (C2, reinforced)

- Inline `-q "$(printf ...)"` resumes silently no-op on quotes/apostrophes
  (bash EOF error, exit 2, worker gets nothing). Prompt files + `$(cat …)` are
  mandatory; verify launch by grepping the dispatch log for your EXIT tag.
- Early-exit workers WITH a correct root-cause in their logs get a numbered
  fix packet resuming the same owner — never a replacement session, never a
  rediscovery of what the worker already proved.
