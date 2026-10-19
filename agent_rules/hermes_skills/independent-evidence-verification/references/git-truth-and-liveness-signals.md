# Git truth, liveness signals and gate exit codes

Session-specific detail from the MF correction round `20260924T1055Z` (8 lanes, 13 dispatches, 13/13 PROVEN).
Every rule below was paid for with a measured false positive; the numbers are the evidence.

## 1. Content proof across worktrees: compare BLOBS, never worktree bytes

A cross-check of a merged integration tree against each source worktree reported **3 files "DIFFER"**. The same check at
blob level matched **4/4**:

```
git rev-parse <source-rev>:<path>   # vs
git rev-parse HEAD:<path>           # in the integration tree
```

Cause: `core.autocrlf=true` with no `eol=lf` pin for that path. The same blob checked out as
**68,616 B LF-only** in one worktree and **70,237 B with 1,621 CRLF pairs** in the other. Rules:

* prove content with blob ids (`git rev-parse <rev>:<path>`, or `git diff <revA> <revB> -- <path>`);
* treat a worktree-byte mismatch as **unproven**, not as a difference — and say which of the two you measured;
* only after the blob proof, state that a transport is content-exact.

## 2. An authorized HEAD advance is not protected-tree drift

When one owner legitimately transports merged ranges, **another lane's tree HEAD moves**. Measured: the QA tree was
advanced to the frozen integrated candidate on the Manager's instruction, and the baseline-comparison guard reported
`protected_tree_drift:S12QA`.

Proof recipe before accepting it (do these, then exclude the lane from the drift check — do not weaken the guard):

1. the new HEAD equals the artifact the Manager named (here: the frozen candidate id);
2. the lane's own range still exists in the new history: `git merge-base --is-ancestor <lane-range-tip> <new-head>` ⇒ rc 0;
3. `git status --porcelain` = 0;
4. the diff the advance introduced contains only the transported ranges' paths.

Write the ancestry proof into the verification note; "the guard complained but I ignored it" is not a proof.

## 3. A gate's exit code read through a pipe is the pipe's exit code

Measured: `npm run build 2>&1 | tail -30; echo "RC=$?"` printed **RC=0** while the real lint/build results included
failures (`npx eslint` true RC = **1**). `$?` after a pipeline is the **last** command's status (`tail`), which is always
0.

* For every gating command: redirect to a file (`cmd > out.txt 2>&1`) and capture `$?` on the next statement, or use
  `${PIPESTATUS[0]}` immediately;
* re-run any gate whose RC you only ever saw through a pipe before writing a verdict;
* in a report table, print the **true** RC and say that the earlier piped run was discarded.

## 4. Liveness hygiene for long background lanes

A watchdog that captures `{pid set, session ids}` at launch goes stale the moment workers rotate (turn-budget exits,
5-minute 502 resumes). Two measured false alarms in one round:

* `ALL WAVE-A WORKERS EXITED` printed while **three fresh runs were live** (their pids were not in the captured set);
* a `STALL` flag fired for a lane whose launcher **receipt already existed** — i.e. it had finished cleanly.

Rules:

* treat the existence of the launcher's receipt file as `DONE(exit, not stalled)` and exclude that lane from stall logic;
* **re-arm** the pid/session set at every dispatch (cheap: one process-table query + one read-only session-DB query);
* judge liveness from the session DB's newest message timestamp **plus** the process table — never from exit codes or a
  captured pid list;
* on the 8-minute no-progress audit, read the receipt + log payload **first**: a lane with no new rows whose last message
  is ~8 minutes old and whose receipt exists is FINISHED, not hung.

## 5. Windows MAX_PATH on deep probe scratch

Copying a reviewer probe into a deep evidence path produced
`<scratch>/<case>/reservations/<32-hex>__att.reservation.json.tmpNNNNN` ≈ **262 chars**, and the run died with
`FileNotFoundError` at file creation — after the **first two cases passed**, so it reads like a mid-run logic error.
Use a short Windows-native temp root (`C:/Users/<u>/AppData/Local/Temp/<tag>`) for probe scratch and keep only the
results JSON inside the deep evidence root.

## 6. Reusing an external reviewer's probe without corrupting their evidence

* The reviewer's script usually writes its JSON **next to itself** (their evidence dir). Copy it into your own scratch and
  rewrite **only** the output/scratch path lines; assert the rewrite landed (`"manager" in text`) before running, and say
  in the note that the reviewer's file was not touched.
* After a fix, the reviewer's script may **abort** because the fixed code now refuses instead of returning the old shape.
  That abort *is* the fix: wrap each case in `try/except` and capture `type` / `.code` / message, or you will only learn
  the first refusal (measured: the QC probe died on builder #1 and revealed nothing without the wrapper).
* An intentional signature change is part of the fix. Example: replacing a caller-supplied `identity_matches: bool` with a
  backend-resolved proof object means the reviewer's old call raises `TypeError`. Record it as a **disclosed interface
  delta** with a worked replacement call, then verify the **intent** — foreign actor refused, true owner still admitted,
  forged proof rejected — rather than the old call shape.
* Watch for hand-forged fixtures passing by accident: a hand-built integrity digest was refused
  (`identity_proof_integrity_failed`) while the builder-computed one was accepted — build fixtures through the project's
  own fixture helpers, not by typing values.
* Deep-hashing a reviewer's "before" evidence against your own re-run is the cheapest cross-check: worker↔manager
  agreement (9/9 identical case fields) is worth more than either side alone.
