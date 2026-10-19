# Structured terminal records + consumer patching (measured 2026-10-11, MF-DEMO-LONG-01 R4)

## Why prose classification dies
The legacy dispatcher/heartbeat read the LAST occurrence of a status token in the worker
log tail ("latest occurrence wins"). A closing message that says
"...→ SELF_REVIEW_PASS_PENDING_CODEX" as a NEXT STEP beats the actual terminal
"CONTINUE_REQUIRED" appearing earlier in the same message — the round was recorded as
SELF_REVIEW_PASS_PENDING_CODEX while the worker had actually yielded for continuation.
Exit code 0 is NOT completion, and no substring ordering fixes this: the worker's own
plan text will always be able to contain terminal-looking tokens. Fix: a separate
structured JSON record, bound to the invocation, validated fail-closed.

## Contract shape (Pydantic strict, extra='forbid', duplicate keys rejected)
File: `<allowed_root>/evidence/terminal/<invocation_id>.json`, written atomically
(tmp file + os.replace). One record per invocation, written on EVERY terminal —
including CONTINUE_REQUIRED / USER_STOP / BLOCKED.

Fields: run_id, task_id, revision, owner_sid, invocation_id, packet_sha256 (the binding;
ALL SIX values come from the Manager's immutable dispatch record), schema_version,
status (EXACT enum: CONTINUE_REQUIRED | TASK_SUBMITTED | USER_STOP | BLOCKED),
reason, remaining_work (list), artifacts (list of {kind, path, sha256}),
matrix (Q01..Q12 -> PASS/FAIL/UNKNOWN).

Gates:
- CONTINUE_REQUIRED requires non-empty remaining_work (a concrete next action).
- TASK_SUBMITTED requires: remaining_work empty; matrix exactly Q01..Q12 all PASS;
  exactly one artifact per required kind (master/comparison/matrix/checkpoint/receipts);
  each path absolute, inside allowed_root, unique, existing, sha256 matching; the
  matrix artifact file content must equal {"rows": record.matrix}.
- Everything else — missing file, truncated JSON, duplicate key, wrong
  owner/invocation/packet, stale invocation, artifact outside root, exit != 0,
  infrastructure error in the log, child still running — maps to
  NEEDS_RECONCILIATION. Never a pass, never auto-resume.
- TASK_SUBMITTED yields PENDING_MANAGER_QA only; the Manager still re-runs the
  decisive checks (guard diff, artifact hashes, held-out frames). Never acceptance.
- Old records are immutable: new rounds get new records; never backfill a validation
  into a past round.

## Binding without circular hashing
1. Dispatcher mints `invocation_id` (task + UTC + random suffix).
2. Dispatcher reads the packet FILE bytes once; `packet_file_sha256` = sha256(file bytes).
3. Prompt = file text with `{{INVOCATION_ID}}` and `{{PACKET_SHA256}}` placeholders
   replaced (the packet template carries the placeholders; keep the template under
   the ~28K argv ceiling check AFTER substitution).
4. Receipt + append-only DISPATCH_LEDGER row record: run_id, task_id, revision,
   owner_sid, invocation_id, packet_file_sha256 (plus the prompt sha separately).
5. Consumers build the EXPECTED binding from the LEDGER row (append-only = immutable) —
   never from the receipt alone (the receipt is rewritten at end) and never from the
   worker's self-declared output. The worker echoes the two substituted values verbatim
   into its record.

## Patching existing consumers: one byte-exact apply script, not N fuzzy patches
Pattern that worked for a 12-anchor + 6-anchor patch of two live scripts:
- One script holds a list of (old, new) exact strings. Before ANY write, assert
  `text.count(old) == 1` for EVERY anchor; a DRY=1 env mode validates counts only.
- Write with `newline=''` to preserve LF; regenerate unified diffs vs the preimages
  for the record; `py_compile.compile(doraise=True)` both files; record
  before/after bytes/lines/sha256 into an evidence JSON.
- Byte preimages copied BEFORE patching; diffs + facts go to the evidence root.
- Additive fixes discovered after the first application: apply a second bounded patch,
  then REGENERATE the diffs vs the original preimage (never hand-edit a diff).

## Variable-name collision the tests caught, not the patch
The legacy dispatcher constant `RUN_ROOT` actually held `<run>/manager` (dirname of
dirname of the script). Mapping an env override `MF_RUN_ROOT=<run>` straight onto it
sent the dispatch ledger to `<run>/DISPATCH_LEDGER.jsonl` instead of
`<run>/manager/DISPATCH_LEDGER.jsonl`. Rule: before adding an env/root override,
trace EVERY path constant to its producer and keep the original no-env value
byte-identical to what shipped. The first consumer test (controller-lock refusal)
surfaced it pre-dispatch.

## Testing ACTUAL consumers (not helpers): MF_RUN_ROOT isolation
Add an env override so the REAL scripts compute their paths from a temp scaffold:
`MF_RUN_ROOT=<tmp> python -B manager/tools/dispatch_long.py ...` — ledger, lock,
lease and heartbeat files land in `<tmp>/manager/...` while the script bytes are the
shipped ones. The child process runs a fake-child python script injected via the
existing test argv-prefix override (DISPATCH_TEST=1 +
DISPATCH_HERMES_ARGV_PREFIX=[python, fake_child.py]); the fake child parses the
substituted binding out of the prompt exactly like a real worker would, writes logs
and (per mode) a terminal record.

Adversarial matrix that passed 70/70 (case -> expected authoritative class):
- future / quoted / negated PASS prose + valid CONTINUE_REQUIRED record => CONTINUE_REQUIRED
  (also assert legacy_prose_class = SELF_REVIEW_PASS_PENDING_CODEX to prove the old trap
  would have misread it).
- prose only, NO record (fixture gotcha: the fake child must skip writing the record in
  this mode — forgetting one mode produced a false FAIL; when a case fails first check
  whether the CODE or the EXPECTATION is wrong).
- truncated JSON / duplicate JSON keys / wrong owner / wrong invocation / wrong packet /
  missing artifact / matrix mismatch / empty continuation => NEEDS_RECONCILIATION.
- exit0 + "API call failed after 3 retries" present in the log => NEEDS_RECONCILIATION
  (infrastructure fail-closed; match the full retry phrase, not bare "API call failed",
  to avoid transient text false-positives).
- nonzero child exit => NEEDS_RECONCILIATION.
- correct TASK_SUBMITTED (all 5 artifact kinds + artifact matrix == record matrix)
  => TASK_SUBMITTED + VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA.
- controller lock held by a live pid => dispatcher rc=4, ledger row
  action=dispatch_refused reason=controller_locked, and NO child spawned.

## Legacy roll-out
Old receipts have no `terminal_validation` key. Consumers must classify them as
LEGACY_NO_STRUCTURED_TERMINAL and keep the old prose class only as
`legacy_prose_class` (reference, never authority). Re-run a real legacy receipt (the
misread round's actual bytes) as a test case and assert its class is NOT a completing
status.

## Controller lock + GPU lease (invocation runtime module)
- Controller lock: `filelock` on `<manager>/locks/controller.lock` + meta JSON
  {owner_sid, pid, created (wmic-format), name}. Dispatcher acquires BEFORE any write;
  another LIVE holder => rc=4 + ledger row `action=dispatch_refused,
  reason=controller_locked`, NO child spawned. Holder DEAD (identity False) =>
  `break_lock()` + supersede; holder UNKNOWN (AccessDenied) => refuse (fail closed).
  Release writes `released_utc` + outcome into meta.
- GPU lease: one JSON per invocation under `<manager>/leases/` with
  run/owner_sid/invocation_id/job/children[{pid,created,name}]. Release ONLY when every
  child identity is gone AND the render probe is quiet (Comfy /queue empty AND no
  `-B …p4_wan_run*/render_run*/r4_render*` process). Detached child / UNKNOWN probe /
  active queue => keep ACTIVE + `detached:true` + append `release_attempts`. Controller
  exit NEVER frees a busy GPU lease. Measured happy path: child DEAD + queue empty =>
  `released:true {"detail":"no queue job, no runner process"}`.
- Identity: psutil (pid + create_time + name); NoSuchProcess => gone; AccessDenied =>
  UNKNOWN (never read as dead). `wmic_like(epoch)` emits legacy
  `YYYYMMDDHHMMSS.ffffff+HHMM` so wmic-era ledger rows still verify; compare ±2 ms.

## Heartbeat consumer cases (fixture ledger + `--once`)
- validated record => `outcome.class == record status`, `source == "structured_terminal"`;
  row also carries live `controller_lock` + `leases` arrays.
- open invocation + LIVE child pid in the `child_spawned` row => llm_worker_alive true,
  outcome INVOCATION_OPEN; the active lease lists the child as ALIVE.
- REAL legacy receipt bytes => LEGACY_NO_STRUCTURED_TERMINAL; assert class != the old
  prose class and that `legacy_prose_class` preserves it.

## Further field pitfalls (all measured 2026-10-11)
- venv `python.exe` is a REDIRECTOR: it launches a base-interpreter child with the same
  command line => two pids for ONE logical loop (parent->child ppid chain). Do not read
  it as a duplicate process.
- Manager-owned rows (e.g. Q11) reference evidence OUTSIDE the worker's allowed root;
  the artifact-scope check rejects cross-root paths. Publish the evidence, give exact
  paths, and instruct the worker to COPY it into its own root before submission
  (kind `other` + hashes). A worker's "evidence not available" may simply predate the
  file — re-point with the exact path.
- Guard cadence: PRE manifest of the whole protected set BEFORE first dispatch; MID
  manifest at each invocation boundary while the worker is idle; POST at round end;
  diff vs ALLOWED_NEW_PREFIXES (CLEAN = 0 changed / 0 removed / 0 unauthorized added).
  ~38k files => minutes; run scans in background.
- Manager post-invocation re-verification: re-run the validator on the record BYTES +
  recompute every artifact sha256 + check lease release; write `INV_VERIFY.json`. Never
  trust the receipt's cached verdict (R4 invocation #1: 9/9 hashes rechecked,
  PENDING_SAME_OWNER_CONTINUATION, lease RELEASED). For an AV master add the independent decode
  proofs: `ffprobe -select_streams v:0 -count_frames -show_entries stream=nb_read_frames` must
  equal the contracted frame count (R5 master: **9000 decoded**) plus a
  `ffmpeg -v error -i <master> -f null -` decode smoke; header duration alone is not a
  frame-count proof.
- Swap monitor loops via STOP file + identity census, never pattern-kill: write STOP,
  poll until the recorded pids are gone (identity check), DELETE the STOP file, start
  the new loop; keep before/after census in evidence.
- Starter template for the 70/70 consumer matrix: `templates/fake-terminal-worker.py`.
- Deterministic lease-vs-detached-runner probe: `scripts/lease-runner-probe.py`.

## Tail additions — measured later the same day (R4 inv #2/#3)
(These deepen, not replace, the sections above.)

- LEASE WATCH LIST MUST COVER THE NAMING YOU INSTRUCT: extend the runner watch to
  `p4_wan_run*/wan_run*/render_run*/r4_render*/r4_build*`. Workers launching long detached
  batches name the launcher `r4_build*`/`r4_render*` so the lease survives the LLM child
  exiting mid-batch (that is the entire point of `detached:true`). Re-proven with
  `scripts/lease-runner-probe.py` (4/4): a live `-B …r4_build_probe_runner.py` blocks
  release with reason `render active`, lease stays ACTIVE+detached; after the runner dies,
  `released:true`. On a machine with no Comfy server the probe fails CLOSED with
  `render probe unknown` (still blocked) — probes should accept either reason.
  (SUPERSEDED mechanics, R5 v2 below: name-substring + `-B` matching missed native exes and
  other scripts — use spawn-shape basename matching instead; the naming principle stands.)
- HEARTBEAT CLOSURE CAN LAG ONE TICK — diagnose, never re-fix: the heartbeat READS the
  ledger at iteration start, then spends seconds on the tree walk + probes before WRITING
  its row; a terminal landing inside that window is reported once as `open:true` /
  "no closing terminal row" (measured: terminal row 07:12:56.18; tick written 07:13:07.83
  still "open" while `llm_worker_alive` was already false; next tick 07:15:12 =
  `closed by launcher_pid terminal` + CONTINUE_REQUIRED + `source: structured_terminal`;
  a manual `--once` matched). Recipe: (1) recompute the closed-detection logic
  (closed-launcher_pid set vs the last dispatch row) against the CURRENT ledger — if that
  says closed, the consumer logic is fine; (2) run the monitor once (`--once`) for a fresh
  authoritative row; (3) trust the N+1 tick. Never patch the monitor for a single lagged
  tick; the lagged row's other probes can be mid-transition too — cross-check two ticks
  before any alarm. Mirror race on the OPENING side (measured R5d): a tick whose ledger read
  lands a fraction of a second BEFORE the new dispatch row is written reports the PREVIOUS
  (closed) invocation — the next tick shows the new invocation open with llm ALIVE and the
  fresh lease. Same two-tick rule; never "fix" the monitor for it.
- CENSUS HYGIENE — the probe matches ITSELF: a process census whose filter string appears
  in its own `python -c` argv matches the probe, and `bash -lic …` wrapper shells whose
  command text contains the script name match too. Measured artifacts: an 8-not-2
  "heartbeat" count and a phantom third-loop pid that lived seconds. Match on interpreter
  pid + parsed argv fields, exclude your own pid, and count wrapper shells separately from
  loops. (Complements the venv-redirector bullet above: redirector = parent/child pair,
  census self-match = the probe and its wrappers.)
- LONG BUILDS ACROSS INVOCATIONS (worker packet guidance): have the worker produce a
  per-shot deterministic batch script + state file (shot -> status/receipt/wall) + an
  append-only runs ledger; launch it DETACHED under the watch-list naming; every resume
  re-renders ONLY missing shots (reuse exact hashes). Tune parameters (frame-step /
  worker count) only after validating on the hard samples with per-unit receipts; let the
  LLM yield per invocation instead of babysitting the render loop.

## Stall-kill of the LLM while the detached batch runs (measured R4 inv #3, 08:56:35Z)

What fired: the dispatcher's stall detector saw the worker LOG silent 3602 s > 3600 s and killed
the LLM pid only. Receipt: `exit_code:1, timed_out:true` → outcome `NEEDS_RECONCILIATION` — the
EXPECTED fail-closed result for a killed invocation. No terminal record exists and none is coming;
never wait for one — reconcile from the ledger + disk, then resume.

What survived (live design proof): Windows `TerminateProcess` kills the LLM pid only — NO tree
kill. The detached `r4_build_batch.py build` stayed alive (pids still running 65+ min later,
BUILD_STATE kept advancing), and at controller exit the lease release attempt matched the runner
(`render active`) and correctly kept the lease `ACTIVE`/`detached:true` — the live counterpart of
the lease-runner probe.

Root cause + prevention (put the NUMBERS in every packet that spans a long detached job):
- silence budget: no single silent wait may approach the 3600 s threshold — keep every blocking
  step under ~20–30 min and make each wait PRINT ≥1 line (progress tally). The principle alone
  ("don't babysit silently") was already in the packet and the worker still went quiet — spell
  out the budget in minutes.
- prefer chained short polls (`sleep 600; echo POLL-n; <read state file>`), interleaved with
  non-GPU prep (assembly script, QA harness, receipts, matrix).
- when nothing is left to do while the batch runs: write CONTINUE_REQUIRED (remaining = poll /
  assembly steps) and YIELD; the batch runs independently and Manager resumes later.

Reconcile-then-resume checklist (one tool batch, measured): (1) receipt utc_start/end, exit_code,
timed_out; (2) batch pids ALIVE — see attrs pitfall below — + out.log mtime/tail; (3) BUILD_STATE
tally (done/rendering/failed) and re-derive the CURRENT runner pid/log (packets may cite a stale
one after a worker relaunch); (4) lease file status/detached/`release_attempts`; (5) targeted
scope scan = files newer than the previous boundary outside allowed prefixes (cheap MID variant;
full PRE/MID/POST manifests stay for boundaries/round end); (6) resume the SAME SID with a
RE-ATTACH packet: "do NOT kill/relaunch the batch; re-derive its state first; only relaunch from
BUILD_STATE if the runner is actually dead."

Stale-lease bookkeeping: a lease left `ACTIVE`/detached by a KILLED invocation never
auto-releases (only its own dispatcher releases at its own exit) — release it from a later
reconcile once the runner is gone + queue quiet, or it lingers in every heartbeat row.

- psutil attrs completeness (caused a false "batch died" alarm): the `process_iter(attrs)` list must
include EVERY field the filter dereferences. With attrs `['pid','cmdline']` a filter touching
`p.info['name']` sees None → `'python' in None.lower()` raises → a blanket `except: pass`
silently drops EVERY row → "batch pids: []" false negative. Re-run with the full attrs list
before concluding a detached job died. (Distinct from the census self-match bullet above.)

## R5 v2 upgrades (measured 2026-10-12, MF-DEMO-LONG-01 R5) — supersedes parts above

The R4-era consumers above were still beatable (fresh review probes, O/FRESH_PROBES_R4):
heartbeat accepted a stale/wrong-invocation record and an UNKNOWN decision as TASK_SUBMITTED;
dispatch spawned a child while another live GPU lease existed (controller lock free ≠ GPU job
finished); `child_state is not True` read UNKNOWN as reconciled and submitted; stall-kill fired
on log silence while the batch advanced; the runner watch list missed native exes and non-`-B`
scripts. The v2 rules:

### Render-liveness probe — match SPAWN SHAPES, never raw cmdline text
- Detect (A) native exe: argv[0] basename contains a runner name (`ebsynth`, ...); or
  (B) interpreter+script: program basename contains `python` AND a later argv item (≤400 chars,
  no newlines) has a basename ending in `.py/.exe/.bat/.cmd/.pyd` whose stem matches the runner
  list (`video_blend`, `sam2`, `r4_build`, `render_run`, `wan_run`, `vace`, `gmflow`, ...).
- NEVER substring-scan the whole command line: the LLM child carries the PACKET TEXT in its argv,
  so packet words ("sam2", "vace") false-positive and would deadlock lease release forever.
  Exclude manager tools by basename (`dispatch_long`, `heartbeat_long`, `test_`...). Keep packet
  text free of literal `.py` script names when feasible.
- Probe failure stays UNKNOWN — never reads as quiet.

### Lease reconcile barrier (under the controller mutex, BEFORE writing anything)
- Scan EVERY non-RELEASED lease + ledger `child_spawned` lineage for its launcher:
  child ALIVE → refuse (rc4, ledger `dispatch_refused reason=gpu_lease_barrier`, NO spawn,
  lease untouched); child UNKNOWN → refuse (fail closed, needs reconciliation).
- `RESERVED` status = live claim: launcher alive/unverifiable/recent → refuse
  ("reservation in flight"); launcher verified DEAD + age ≥ ~120 s + queue quiet → adopt
  (mark RELEASED with `adopted_by` + evidence).
- ACTIVE with all children verified DEAD + render probe quiet → adopt (release with evidence),
  then proceed. "A free controller lock is NOT proof an older GPU job finished."
- Barrier at reserve/spawn: write `lease_reserve` (status RESERVED + launcher identity) BEFORE
  Popen; promote to ACTIVE with child + spawn-time descendants after; `lease_abandon` ONLY when
  no child was spawned. Race test: two dispatchers on one scaffold → loser rc4/controller_locked,
  exactly ONE `child_spawned` row.

### Terminal strictness ("UNKNOWN children never submit")
- `child_reconciled = child_pid is not None AND child_state is False` (verified DEAD only).
- Release the lease BEFORE the verdict; `invocation_terminal = child_reconciled AND lease
  released` (queue + owned jobs reconciled). Lease that cannot release (child alive / probe
  unknown / queue busy) → NEEDS_RECONCILIATION even on an otherwise valid record.

### Stall audit (supersedes the stall-kill behavior section)
- Log silence > threshold = AUDIT trigger only: measure artifact delta (newest mtime under watch
  roots > window start), recursive descendants, Comfy queue/render probe. PROGRESSING (fresh
  artifacts) or UNKNOWN (any probe unverified / render busy) → reset the window, keep waiting.
  TRUE_HANG ONLY when artifact delta is zero AND the render probe is VERIFIED quiet → kill with a
  distinct classification for same-owner resume.
- Do NOT gate on "all descendants dead": the venv shim's base-python re-exec (the actual worker)
  is a live descendant by construction — that gate never fires. The machine-wide render probe is
  the kill discriminator.
- Silence is measured AT CHECKPOINTS: on every poll, any log growth resets the window. Design
  fixtures with artifact writes spanning ≥2 stall windows and a threshold comfortably > poll
  interval; audits then land every ~2×poll.
- Watch-root default: `[allowed_root, D/input|output|temp/<revision-tree>]` derived from
  allowed_root (its parents[2] = task root). Verify the derivation against the REAL path shape;
  tests may pass `--watch-root` explicitly (point it where the child actually writes, or the
  delta reads as zero).

### Heartbeat binding revalidation
- `effective_outcome` must validate the receipt against the IMMUTABLE dispatch row
  (invocation_id / owner_sid / run_id / task_id / revision / packet hash) + a KNOWN decision
  enum; stale receipt / wrong owner / unknown decision → NEEDS_RECONCILIATION. Keep this
  function SELF-CONTAINED (no imports at call time): the review probe AST-extracts it with a
  minimal namespace ({os, markers}) and cross-module references fail there.
- Then `revalidate_terminal`: re-run the full validator against CURRENT artifact bytes with the
  binding from the dispatch row; a cached `terminal_validation` is never authority. Wire: closed
  invocation + structured outcome → revalidate → NR/mismatch downgrades the heartbeat row.
- Schema revision: controlled `Literal['r4','r5']` extension; old-revision records stay
  immutable and CANNOT bind a new-revision dispatch (binding mismatch = NR).

### Probe/test replication notes (what the fresh review actually runs)
- Recreate the probe SHAPES in your own suite: (1) stale-binding + unknown-decision heartbeat via
  AST-extracted functions; (2) ACTIVE-lease fixture with a live sleeper child; (3) a wrapper that
  patches `identity_alive` so a gone pid reads None (AccessDenied model) for unknown-child;
  (4) three runner-fixture process commands for the render probe; (5) two-controller race with a
  long-running winner child. With the v2 barrier the unknown-child wrapper gets REFUSED at
  reconcile — that is a correct fail-closed outcome too.
- Fake-child modes that paid off: ok_submit / ok_continue / silent_batch (artifact writes every
  ~1.5 s for ≥2 stall windows, no log growth) / hang (no writes) / tamper (write a valid record,
  then append bytes to an artifact → hash mismatch on recheck).
- Two fixes came from debugging the FIXTURE, not the code: watch-root pointing at the wrong dir
  (delta invisible), and a tamper mode that forgot to ALSO set status/artifacts (so the hash was
  never checked). When a new test fails, first decide whether the CODE or the EXPECTATION is wrong.

### Record-first + budget-pre-record reconcile (measured 2026-10-12, R5 continuation rounds)

- Budget can land BEFORE the record write: exit 0 + prose CONTINUE_REQUIRED + NO terminal record
  → dispatch correctly returns NEEDS_RECONCILIATION (`[WinError 2] ... terminal/<inv>.json`).
  Never backfill the closed invocation's record (immutable history); resume the SAME SID with a
  corrective continuation. Full triage + the RECORD-FIRST packet rule (skeleton at start,
  refresh at milestones, refresh at ~65-70/80 turns):
  `independent-evidence-verification/references/iteration-budget-exhaustion-and-finish-packets.md` §8.
  Measured live: next invocation's skeleton record existed ~1 minute after dispatch.
  RECORD-LAST follows (next round, same day): a record refreshed BEFORE later appends to a listed
  `*_RUNS.jsonl` failed with `artifact hash mismatch: <kind>` → NR. Treat the record refresh as the
  FINAL write of the turn; keep volatile append-only receipts out of mid-flight records. Full case:
  iteration-budget §8a.
- v2 barrier + terminal strictness behave correctly in production: observed lease lifecycle
  `RESERVED → ACTIVE (children incl. spawn-time descendants) → RELEASED` with `release_attempts`
  evidence; heartbeat revalidated a genuine CONTINUE_REQUIRED record without downgrading it.

### New-Manager takeover audit (measured 2026-10-12)

- WHO is the controller: read the previous Manager session's LAST messages in the Hermes DB — an
  UNANSWERED dispatch/user message (no assistant reply after it) means that controller never
  acted; do not assume it dispatched, do not resume it, and record the takeover in the registry
  BEFORE any new dispatch (session_id + takeover_utc + note + controllers_history append).
- Zero-writer audit set (all must be clean before resume): every lease `status` (want RELEASED),
  controller-lock meta `released_utc`, Comfy `/queue` empty, process scan for worker/render pids,
  GPU util. "Heartbeat bg still running" is not liveness proof of a render.
- mtime-cut gotcha: `time.mktime(time.strptime('YYYY-MM-DD HH:MM:SS'))` parses LOCAL time — for a
  UTC boundary use `datetime(..., tzinfo=timezone.utc).timestamp()`, or a "changed since takeover"
  list reads a shifted window and flags pre-existing files as unauthorized writes.
- Hermes state.db (open read-only: `file:...?mode=ro` + `PRAGMA query_only=1`): table `sessions`
  is keyed by `id` (NOT `session_id`); `messages.timestamp` is an epoch float; recent-session SQL
  must compare numerically (`started_at > strftime('%s','now') - N*3600`) — a float-vs-string
  compare matches nothing and silently returns an empty list.
