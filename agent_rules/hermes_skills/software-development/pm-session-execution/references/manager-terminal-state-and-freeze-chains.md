# Manager-mode addendum: terminal-state honesty & freeze chains (S09-C1→C2, verified 2026-08-25)

Lessons from the S09 C1 correction round (manager wrote TASK_MANAGER_VERIFIED with 2 open
FAIL_OPEN_QUESTIONs; Codex overruled to CHANGES_REQUESTED and re-stated the correct terminal
as BLOCKED_WITH_FINDINGS) and the S09-C2 round that fixed the class of failures.

## 1. Terminal-state honesty

- A required acceptance class ending FAIL / unknown / FAIL_OPEN_QUESTION forces
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW` — no matter how honest or well-documented
  the measured evidence is. Honest evidence ≠ the prompt's binary blocker rule satisfied.
- Before writing ANY terminal state, re-read the prompt's own blocker list item-by-item and
  check each one against disk reality. The reviewer reads the prompt literally; so must the
  manager.
- "The worker was honest about the gap" is a virtue of the worker, not a waiver for the
  manager's verdict.

## 2. Freeze/join handshakes are CHAINS, not point-in-time hashes

- Pin a machine-readable recursive manifest over EVERY behavior-critical file:
  `{version, supersedes?, reason?, frozen_at, head, files: {path: sha256}}`.
- Record the manifest SHA in the session registry; every downstream measured/consumer run
  verifies it BEFORE and AFTER the run.
- Any drift invalidates ALL downstream results: stop consumers, resume the drifting owner,
  pin a new manifest, rerun downstream. Never patch a hash constant in place.
- A legitimate post-freeze scope change (e.g. adding per-region occluder placement to a
  frozen renderer contract) = explicit v2 manifest with `supersedes` + `reason`, full
  downstream rerun, supersession recorded in the registry.
- **ONE authority only** (C2 verdict F2): after any manifest bump, grep every downstream
  evidence JSON for the OLD manifest SHA — any hit means stale evidence needing RERUN, not
  relabel. C2 pinned terminal-manifest v3 but all six measured rows + I05 decision still
  carried v2, while the harness ALSO trusted a legacy 3-file manifest and prose registry
  tokens — three competing "frozen" authorities. Pass the exact manifest path+SHA into the
  measured CLI; never allow newest-scan or fallback chains.
- **Canonical hash equality is a gate, not a label** (C2 verdict F3): independent recompute
  must use the SAME canonical formula (frame count + ordered shape + contiguous decoded
  bytes) fed by the public decoder — independence lives in execution, not in inventing a
  different serialization (ffmpeg rawvideo/rgb24 mismatches on pixel-order = false alarm).
  Assert per-row harness hash == adapter `output_frame_sha256`; add an adversarial test
  against raw-concat regression.

## 3. rg-gates cover active test code

- "No references to old artifact X" gates must sweep production AND frontend AND tests.
  Tests that still LOAD the deprecated artifact as frozen input pass their own suites while
  breaching the sprint contract (caught in C2 final gate: two T02 test files pointed at the
  v1 benchmark).
- Classify every hit before failing: operative load vs prohibition-note vs log history.
  An operative load IS a finding; prohibition notes and archival docs are allowed.

## 3b. Acceptance-proof discipline (C2 verdict F1/F5)

- Read WHAT an E2E asserts before crediting it: C2's "only-affected-regenerates" spec made
  a pin fail on purpose, replayed the old job, and asserted ZERO regeneration — green spec,
  missing P0 feature. Acceptance assertions must be POSITIVE (new generation + changed
  artifact ID/hash for affected loops), never merely "nothing broke".
- If production code lacks the acceptance mechanism entirely (e.g. confirm endpoint commits
  a correction but creates no regeneration job anywhere), no passing test closes the
  criterion — grep for the mechanism, not just the tests.
- Defects sitting on a REQUIRED flow are blocking regardless of owning lane: route them to
  the owner, never downgrade them to non-blocking notes because "not my lane" (C2 F5:
  CorrectionPanel affected_loop_ids + ApprovalPanel reasonsOf were logged as notes, Codex
  rated both P1).

## 3c. Terminal evidence hygiene (C2 verdict F6)

- Timestamps ONLY from actual `date` output — never planned times (C2 wrote "22:00" at a
  real 21:27). Counts/hashes/port claims come from the LAST command run on a QUIESCENT
  checkpoint, with exact command + exit code recorded ("356 passed" was stale; reviewer's
  fresh collect found 363 tests; "ports free" claimed while Next dev :3014 still listened).
- One append mechanism per registry entry (heredoc OR patch tool, never both) to avoid
  duplicate rows; correct via appended correction entries, never history rewrites.
- After writing the terminal state, ANNOUNCE standby explicitly ("Manager dừng, chờ Codex
  review; im lặng đến verdict kế tiếp là đúng protocol") — unannounced post-terminal
  silence reads as a hang ("sao thấy dừng 40m rồi?").
- Port/process cleanup requires ownership attribution first (PID → CommandLine proves the
  listener belongs to this worktree) before killing anything.

## 4. Manager BA-scope decisions get provenance

When workers surface multiple fix options (e.g. redefine fixture vs open renderer scope vs
new harness), the Manager picks ONE, records it in the registry citing the exact prompt
clause granting authority ("mục 3.2: group_occlusion required → option (b) chosen"), and
routes the implementation to the owning session. Reviewers then see the decision as
in-scope rather than invented authority.

## 5. Determinism & adversarial controls in benchmark gates

- Same-seed A/B comparisons strip ONLY the fields the results file itself declares as
  non-deterministic plus run-scoped artifact paths; anything else differing is a finding.
  When no declaration exists (C3 case), strip timing keys RECURSIVELY by name
  (`wall_time_ms_total`, `runtime_ms_per_frame_measured`, `wall_runtime_ms_per_frame`)
  at any nesting depth + run-scoped path keys (`artifact_path`, `run_dir`,
  `j1_manifest_path`, `adversarial_artifact`) — a top-level-only strip false-fails.
- Adversarial controls (e.g. source-reencode substitution) must read FAILED_AS_EXPECTED on
  every class they apply to — a passing control means the detector is broken.
- Evidence JSONs nest verdicts (`results[i].threshold_evaluation.overall_pass`) — print real
  keys before declaring "no pass evidence".

## 6. Stacked same-owner resumes: track PROCS, not lanes

Multi-phase rounds resume ONE owner repeatedly (PREP → FINAL → BINDING); each phase is a
separate background proc. Completion notifications can lag HOURS behind reality (S09-C3:
T04's PREP proc notified ~4h after dispatch, after two later phases were already stacked),
and concurrent `hermes chat --resume <same-sid>` processes appear to interleave session
history — two of three stacked T04 phases died exit=1 mid-diff while the newest survived.
- Before dispatching phase N+1 to an owner: `process(action='poll')` EVERY prior live proc
  of that owner; never infer liveness from lane-level heartbeat rows.
- If a later round survives while earlier ones died exit=1 mid-work, do NOT re-dispatch the
  dead attempts — the survivor's turn supersedes their scope; verify coverage against the
  full packet checklist instead.
- Liveness probe when log freezes: walk the Windows process tree from the dispatcher bash
  PID down to the leaf python (`Get-CimInstance Win32_Process -Filter 'ParentProcessId=…'`),
  then sample leaf CPU twice 60–90s apart — increasing CPU = ALIVE even with byte-frozen
  logs. Declare death only on (log frozen ×2) AND (leaf CPU static) AND (tree gone).
- **STALL vs DEATH vs CONTEXT-COMPACT (C3 BINDING, 26/08 night)**: three frozen-log cases
  need different responses. (a) *Stall* = log frozen ~20 min AND leaf CPU creeping
  (+0.16s per 5 min) → worker stuck waiting on the API stream; kill by explicit PID chain,
  wait the 5-minute window, resume SAME owner with SAME packet; the killed round's EXIT
  marker reads 127 (manager's kill, not a worker violation). (b) *Context-compact* = right
  after resuming a VERY LONG session, log can stay frozen 6+ minutes while CPU rises
  slowly and steadily — that is history reassembly; DO NOT kill during it (next sample
  burst +15KB mid-run). Killable combination is frozen log + FLAT CPU together. (c) *Death*
  = tree gone / poll not_found + no EXIT marker.
- **Chain pinning at bind time**: the FINAL binding packet lists every upstream SHA
  verbatim (manifest v4 `ae92247b…`, run_A content `12de1345…`, decision `d289929d…`)
  and forbids stale pins; manager verify then greps the ROUTE SOURCE for those literals
  (found at `s09_demo_compare.py:92` and `:103`) instead of trusting REPORT claims —
  source-line evidence survives any report inaccuracy.
- **Fill join-gate wait windows with cheap static gates** (ruff/mypy/alembic/OpenAPI
  count) while an E2E lane runs — foreground-only, zero write overlap, shortens the
  terminal path by up to an hour.

## 7. Contract-vs-schema contradictions are P1 defects (C3 endgame addendum)

- When a required Pydantic field contradicts the written API contract (real case:
  `RegenerateJobRequest.expect_content_sha256` mandatory while §3.2 said body =
  correction_id only), the CONTRACT wins — even if the extra field looks like
  "stronger safety". If the server already pins fail-closed server-side, a
  redundant MANDATORY client pin is a defect that bricks legitimate callers
  (every UI POST → 422). Fix = make it optional; keep the TOCTOU verification
  branch for callers that do send it.
- Replay/idempotency semantics must be asserted via identity + `reused` flag,
  never inferred from HTTP status (201 with `reused:false` on an identical
  job_id is broken mapping).
- An acceptance lane honestly self-declaring `BLOCKED_WITH_FINDINGS` and routing
  defects to owners is the gate WORKING — credit it in heartbeats, record its
  positive diagnostics (affected artifact hash changed for real, context SHA
  stable) as architecture evidence alongside the finding list.
