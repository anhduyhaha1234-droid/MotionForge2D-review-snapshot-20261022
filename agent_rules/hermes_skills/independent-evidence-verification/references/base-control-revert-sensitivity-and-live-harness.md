# Base control for revert sensitivity, and a live-code isolation harness

Measured 2026-09-30 (MF2D MF-END-10/M1-01). Covers two independent techniques that
decide whether a UI slice is actually proven.

## 1. "The new E2E test passes" is not proof the test can fail

A packet can require: *"the new browser test must catch a missing CTA / wrong selected
ID when the patch is reverted; static-only tests are not enough."* A passing run
proves nothing about that. You need a **base control**: the same test against the
un-patched code.

How to run it so nothing is mutated and nothing is faked:

1. Create a **disposable verifier worktree** at the same base commit
   (`git worktree add --detach <path> <base>`). Do NOT temporarily revert your own
   allowlisted file to simulate the revert — that edits the artifact under test and
   makes the evidence self-referential.
2. Give the verifier worktree the **same dependency tree** the candidate uses
   (on Windows: a `node_modules` junction to the already-installed tree — no
   `npm install`).
3. Copy the spec file **byte-for-byte** and record its sha on both sides. The
   identical sha is what makes the pair a proof: the only variable left is *which
   frontend is serving*.
4. Hold the API + DB constant and swap only the UI process on the same port.
5. Require **candidate = pass AND base = fail**. Measured: `4 passed (6.7s)` vs
   `4 failed` (the CTA selector never hydrates because the button does not exist).
6. Remove the verifier worktree afterwards and confirm `git worktree list` shows it
   is gone, and that the shared dependency tree is still intact (count the packages
   before and after).

A writer attempting this itself will often do it by mutating its own file
(`REVERT_PW_RC=1` in its log) — accept that as supporting evidence, but run the
clean worktree version yourself; it is the one a reviewer can re-derive.

### Cleanup trap on Windows

`git worktree remove --force <path>` can leave a stub directory containing only the
junction. `rmdir` on the junction does not always complete from a shell wrapper, and
the leftover reads as "worktree still present" in your own final gate. Verify with an
explicit `find <path>` (expect 0 entries) and remove the stub, then re-check.

Before removing *any* worktree, confirm which directories are junctions and where
they point: a chain (`tree A/frontend/node_modules → tree B/frontend/node_modules`)
means removing A is safe only while B exists. Count packages in the target before and
after (measured: 297 → 297, Next 16.2.12 intact).

## 2. A runtime harness must not copy the code it is testing

First attempt: the harness copied all tracked `frontend/` files into the runtime root
and ran the dev server there. It worked — and was **wrong**: any edit made afterwards
would be served from the stale copy, so the browser proof would silently exercise the
baseline. The failure surfaced as a confusing `500` (`Module not found: Can't resolve
'@/lib/api'`) that had nothing to do with the code under test.

Correct shape:

- The runtime root holds **only isolated state**: fresh DB, `artifacts/`, `output/`.
- The servers run with `cwd` **inside the correction worktree**, so a dev-server edit
  is live.
- The worktree stays porcelain-clean because `.next/` is git-ignored — verify with
  `git status --porcelain` after starting the server.
- Ports are pinned per-run (e.g. API 8071 / UI 3071) and probed free before start,
  never the user's dev port.
- Each pid is recorded with `(pid, create_time, exec_path)`; stop verifies all three
  and terminates leaf-first, then re-probe the ports to prove they are free.

Two more measured traps while building this:

- **`npx` / `npm` are shell scripts on Windows**; `CreateProcess` cannot spawn them
  (`WinError 2`). Call the JS entry directly
  (`node <node_modules>/next/dist/bin/next dev ...`) or go through a shell.
- **Turbopack panics on a junctioned `node_modules`**:
  `Symlink [project]/node_modules is invalid, it points out of the filesystem root`.
  webpack (`next build --webpack`) builds the same tree fine. Report this as a
  harness artifact with the workaround and let the reviewer rule on it — do not
  "fix" it by installing dependencies into the worktree.

### Fail-closed before dispatch

Prove the harness end-to-end with a **manager-owned probe** before handing it to a
worker: create a throwaway record through the real API (expect 201), then a duplicate
(expect 409), then an invalid field (expect 422), then delete the DB and re-probe that
`total == 0`. Only then is "empty library" a precondition you can assert.
