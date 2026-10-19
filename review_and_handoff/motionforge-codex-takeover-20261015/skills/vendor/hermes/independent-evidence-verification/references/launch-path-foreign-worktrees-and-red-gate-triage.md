# Launch-path traps, foreign worktrees, and classifying a RED broad gate (verified 2026-09-29)

Context: Manager orchestrating 3 concurrent lanes (Manager + GPU demo lane + CPU code
lane) in a many-worktree repo, dispatching via a Python launcher, on Windows/git-bash.
Every trap below cost a real cycle and each one wore a disguise that made a WRONG state
read as CORRECT.

## 1. An MSYS-shaped path passed to a Windows binary creates a phantom `C:\c\...`

Measured twice, two disguises:

**(a) Launcher argv.** `python -B dispatch_lane.py "$R/manager/packets/P.md" ...` (with
`R=/c/Users/Admin/...`) died with

```
FileNotFoundError: [Errno 2] No such file or directory:
  '\c\Users\Admin\Documents\Codex\...\manager\packets\D0-...md'
```

The launcher is a pure-argv passthrough, so the file clearly existed — the *value* was
rewritten. Fix that worked: write the path natively in the command itself
(`python -B dispatch_lane.py "C:/Users/Admin/.../D0-....md" ...`), never through a
`/c/...` shell variable. (Same family as the skill's pitfall about `"$VAR"/script.py`.)

**(b) `git worktree add` — the dangerous one.** Running
`git worktree add -b <branch> "$MSG_PATH/C11" <base>` from git-bash created the tree at
**`C:\c\Users\Admin\...\C11`** — and reported success. Critically, the immediately
following verification **PASSED for the wrong reason**:

```
$ git worktree list | grep -E "0929"
C:/c/Users/Admin/Documents/Codex/work/mf-delivery-20260929/C11   a52fca8 [codex/mf-end-11-c11-0929]
C:/c/Users/Admin/Documents/Codex/work/mf-delivery-20260929/C22   a52fca8 [codex/mf-end-22-c22-0929]
```

Right branch, right HEAD, clean porcelain — a `grep` for the branch name or a
`rev-parse` check confirms everything while the tree sits in a directory nobody will
ever `cd` into. The only tell was the literal `C:/c/` prefix.

Rules:
- Pass **native `C:/...` paths** to `git worktree add` explicitly; never let a shell
  variable carrying a `/c/...` value reach it.
- Verify worktrees by reading the **path column literally** (`ls -d <expected path>`
  must succeed), not by grepping for the branch or asking `rev-parse` — those answer a
  different question and will certify the phantom.
- Cleanup: `git worktree remove --force "C:/c/..."` **then** `git branch -D <branch>`
  (the branch survives the tree removal), then re-add with the explicit native path.
  Confirm with `ls -d /c/c && echo BAD` → expect absent.

## 2. Untracked foreign worktrees in a shared repo are NOT covered by your guard

A new worktree appeared mid-run (`mf-external-review-20260929`, branch
`codex/external-review-20260929`) with **740 dirty paths** and docs named
`SOURCE_DELIVERY.md` / `CODE_SNAPSHOT_MANIFEST.json` — not created by this Manager.
Dating it decides the response: walk the tree and bucket by `getmtime` age
(`now - m < 1800`); 2703 files in the last 30 min means an **active external writer**,
not a stale leftover.

Consequences that matter:
- Your byte-safe write-set guard only covers the paths YOU registered. A concurrent
  external writer is invisible to it — enumerate `git worktree list` on the shared MAIN
  repo at preflight and again at every wave boundary, and record the ones you did not
  create plus their observed write activity.
- Do not "tidy" or remove them (never delete a worktree/branch with uncommitted work);
  record them as a disclosed observation and, if they touch your integration base,
  raise it before freezing.

## 3. A late exit-notice from a DEAD dispatch handle reads like a live lane's result

The first dispatch attempt failed instantly on the path bug above; it was re-dispatched
under a new handle. Minutes later the runtime delivered a completion notice for the
**old, failed** handle whose command text was nearly identical. Acting on it would have
recorded a phantom lane failure for a lane that was healthy.

- Keep handles distinct and check the notice's **exact command/packet path** against the
  live table before trusting the verdict; a stale handle's exit code describes a process
  that never did any work.
- Corollary for the reverse case (run ended, notice pending): the durable signal is the
  **lane log's size + mtime**, not the notice. `log_last_write_ago_min == 0.1` with a
  growing byte count disproves "the lane died" regardless of what a notice claims.
- Also close/finish dead handles explicitly so their notices cannot be confused later.

## 4. Classifying a RED broad gate: cross-lane seam vs regression

A lane's broad gate came back `891 passed, 1 failed`:

```
tests/product_delivery/test_mf_end_28.py::test_28_2_builder_is_deterministic
  AssertionError: committed inventory.json is stale vs a fresh build
  app_tree_sha256 26ef7c09… (committed)  !=  1f7999ec… (fresh)
```

The assertion hashes **`backend.app_tree_sha256` — the whole `app/` tree**. The lane
under test had legitimately changed one file under `app/`, and the packaging inventory
that records that hash belongs to a DIFFERENT task's write-set. So the red is a
**cross-lane process seam, not a regression by the writer**.

Triage recipe (do this BEFORE reporting or routing a defect):
1. Read the failing assertion and identify **what artifact it hashes/compares**.
2. `git show --stat` the artifact and the test; map both to a Task ID via the write-set
   matrix. If the artifact is **outside the writing lane's allowlist**, it is cross-lane.
3. Do NOT let the writing lane touch it (no "while you're in there") and do NOT waive or
   skip the test. Record a `CROSS_LANE_BLOCKERS.md` entry: measured command + verbatim
   assertion output + mechanism + the OWNING task id + the correct ordering.
4. Ordering matters: for an inventory that must reflect a **frozen** candidate, the
   refresh belongs to the later packaging task, AFTER the journey is frozen and BEFORE
   the final single broad integration gate. Regenerating it early just re-stales it on
   the next `app/` change, and running the final broad gate before the refresh
   guarantees one red for a non-product reason.
5. Note the recurrence count in the entry. The same seam appearing 4 times in one
   project is a **verification-ops** defect, not a per-lane bug, and deserves a
   standing rule rather than a fourth ad-hoc fix.

Symptom to recognise: **exactly one** red, in a *neighbouring* task's file, caused by a
hash/aggregate that spans the whole tree — while the lane's own focused tests are green.
