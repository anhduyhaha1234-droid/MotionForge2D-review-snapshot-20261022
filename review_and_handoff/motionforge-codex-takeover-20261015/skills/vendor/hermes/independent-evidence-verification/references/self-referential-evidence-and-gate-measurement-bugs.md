# Self-referential evidence, and four gate bugs that looked like product defects

Measured 2026-09-30 (MF2D MF-END-10/M1-01 submission). One session produced **four**
red gate rows, and **all four were defects in the gate**, not in the artifact under
test. Every one of them would have been written into the review packet as a product
finding by a less suspicious operator.

## 1. An artifact that carries its own digest can never self-verify

A manifest that hashes every file under its root reports phantom `CHANGED` on every
regeneration, because the file that *holds the digest* is written after the build
that recorded it.

Concrete chain that took four iterations to unwind:

1. `manifest.sh` walks the RUN root and hashes everything, then writes
   `EVIDENCE_MANIFEST.json` — its own file is correctly excluded by name.
2. `T019_seal.txt` prints the manifest's digest for the reviewer. It is **inside**
   the root, so the next build hashes it; its content then changes again.
   → `mismatch: 1  manager/T019_seal.txt CHANGED`.
3. Fixing that by adding `T019_seal.txt` to the exclusion set, the verify step was
   redirected into `T023_manifest_verify.txt` — the **same bug, one layer down**:
   the new verify output became an unlisted file on disk.
   → `unlisted_on_disk: ["manager/T023_manifest_verify.txt"]`.
4. The review report itself quoted the manifest digest. Since the report is a
   manifested file, **any digest printed inside it is stale by construction** —
   each edit changed the digest it claimed.

**Rule.** Exclude exactly the self-referential files *by name*, with the reason
written in the builder's own comment block, and never quote a digest of a file that
is itself manifested. In the report, point at the raw verify output
(`manager/T023_manifest_verify.txt`) instead of transcribing a number that cannot
stay true.

**Determinism proof that actually works:** run the builder **twice in a row** and
require an identical `entries_digest` (a hash of the entries array, which excludes
timestamps). Then run a **read-only `verify`** as the last step. Measured clean:
`count 154, mismatch 0, unlisted 0`, identical digest across both runs.

Ready-to-copy builder: `scripts/evidence_manifest.py`.

## 2. Gate bugs that masquerade as findings

| Symptom | Real cause | Correct assertion |
|---|---|---|
| Row FAILs with an **empty** `actual` | PowerShell `(...).Count` returns *nothing* for a single object (no `.Count` on a bare `CimInstance`) | count in Python/psutil, or wrap with `@(...)` |
| `live worker` reports `actual=1` while nothing is running | the checker carried the target session id **inline in its own argv** (`python -c "... '20260928_181955_a6d89a' ..."`) and matched **itself** | read the identity from a FILE, never from the command line |
| `usage ledger rows expected=10 actual=12` | the row pinned a **literal count** for an append-only file that legitimately grew | assert the PROPERTY: `>= floor` (append-only-ness), not a frozen number |
| manifest self-check `mismatch: 2` | the two files that hold the manifest's own digest | exclude them explicitly (§1) |

Ready-to-copy probe: `scripts/self_excluding_liveness_probe.py` — excludes its own
pid and its full ancestor chain, and skips shell parents, so a self-match is
structurally impossible.

### The general rule

> When a gate row goes red on a path, file, or count **you just wrote**, print the
> RAW command output inside the row detail before believing it. A mangled path
> (`ts/…` for `tests/…`), an empty actual, or an off-by-N count is the tell that the
> gate is broken.

And: **assert the property, not the snapshot.** `porcelain == allowlist` beats
`porcelain has 5 lines`; `ledger is append-only and >= N` beats `ledger has 10 rows`;
`no unexpected drift` (with an explicit allow-list of files the gate itself writes)
beats `zero changed entries`.

## 3. Preserve the failing runs

Every red run above was kept (`T015`, `T019`, `T020`, `T021`) and the four bugs were
disclosed in the review packet's own measurement note. **Do not** delete a red gate
output after fixing a gate bug: the reviewer needs to see that the number moved
because the *instrument* was fixed, not because the artifact was edited to agree.

Corollary from the same session: after fixing a gate, re-run the whole script and
check the **summary line** (`ok=N bad=0`) — a fix that introduces a new red row one
layer down is the normal failure mode here (it happened twice).
