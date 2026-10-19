# Proving a regression test actually catches the defect (base control) — verified 2026-09-30

A packet commonly demands a test worth something: *"the new E2E must catch the
missing CTA/caller or a wrong selected ID — static-only is not enough."* A test that
passes on the candidate proves **nothing** about that claim. The only measurement
that does is a **base control**: run the *same* test bytes against a **pre-patch
tree at the same base** and show it goes RED.

## The technique

1. **Freeze the spec first.** Record its sha256. Every side must use byte-identical
   test code, or you are comparing two different tests.
2. **Make a disposable worktree detached at the task's BASE commit** (not a branch
   tip, not the candidate): `git worktree add --detach <CTRL_DIR> <base-sha>`.
3. **Copy the spec in verbatim**, then re-verify the hash on the copy.
4. **Hold everything else constant** — same API port, same QA database, same
   browser, same reporter/workers. The ONLY variable is which frontend serves the
   UI port.
5. **Run both sides** and keep both raw outputs.
6. **Report the pair**, never one half: `candidate 4 passed` / `base 4 failed`.

Measured 2026-09-30 (MF2D M1-01, Next 16.2.12 dev server, Playwright):

| Side | Tree | Result |
|---|---|---|
| candidate | correction worktree (patched) | **4 passed (6.7 s)** |
| base control | detached worktree at the same base (unpatched) | **4 failed** |

Read the failure text — the base control must go red for the *right* reason. Here
the CTA selector never hydrated (`waitForHydration` timeout at the selector). A base
control that fails on a port collision or a missing dep proves nothing.

## Why not let the worker self-probe by mutating its own file

The observed worker did attempt a revert probe, but by *temporarily patching its own
allowlisted source back to the base block*, running the spec, then restoring and
re-verifying the sha. It worked (`REVERT_PW_RC=1`) but it:

- mutates the very artifact under test while evidence is being collected;
- makes the proof depend on a byte-exact restore afterwards;
- can dirty a git-tracked file (the observed run polluted a tracked
  `test-results/.last-run.json` and had to restore it).

The separate-worktree control has none of those properties. Use it as the primary
proof; a self-probe is corroboration at best.

## Decide the shape BEFORE measuring

Write down, before running anything: *"hypothesis: spec FAILS on the pre-patch UI and
PASSES on the patched UI; only the serving tree varies."* A control run after you
already know the answer invites you to explain away an unexpected result.

## Hazard: removing a disposable worktree can destroy a SHARED dependency chain

`node_modules` is commonly shared across trees as a Windows **junction**
(`powershell New-Item -ItemType Junction`) to avoid reinstalling. When that junction
sits *inside* the disposable worktree, removing the worktree **deletes the junction**,
and every consumer chaining through it breaks.

Measured 2026-09-30: `C25/frontend/node_modules` was a junction →
`MF-END-24/frontend/node_modules` (the real 297-package tree). A verifier worktree was
given its own junction to the *same* target. `git worktree remove --force` on the
verifier left an orphan junction behind instead of cleaning up, and the shared target
had to be re-created for the other consumers.

Rules:

1. **Remove the junction BEFORE removing the worktree.** `cmd /c rmdir <junction>` can
   silently no-op (it printed just the shell banner); Python `shutil.rmtree(<junction>)`
   actually removed it. Verify with `os.path.exists()` afterwards, and `find <dir>`
   should list nothing.
2. **After any worktree removal, re-verify every consumer of the shared tree** —
   count packages and read a known version back:
   `ls <shared>/node_modules | wc -l` and
   `python -c "import json;print(json.load(open('<shared>/node_modules/next/package.json'))['version'])"`.
   Report the number, not an assurance.
3. **Prefer a real `node_modules` for graphs with a chain of junctions** — repoint the
   source tree at an already-installed sibling, run the control, then restore. Fewer
   links, fewer ways to break a neighbour.
4. The disposable tree's `test-results/` after a control run is a **stray artifact** —
   remove it with the tree.

See also the junction/Turbopack pitfall in SKILL.md: a junction serves `next dev`
fine but `npm run build` (Turbopack) panics with *"Symlink [project]/node_modules is
invalid, it points out of the filesystem root"* — `next build --webpack` succeeds.
Disclose this as a harness artifact, not a product defect.

## Same-family disclosure: `porcelain` says modified, the blob says otherwise

`git status --porcelain` can list a tracked file as modified while its content is
byte-identical to HEAD, purely from the CRLF/LF worktree attribute. Do NOT call this
an out-of-allowlist violation, and do NOT revert it. Diagnose exactly:

```bash
git hash-object <path>            # blob of the worktree bytes
git rev-parse HEAD:<path>         # blob of the committed version
```

Equal blobs ⇒ the worktree copy differs only in line endings. Disclose it as "shows
modified in porcelain, blob equals HEAD (`<sha>`) — line-ending artifact, not a content
change" and keep the scope verdict clean. Measured case: a Playwright run rewrote
`.last-run.json` with identical content; the blob comparison settled it in one command.

## A green gate on a WERKSPACE with no commit is not a candidate

The observed writer exited `exit=0` after the browser phase having produced real code
but **no commit** and no REPORT/AC_MATRIX/DIFF. Treat the on-disk bytes as the frozen
candidate (hash them, back them up byte-for-byte) and say plainly in the submission
that the candidate is **uncommitted**, rather than letting a reviewer discover it.

## Reporting shape

In the review artifact state: the spec sha used on both sides, both trees (base sha +
branch/detach state), both verdicts, the raw output files, and the one-line reason the
base control failed. Add a row under the AC it defends, marked as a **Manager-run**
measurement, so a reviewer can distinguish it from anything the writer claimed.
