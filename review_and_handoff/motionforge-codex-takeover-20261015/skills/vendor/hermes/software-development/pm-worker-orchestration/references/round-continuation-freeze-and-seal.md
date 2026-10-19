# Round continuation, freeze-and-seal, and claim hygiene

Session-derived recipes for a Manager running multi-round corrective waves with CLI workers.
Complements `pm-session-execution` `references/worker-wave-verification-and-guard-classification.md`
(verification table, guard classes, liveness, narrative-vs-artifact, freeze *sequencing*) with the
mechanics that were missing there: how a round ends early, how to seal bytes after the fact, how to
freeze an evaluator input without clobbering it, and how to stop your own packet from becoming the
next defect.

## 1. A round can end "successfully" while the deliverable is missing

Observed twice in one wave with the same shape:

- worker exhausts its per-run tool cap (`~90` calls for `hermes -z`), exits `0`, and reports
  **`RUNNING`** honestly — all *measurements* done, the required *documents* not written;
- a second round exhausted the cap after fixing one row and before writing the evidence set.

So `exit 0` + `TASK_SUBMITTED` in the log are both claims. Before accepting either:

1. `ls -la` the exact artifact paths the packet names (documents, JSONs, media) and check sizes are
   non-zero;
2. run the worker's own suite yourself and read the count;
3. read the receipt (`exit_code`, `duration_seconds`, `packet_sha256`) and the session DB
   (`tool_call_count`, `ended_at`) to see *how* the round ended;
4. only then decide the terminal state.

**Continuation scoping rule.** When the gap is "measurements done, documents/commit missing", the
continuation packet must (a) list the exact missing items, (b) say explicitly *do not re-measure
anything — the numbers are on disk*, (c) name the one boundary item still owed, and (d) set a small
tool budget (~90 calls is a full round; a docs+commit round is well under it). Re-running the
measurement is the failure mode this rule exists to prevent.

## 2. The commit-seal round

A packet that grants no git authority is correct — but it leaves a verified fix uncommitted, so a
reviewer cannot tell *which bytes* were reviewed. Dispatch a tiny **git-only** seal round:

- preflight: `HEAD` unchanged and `git status --porcelain` shows **exactly** the expected modified
  paths, nothing more. Any extra path ⇒ stop, do not commit an unknown diff;
- confirm the content hashes still equal the ones in the worker's report; if a hash moved, stop;
- commit **only** the explicit paths — never `git add -A` / `git add .`;
- prove it: `git show --stat --oneline HEAD` (expect exactly N files), `git rev-parse HEAD` and
  `HEAD^` (parent intact), `git status --porcelain` empty, and `git branch -r --contains HEAD`
  empty (= on no remote);
- assert the committed blob equals the working-tree file: `git show HEAD:<path> | sha256sum` vs
  `sha256sum <path>`. A commit whose blob does not match the reviewed hash is worse than no commit.

Budget it as a seal (~15 calls), not a work round. A `git`-internal `bad object refs/...` /
`failed to perform geometric repack` message from a pre-existing dangling ref is non-fatal — verify
with `rev-parse` and disclose it rather than treating it as a failed commit.

## 3. Freezing an evaluator input (mechanics)

`manager/frozen/<candidateID>/` holds a copy the evaluator may read, hash-pinned, taken **after** the
writer is terminal:

- copy every file (source window, references, run records, graph JSON, frame map, pins, media) with
  `copy2` and immediately re-hash each copy; the manifest records per file: source path, frozen path,
  bytes, `sha256`, `match`, `mtime`;
- skip `__pycache__`/`*.pyc` and anything above a stated size ceiling — list the skips in the manifest
  rather than silently dropping them;
- manifest header: `freeze_id`, `frozen_at_utc`, sources, `file_count`, `bytes_total`,
  `hash_mismatch` (must be 0), `skipped`;
- **refuse to write into an existing non-empty freeze id** unless explicitly forced. This guard
  caught a real self-inflicted error: a `SNAPSHOT.md` written into the freeze directory *before*
  running the freezer made it abort with `freeze id exists and is not empty`. Order is: create the
  manifest first, then add any human-readable `SNAPSHOT.md` beside it;
- a correction ⇒ **new candidate ID and a new freeze**. Never reuse a path a review already read and
  never re-point a report at mutated evidence;
- say plainly in the freeze doc which artifacts are *not* frozen yet (e.g. the clip whose owner round
  is still running) so the evaluator does not assume more coverage than exists.

## 4. One heavy GPU job, without idling the CPU lanes

A "one heavy GPU job at a time" rule tempts you into serialising everything. Instead give the CPU-side
verification its **own** engine so it cannot contend:

- separate runtime directory inside the verifying task's write-set, its own port, `device=cpu`, and
  CUDA hidden (`CUDA_VISIBLE_DEVICES=` empty) — measured result: VRAM moved 1,104 → 1,102 MiB while the
  GPU-owning lane kept the card;
- reserve a **new** port number for each wave; reusing the previous wave's port lets a stale
  `instance_epoch` / lease from a dead server be mis-read as the current boot identity;
- verify the frozen baseline runtime is untouched by the CPU proof (`find <frozen-runtime> -newermt
  <wave-start>` empty) and state it as a guard row.

## 5. Your own packet is an evidence artifact too

Three claims the Manager had written into a packet were disproved by the reviewer, because they were
argued from a report instead of measured:

- "the render's PTS makes `pts = frame_id*512` impossible" — the delivered raw file was valid CFR;
- "the export drops the padding" — it dropped decoded frame 119 and kept the padding frame;
- "368 is the expected height" — 368 was only a step-16 generation canvas, and the mismatch against a
  360-row source was the actual defect.

Rules that fall out of that:

- before writing a claim into a packet, measure it or mark it as unverified;
- when a reviewer disproves one, require the owner to produce a **`CLAIM_CORRECTIONS.md`**: each
  disproved claim verbatim, then the replacement measurement that supersedes it. Fold a pointer into
  the successor packet so the wrong claim is not repeated;
- write row acceptance as *what to do*, not as a value to assert. "Pass the source geometry through
  unchanged, pad as a canvas step and crop back" beats "expect 368" — the latter invites the worker to
  make the gate agree with the bug.

## 6. Row registration, before any edit

For a finite correction matrix:

- register the **exact mandated test name** (or a documented 1:1 mapping onto an existing test) *before*
  touching code, and have the worker print that mapping;
- each row carries: before/after code hash, the raw command, exit code, expected vs actual, and a
  **negative control that is RED against the pre-fix bytes** (the previous bytes are in the Manager's
  preimage snapshot, so this is checkable, not rhetorical);
- disposition **100 %** of rows — `pass` / `fail` / `not-applicable` with a reason — and never let a
  broad suite's green stand in for a failing binary row;
- keep the rows in the final matrix with their measured values, not a test count.
