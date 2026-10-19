# S09-C3 cycle notes — targeted regeneration, unified freeze, long-path read

Session-specific detail for the C3 correction round (launched 25/08 late
evening). Companion to SKILL.md; C1/C2 arcs live in pm-correction-cycles.md and
s09-c2-full-cycle.md.

## What Codex's C2 review added to the gate vocabulary

The C2 review (S09_C2_PM_REVIEW_2026-08-25.md) confirmed the C2 terminal was
WRONG in kind: `TASK_MANAGER_VERIFIED` written while 2 FOQ were open → corrected
to `BLOCKED_WITH_FINDINGS`. It also introduced findings classes the C2 gates
never looked for:

- **F1-class: acceptance asserted the INVERSE of the requirement.** The E2E
  spec created a job with a non-measured route pin, waited for it to fail,
  replayed the old manifest and asserted ALL loops unchanged — including the
  affected one — then called it "only affected regenerates" pass. The REPORT
  described the zero-regeneration behavior accurately AND still called it a
  pass, deferring new-hash asserts to "later". Lesson: when an acceptance
  criterion says X must change, the evidence must show a before/after delta on
  X itself, not the absence of change plus a promise.
- **F6-class: terminal-evidence hygiene.** Terminal timestamp earlier than
  later append actions, duplicated registry rows, wrong file counts ("13+1"),
  suite counts from memory vs current collect (356 vs 363), cleanup claims
  contradicted by a live dev-server port. Rule absorbed into SKILL.md: every
  count/hash/process claim comes from the LAST command run on the quiescent
  checkpoint, with exact command + exit code logged.
- **Port residue across review boundary**: initial Codex boundary found Next
  :3014 alive despite "ports free" claims. Preflight must netstat the known
  lane ports (3014/3114/8099/8199) and attribute each listener by CommandLine
  before declaring quiescence. A worktree-owned `next start-server` node PID is
  killable by ownership check (`frontend/node_modules` path proves it).

## C3 structural pattern: correction → durable targeted regeneration

The BA contract that closed F1 is reusable for any "apply change to a subset"
feature:

1. Applied correction carries immutable context (id/kind/revision/natural key +
   affected IDs + canonical mutation result) surfaced by ONE public service
   function returning a deterministic context SHA.
2. New durable Job fingerprint = base_job_id + context SHA + frozen evidence
   SHA → replay-same-context returns the SAME job (idempotent generation),
   different context = different generation.
3. Unaffected loops reuse exact artifact rows/files/hashes; affected loops get
   real re-render (z-order effect must actually change compositing order —
   no marker pixels).
4. Route-pin-refused / failed / old-replay jobs explicitly do NOT count as
   regeneration; fail-closed stays but cannot substitute for acceptance.
5. UI must send non-empty affected_loop_ids and poll the durable job; copy says
   "targeted generation", never "full rerun".

## Long-path read (Windows) — write-side fix is not enough

C2 fixed long-path WRITE (atomic publication ≥260 chars) but GET content 404'd:
reader used plain `candidate.is_file()` + plain `FileResponse`. Both existence
check AND serve need Win32 extended paths (`\\?\`). Test recipe that caught it:
completed job with MP4 at absolute path length 272 → `GET /content` → assert
200 + byte-hash match. Gate now requires explicit write + HTTP read/serve at
≥260.

## Unified freeze v4 dispatch packet shape

Manager-provided authority block pasted verbatim into worker prompts:

```
FREEZE AUTHORITY DUY NHẤT (exact path+SHA, KHÔNG scan "newest",
KHÔNG fallback v2/v1, KHÔNG tin manifest ba-file ..., KHÔNG dùng prose token):
- Path: output/s09/20260823_sprint_full/j1-c3/renderer_freeze_manifest_v4.json
- V4_MANIFEST_SHA256 = ae92247b8bfd...
VERIFY TOÀN BỘ path→hash TRƯỚC và SAU từng run; drift → fail-closed dừng ngay.
```

Plus per-row requirements: record j1_manifest_path + SHA in every measured row;
downstream decisions pin the same SHA; rg-gate for the OLD sha after re-pin.

## Wave-A-then-phased-final dispatch (5 owners)

Wave A: T05A (context service) ∥ T03 (generation handler) ∥ T04-PREP
(long-path read + endpoint scaffold against T05A interface, stubbed via DI
until J1) ∥ T05B-PREP (UI wiring, no production E2E yet) ∥ I03-C3 (measured
rerun on v4 immediately — safe because all four other lanes are forbidden from
touching the J1 file set). Joins: J1 = T05A+T03 exit → resume T04 final;
I03 verified → I05 decision-only; J2 = I05+T04+T05B done → T06B production
acceptance (fresh DB/runtime ×2 Chromium, stale-confirm 409 zero-mutation
probe, reload + actual backend restart persistence).

## Verified outcomes + audit recipes (26/08 early morning, Manager hands-on)

- T05A: `applied_regeneration_context()` at s09_correction.py:585 — canonical
  ctx (affected lists sorted+dedup, effect = mutation result,
  `context_sha256` = sha256(canonical JSON minus the sha field)).
  NEW suite `tests/test_s09_t05_backend_c3_context.py` 11 tests ×2 PASS;
  T05 regression domain/api/c1/migration 76 passed. Lesson: locate new
  coverage by grepping tests/ for the function name — it landed in a NEW
  file, not the pre-existing t05 domain/api/c1 files.
- T03: `regen_fingerprint` s09_demo_jobs.py:1021; targeted generation plans
  ONLY affected loops (:186). Real acceptance tests:
  test_regen_one_generation_affected_changes_unaffected_identical,
  test_replay_same_correction_same_job_new_correction_new_generation,
  test_regen_fail_closed_cases,
  test_kill_mid_run_reconcile_replay_no_duplicate. 23 passed ×2.
- I03-C3 per run: 6 MEASURED_RENDERED_OUTPUT (sprite_affine) + 6 adversarial
  CONTRACT_REJECTED_BY_FROZEN_CONTRACT rows — count measured passes AFTER
  excluding control rows or every class double-counts. canonical==adapter
  hash 12/12; all rows pin j1_manifest_path=v4 + exact SHA; post-run drift
  NONE; benchmark suite 33 passed ×2.
- I05-C3: 6/6 PASS_MEASURED_ROUTE, FOQ=0, sample_counts>0 (60–120 frames);
  decision SHA d289929d948ddfa7ae961810c47e43d4e1a37bda8aea21074c5a7df8c13063e9.

### Deep-strip determinism recipe

A/B compare needs a DEEP recursive strip of timing/path fields at ALL dict
depths (`wall_time_ms_total`, `runtime_ms_per_frame_measured`,
`wall_runtime_ms_per_frame`, `artifact_path`, `run_dir`, `j1_manifest_path`,
`adversarial_artifact`). A top-level-key strip left 18 nested diff lines and
produced a false FAIL. Tiebreaker when checks disagree: decoded-hash equality
A==B per fixture/route (True 6/6 while structural noise remained → timing
noise confirmed, content deterministic). Never issue a determinism verdict
while the two checks disagree.

### Provenance location trap in decision docs

I05 stored manifest/run pins under nested keys
(`independent_verification.j1_c3_v4.file_sha256`,
`i03_run_A.content_sha256`) and reference-media status under
`reference_states`. Auditing only top-level `inputs`/`provenance` keys reports
false-missing provenance. Locate by whole-doc token scan for the expected
SHA/path first, then structured-audit where it actually lives. The same scan
doubles as the stale-pin negative assertion: zero hits for EVERY prior-cycle
token (`aa405015` v2, `b8928aec` v3, `t00-i03-c2` paths).

## T04 stall + recovery timeline (26/08 ~04:30, live example of SKILL.md §6)

- T04-PREP exited 1 mid-work (log severed after a diff, no summary) — treated
  as dead-worker; the still-running binding round (R1) superseded it.
- R1 then stalled: log frozen at 393762 bytes from 04:27 (~22 min), leaf
  python CPU crawling +0.05–0.16s per multi-minute window. Router itself was
  healthy (curl /v1/models → 200 fast), so the hang was worker-side streaming.
- Recovery executed exactly per Rules §7: killed ONLY the exact chain PIDs
  (wrapper bash 16992 → hermes 5692 → python 13384 via ParentProcessId walk),
  waited the full 5 minutes, re-dispatched SAME owner session with the SAME
  prompt file (sleep 300 inside the background command so the wait is
  enforced mechanically). Progress survived: the last log lines showed the
  job_type check already extended with JOB_TYPE_S09_DEMO_REGEN — session
  context carried into R2.
- Registry recorded it as "T04-BIND R1 STALL — recovery theo §7" with probe
  numbers, not as a lane failure. ETA pushed honestly (+30–45 min) in the
  same heartbeat rather than defending the old estimate.

## Acceptance-lane findings → owner-routing loop (C3 verified ×3, 26/08)

Production acceptance lanes exist to FIND contract defects — expect 1–2 extra
rounds even after every unit/static gate is green. The loop that closed C3's
last three findings (T06B F1/F2 → T04 fix → rerun → F3 → T06A fix) in one
morning:

1. The acceptance worker hitting a defect OUTSIDE its write-set must report
   `STATUS: BLOCKED_WITH_FINDINGS` with per-finding evidence + a one-line
   "việc cần để mở khóa". That is the DESIRED worker outcome — never push an
   E2E lane to force a pass (that was exactly Codex's C2-F1 complaint).
2. Manager confirms each finding IN CODE before routing: read the exact
   schema/service lines cited (all three C3 findings confirmed at file:line
   within minutes — schemas/s09_demo_compare.py:215, s09_approval.py:370-374).
3. Route each finding to its EXACT owner as a resume carrying root cause
   (file:line) + prescribed fix + forbidden alternative — e.g. "(a) make the
   client pin OPTIONAL, server already pins via decision SHA; do NOT (b) make
   the frontend send it, that violates the body-only-correction_id contract".
   One prescribed option prevents the owner re-litigating the design.
4. Owner lands fix + regression tests; the acceptance lane RE-RUNS THE SAME
   frozen spec — never rewrite the spec to match the bug.
5. Finding an owner NOT named in the prompt: `ls docs/pm/sessions/ | grep -i
   <component>`, then grep that dir for `[0-9]{8}_[0-9]{6}_[a-f0-9]{6}` (used
   to route F3 to T06A when only T05A/T03/T04/T05B/T06B were named).

Contract-drift subclass (F3): when one side of an API contract gains accepted
sources (FE `reasonsOf` matching reasons[] / override_reason /
provenance.reasons / provenance.evidence), grep the OTHER side for the same
source list before declaring the feature done — the backend still matched 2 of
4 sources and approval-overrides failed only in full E2E.

## API contract lessons (C3 F1/F2 fixes, verified)

- When the server already binds evidence by a SHA chain (decision document
  embeds the benchmark content SHA and verifies on-disk bytes server-side), a
  REQUIRED client-side copy of the same pin is redundant friction that bricks
  legitimate callers (UI POST → 422 Field required). Make it
  `str | None = None`: absent = rely on the server pin; present = verify it
  (TOCTOU guard). Fail-closed semantics unchanged either way.
- Idempotent-create endpoints must return `reused=true` (consistent status)
  on identical replay; returning created-semantics with `reused=false` while
  the job_id is identical breaks the replay contract even though dedup
  happened underneath.
- FastAPI double-decorator (`@router.post("/x")` stacked over
  `@router.post("/x/")`) yields TWO OpenAPI paths differing only in trailing
  slash for ONE handler — intentional aliasing, not a duplicate path/method
  defect. Confirm the shared endpoint function before flagging.

## Cycle closure (26/08 morning): rerun-3 PASS + evidence-JSON audit

After each owner fix lands, the acceptance lane re-runs THE SAME frozen spec;
C3 needed exactly three rounds (F1+F2 batched to T04, then F3 to T06A) before
rerun-3 went green: Chromium **1 passed ×2** (17.3s / 19.2s, PW_EXIT=0),
STATUS TASK_SUBMITTED. Realistic expectation: an E2E acceptance lane over a
multi-owner contract surfaces ~3 defects even when every unit/static gate is
green — budget the ETA for it (each round = owner resume + focused tests +
acceptance rerun ≈ 30–60 min).

Manager-side evidence audit on the worker's `evidence-rerun3-run{1,2}.json`
(before/after publication snapshots per loop) — verify the binary requirement
yourself instead of trusting "1 passed":

```
for each loop: changed = (before.artifact_id != after.artifact_id)
               or (before.sha256 != after.sha256)
affected loop(s): changed MUST be True (+ size delta proves real bytes moved)
unaffected loops: changed MUST be False AND sha/size/frame_count identical
```

C3 run1: d4_group_occlusion 79461→79333 bytes (real z-order effect), other
three loops byte-identical. Note the snapshot rows carry no generation/
regenerated fields in this schema — "NEW generation" is proven by the
artifact-id/hash delta plus the distinct regen job id, so don't fail the
audit hunting for a field the producer never writes; assert what the spec
asserts.

Final gate ordering lesson: launch Gate 1 (full suite) as a background job
IMMEDIATELY after the last lane closes, then run static gates (ruff/mypy/
alembic/OpenAPI) inline while it runs — they touch nothing pytest needs and
save 10–15 min off the terminal. New test files from correction lanes (e.g.
`test_s09_t05_backend_c3_context.py`) must be added to the resolved gate file
list — collect `ls tests/test_s09*.py` fresh each round, don't reuse the
previous round's count.

## Final-gate gate 3c: canonical hash recompute — use production functions, not reimplementations

The C3 final gate required an INDEPENDENT canonical-hash recompute for every
measured row (Codex C2-F3). Two failed approaches before the working one:

1. `ffmpeg -i mp4 -f rawvideo -pix_fmt rgb24` + file digest → pixel-order/
   format differs from the decoder pipeline → 0/6 match on perfect artifacts.
2. Hand-rolled mirror of `canonical_frame_sha256` that hashed
   `f.tobytes()` per frame without `np.ascontiguousarray` → also 0/6 FALSE
   mismatches (non-contiguous frames hash different bytes).

Working recipe (6/6 True in one pass):

```python
import hashlib, sys
sys.path.insert(0, ".")
from pathlib import Path
from app.services.renderer_routes.composite import (
    decode_rgb_frames, canonical_frame_sha256,
)
for r in results["results"]:
    if not r.get("decoded_output_hash"):
        continue  # skip adversarial/CONTRACT_REJECTED rows
    frames = decode_rgb_frames(Path(r["artifact_path"]))
    canon = canonical_frame_sha256(frames)  # THE production function
    assert canon == r["decoded_output_hash"] == r["adapter_output_frame_sha256"]
```

"Independent" means independent BYTES (you decode and hash yourself via
public surfaces), not an independent REIMPLEMENTATION of the algorithm —
a mirror that drifts by one contiguity call produces false evidence defects
and wastes a debugging cycle suspecting good artifacts. Assert the THREE-way
equality (recompute == harness stored field == adapter field); if it fails,
the defect is real and lives upstream.

## Final gate cleanup: qa_app_patch residue + ESLint scope (26/08 08:25)

- The final netstat found TWO strays the earlier per-lane checks missed: a
  `next start-server` node on :3014 AND `uvicorn output.s09...t05b.
  qa_app_patch:app --port 8099` — the latter from T05B's PREP phase two rounds
  earlier. Cleanup rule: kill both, but NAME them separately in the registry —
  a qa_app_patch uvicorn is also evidence that a forbidden test-only router
  surface existed in the lane; Codex will want to know whether it touched any
  acceptance evidence. Production-app uvicorn (`app.main:app`) ≠ qa-patch
  uvicorn; they are different findings even on the same port.
- ESLint scope: full-repo `npx eslint src --max-warnings 0` failed on
  pre-existing warnings in unrelated features — the C3 gate is S09-scoped
  (`npx eslint "src/features/demo/**" --max-warnings 0`, exit=0). Record the
  out-of-scope warning count as informational in the registry ("full-src
  eslint còn warnings ngoài scope S09 pre-existing") so the green scoped gate
  is not misread as a clean repo. Also `next lint --max-warnings` errors with
  "unknown option" on current Next — invoke eslint directly.
- Terminal line goes into the registry LAST (after cleanup rows), via heredoc
  append + one dedupe/fixup pass — patching appended lines fails on identical
  strings when the same content was written twice in one run.
