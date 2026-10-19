# Proving a regression test actually catches the defect (base control) — verified 2026-09-30

A packet commonly demands a test that is worth something:
*"new E2E must catch the missing CTA/caller or a wrong selected ID — static-only
is not enough."* A test that passes on the candidate proves **nothing** about that
claim. The only measurement that does is a **base control**: run the *same* test
bytes against a **pre-patch tree at the same base**, and show it goes RED.

## The technique

1. **Freeze the spec first.** Record its sha256. Every side of the comparison must
   use byte-identical test code, or you are measuring two different tests.
2. **Create a disposable worktree detached at the task's BASE commit** (not a
   branch tip, not the candidate):
   `git worktree add --detach <CTRL_DIR> <base-sha>`.
3. **Copy the spec in verbatim** and re-verify the hash on the copy.
4. **Hold everything else constant**: same API port, same QA database, same
   browser, same workers/reporter. The ONLY variable is which frontend serves the
   UI port.
5. **Run both sides** and keep both raw outputs.
6. **Report the pair**, never one half: `candidate 4 passed` / `base 4 failed`.

Measured 2026-09-30 (MF2D M1-01, Next dev server, Playwright):

| Side | Tree | Result |
|---|---|---|
| candidate | correction worktree (patched) | **4 passed (6.7 s)** |
| base control | detached worktree at the same base (unpatched) | **4 failed** |

The base control failed for the right reason — the CTA selector never hydrated,
so `waitForHydration` timed out at the *selector*, not on an unrelated error. Always
read the failure text: a base control that goes red for an unrelated reason
(port collision, missing dep) proves nothing.

## Why not let the worker self-probe by mutating its own file

The observed worker did attempt a revert probe, but by *temporarily patching its own
allowlisted source back to the base block*, running the spec, then restoring and
re-verifying the sha. It worked (`REVERT_PW_RC=1`) but it:

- mutates the very artifact under test while the evidence is being collected;
- makes the proof depend on the mutation being byte-restored afterwards;
- can contaminate a git-tracked file (the observed run dirtied
  `test-results/.last-run.json` this way and had to restore it).

The separate-worktree control has none of those properties. Use it as the primary
proof; a self-probe is corroboration at best.

## Decide the shape BEFORE measuring

Write down, before running anything: *"hypothesis: spec FAILS on pre-patch UI and
PASSES on patched UI; only the serving tree varies."* A control run after you
already know the answer invites you to explain away an unexpected result.

## Hazard: a disposable verifier worktree can destroy a SHARED dependency chain

`node_modules` is commonly shared across trees as a Windows **junction**
(`powershell New-Item -ItemType Junction`) to avoid reinstalling. If the junction
lives *inside* the disposable worktree, removing that worktree **deletes the
junction**, and anything chaining through it breaks.

Measured 2026-09-30: `C25/frontend/node_modules` was a junction →
`MF-END-24/frontend/node_modules` (the real 297-package tree). A verifier worktree
was given its own junction to the *same* MF-END-24 tree. Removing the verifier
worktree with `git worktree remove --force` left an orphan junction directory, and
the shared target had to be re-created for the other consumers.

Rules that came out of it:

1. **Remove the junction BEFORE removing the worktree.** `cmd /c rmdir <junction>`
   can silently no-op (it printed the shell banner and nothing else); Python
   `shutil.rmtree(<junction_path>)` actually removed it. Verify with
   `os.path.exists()` afterwards, and `find <dir>` should list nothing.
2. **After any worktree removal, re-verify every consumer of the shared tree** —
   count the packages and read a known version back:
   `ls <shared>/node_modules | wc -l` and
   `python -c "import json;print(json.load(open('<shared>/node_modules/next/package.json'))['version'])"`.
   Report the number, not an assurance.
3. **Prefer a real `node_modules` for graphs with a chain of junctions** — for
   example repoint the source tree at an already-installed sibling, run the
   control, then restore. Fewer links, fewer ways to break a neighbour.
4. The disposable tree's own `test-results/` after a control run is a **stray
   artifact** — remove it with the tree.

## Same-family disclosure: `porcelain` says modified, the blob says otherwise

`git status --porcelain` can list a tracked file as modified while its content is
byte-identical to HEAD, purely because of the CRLF/LF worktree attribute. Do NOT
call this an out-of-allowlist violation and do NOT revert it. Diagnose exactly:

```bash
git hash-object <path>            # blob of the worktree bytes
git rev-parse HEAD:<path>         # blob of the committed version
```

Equal blobs ⇒ the worktree copy differs only in line endings. Disclose it as
"shows modified in porcelain, blob equals HEAD (`<sha>`) — line-ending artifact,
not a content change" and keep the scope verdict clean. Measured case: a Playwright
run rewrote `.last-run.json` with identical content; the blob comparison settled it
in one command.

## Reporting shape

State, in the review artifact: the spec sha used on both sides, the two trees (with
base sha and branch/detach state), the two verdicts, the raw output files, and the
one-line reason the base control failed. Add a row for it in the AC matrix under
the AC it defends, marked as a **Manager-run** measurement so a reviewer can
distinguish it from anything the writer claimed.
