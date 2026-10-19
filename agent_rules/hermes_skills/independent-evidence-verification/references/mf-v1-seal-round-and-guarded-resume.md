# Seal round, hash-only manifests, and a manager's own false finding (2026-09-22)

Session context: correction wave `mf-reskin-correction-20260922/20260922T0955Z`, three disjoint CPU lanes
(COMFY F01–F05, VIDEO14B F06–F09, BENCH F10) after an independent review returned
`CHANGES_REQUESTED`. This file records three things §28 draws on, all manager-side.

---

## 1. The commit-only seal round (BENCH c2)

**Situation.** The BENCH c1 round came back `TASK_SUBMITTED` with the F10 ledger-durability fix verified
but **uncommitted**, because the packet granted no git authority. The Manager's own verification was:

| Check | Result |
|---|---|
| suite re-run in the lane worktree | `pytest test_bench_harness.py -q` → **11 passed, 0.91 s** |
| files changed vs preimage | exactly 3 of 13, **all grew**: `common.py` 141→329 L, `run_dryrun.py` 591→598 L, `test_bench_harness.py` 169→349 L |
| pre-fix control | `raw/pytest_pre_fix.txt` → `3 failed, 1 passed, 7 deselected, 4 errors` |
| protected set verify | **VERIFIED, 0 failures, 40 files** |
| lane's final gate | **35/35 GATE_PASS** (on disk, not a claim) |

**Packet shape that worked** (`MF-V1-BENCH-c2-commit-seal.md`, ~15-call budget):

1. `RULES_LOADED` + `PREFLIGHT_OK`; HEAD must still be `a2ff225…` and porcelain must show **exactly**
   the three paths — otherwise stop, do not commit an unknown diff.
2. Re-confirm the three content hashes; stop if any moved.
3. Commit **only** those explicit paths; `git add -A`/`git add .` explicitly forbidden.
4. Prove: `git show --stat` (3 files), `git rev-parse HEAD` **and** `HEAD^`, porcelain empty,
   `git branch -r --contains HEAD` empty.
5. Append one line (the SHA) to `NEW/BENCH/REPORT.md`; do not restructure it.

**Manager verification of the seal:**

```
HEAD  663199b79e34d8c582c2cc8bcba29b4581bec20a  bench(F10): ledger-durability correction …
HEAD^ a2ff22562bd362707d1cbb493d196a06ad8f7825  (declared parent, intact)
3 files changed, 425 insertions(+), 50 deletions(-)
porcelain: 0      branch -r --contains HEAD: (empty)
git show HEAD:<path> | sha256sum  →  340ebc24… / 0936b9a6… / 96a358e0…   (3/3 == reported)
```

**Trap in the same round:** the commit printed

```
fatal: bad object refs/codex/turn-diffs/.../base
failed to perform geometric repack
```

…and still succeeded. Those are a **pre-existing dangling ref from the Codex CLI**, not a failed commit.
Assert the invariants (`rev-parse HEAD`/`HEAD^`, `show --stat`) rather than reading git's message.

---

## 2. Hash-only manifest vs the ledger loss

Wave 2's Manager snapshot of the BENCH evidence tree was written as a **hash manifest**:

| Fact | Value |
|---|---|
| file | `manager/guard/wave2/bench-evidence-pre.json` |
| entry for `raw/cmd_transcript.jsonl` | bytes 149,831, sha `D2CEBE0A2E93AD81149A…` |
| byte copies kept | **none** |

The lane then reopened that ledger with mode `"w"` (`common.flush_ledger()`), truncating **306 rows → 20**.
Nothing could restore it: not git (the file is in an evidence root, not the repo), not the Manager's
manifest, not the reviewer's copies. The ledger is recorded `OPEN_WITH_ACCEPTED_LOSS` with the preimage
facts preserved and an explicit statement that it is **not** reconstructed.

Contrast: the *byte* snapshots taken in the same wave did work — COMFY pre-write 22 files, VIDEO14B
untracked 61 files, BENCH 13, all `snapshot_hash_mismatch: 0`, plus the 94-file wave-2 media/evidence
snapshot. Those could have been restored. The lesson is the manifest **type**, not the tooling.

What survived for the reviewer: per-step raw JSONs and `BENCH/REPORT.md` carry the measurements with their
own hashes; only the command transcript (argv/cwd/exit/duration envelopes) was lost.

---

## 3. The manager's own false duplicate count

Ad-hoc health check over the lane's NEW ledger (`BENCH/raw/cmd_transcript.jsonl`, 206 lines):

```python
ids = [r.get('row_id') or r.get('id') for r in rows]
len(ids) - len(set(ids))     # → 5    reported as "5 duplicates"
```

Re-derived by classifying rows first:

```
kinds:             {'command': 200, 'header': 6}
headers:           6  (run-level, carry 'run' + 'commands', no cmd_id, no row_id)
command rows:      200
unique cmd_id:     100
row_id duplicated: {}          # → 0
```

6 header rows have **no `row_id`**, so `None` collapsed them into one "duplicate group of 6" — the count
was an artifact of my own counting key, not a defect in the lane's fix. Had it been filed as a finding it
would have been a false negative-claim against a correct implementation, in the same wave where the lane
was already on a guarded resume for an evidence incident.

**Rule:** when your checker contradicts a worker's claim, suspect the checker; re-derive by a second
method (classify by row kind, count the intended key) before writing a finding, and retract explicitly if
you already reported it.
