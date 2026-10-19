# Evaluator output integrity — the summary string, and the packet's own honesty gate

Measured 2026-09-23, closing a wave where a manager graded a frozen GPU candidate and then had to
write the review packet. Two independent lessons, both about **the output of your own verification
machinery** rather than about the worker.

---

## 1. An aggregate verdict string can contradict the row map it summarises

The evaluator's harness printed, at the end of a clean run:

```
TECHNICAL=TECHNICAL_FAIL
```

Its own row map in the same run was:

```
8 PASS / 2 UNMEASURED / 0 FAIL
```

Nothing was broken. The harness's aggregation rule was:

```python
all(v in ("PASS", "NOT_APPLICABLE") for v in rows.values())
```

`UNMEASURED` is deliberately **not** in that set, so a run with **zero** failures still stamps
`TECHNICAL_FAIL`. The row that had genuinely failed on the previous candidate (a geometry check,
640×368 vs 640×360) had flipped to **PASS**, and a re-encode control proved the row still had teeth.

### Why this is dangerous in both directions

- **Laundering it**: silently dropping the string and reporting "all green" hides a real signal
  (there *are* rows the harness could not measure).
- **Passing it through**: a reviewer greps `TECHNICAL_FAIL` and reads a failed pipeline where there
  were zero failed checks — or worse, a manager marks a row FAIL that is actually `UNMEASURED`.

### Rule

When an evaluator's **aggregate** disagrees with its **row map**, treat the aggregate as a
**vocabulary artefact** until you have read the aggregation rule in the harness source. Then:

1. **Read the rule**, quote it, and state the count it produces (`UNMEASURED ∉ {PASS,
   NOT_APPLICABLE}` → true total `8/2/0`).
2. **Report both**: the raw string *and* the true row counts, plus the rule that explains the
   difference. Put the explanation next to the string, not three sections away.
3. **Never translate `UNMEASURED` into PASS or FAIL.** It gets its own row disposition, with the
   reason and the positive control that showed the measure had no discriminating power on this
   window (a "flat" distance curve also fails on a source-vs-its-own-cut pair, so the test cannot
   tell alignment from misalignment — the honest answer is *not measured*).
4. **Check the row actually has teeth** before believing a flip: here re-encoding at the old height
   made the geometry row fail again on demand. A row that cannot fail proves nothing when it passes.
5. Record the artefact in the packet as a **disclosed limit** so the next reader does not re-derive
   it — and so nobody "fixes" the harness mid-review and changes the numbers.

Generalisation: any tool that emits a single status word (`TECHNICAL_FAIL`, `FAILED`, `NOT_OK`,
`DEGRADED`) computed over a heterogeneous bag of dispositions deserves the same treatment — find the
predicate, then quote the predicate.

---

## 2. Encode the packet's honesty invariants as machine checks, and re-run them after every edit

A review packet makes claims **about itself**: "no self-approval anywhere", "these rows are
unmeasured", "the frozen bytes are intact", "nothing was pushed". Prose cannot be trusted to keep
those true across a session of edits — three times in one run an edit to a management document broke
a different invariant than the one the editor was thinking about:

- a fuzzy patch inserted a paragraph **into the middle of a markdown table**, orphaning a row and
  leaving a blank line where a table row should be;
- a document was written without the run-state line, so it read as if no
  `NOT_APPROVED / NOT_CLOSED` claim applied to it;
- a lane's HEAD moved (a worker committed) after the gate had been written, so the gate's expected
  commit was stale.

### Rule

Write one **final-gate script** that reads the packet from disk and asserts the invariants, run it as
the last act before delivery — and **re-run it after every subsequent edit to any deliverable**. Its
checks, in the shape that worked:

| Group | Check |
|---|---|
| Deliverables | each required document exists and is above a minimum size (a 300-byte "report" is a stub) |
| Freeze | manifest `hash_mismatch == 0`; every listed file present **and** re-hashed from disk; the candidate clip's sha and byte count match the recorded values |
| Protected packet | a *submitted* evidence packet's ledger prefix still matches its recorded hash, and its extra rows are still present (attributed, never truncated) |
| Git | per tree: `HEAD == expected`, parent object still reachable, `git branch -r --contains HEAD` **empty**; main branch HEAD unchanged |
| Machine | no engine port accepting connections; GPU near idle |
| **Honesty — absence** | no self-approval token in any deliverable (`QUALITY_ACCEPTED = 1`, `STATUS: APPROVED`, `STATUS: CLOSED`, `APPROVED_BY_MANAGER`) |
| **Honesty — presence** | where a document claims a run state it must name `NOT_APPROVED`/`NOT_CLOSED` or `QUALITY_ACCEPTED = 0`; the evaluation document must contain `UNMEASURED` and `NOT_VISUALLY_APPROVED` and must not present a cost-per-accepted-unit number when accepted units are 0 |
| **Document integrity** | no corrupted table row (`"\n||" not in text`); every lane/row the table is supposed to carry is still greppable |
| Registry | the session registry genuinely carries its provenance grades and the never-resume ban |

Exit non-zero on any failure and write the transcript into the packet, so the gate's own result is
reviewable. Two of the checks above caught **real defects in the manager's own documents** during
this run (the missing run-state line, and the orphaned table row) — which is the whole point: the
gate exists to catch the author, not the workers.

### Pitfall: the gate can go stale mid-session

A gate that pins `HEAD == <sha>` breaks the moment a still-live lane commits. That is a **gate
maintenance** signal, not a task failure: update the expected value to the new verified commit (and
its parent), confirm the parent is the value you pinned before, then re-run. Do the same whenever a
document is edited after a gate run — never deliver a `STEP5_GATE.txt` that predates your last edit.

### Pitfall: probing a script that has no `--help`

A gate/verification script written with bare `sys.argv` indexing **executes on invocation** — calling
it with `--help` raises `IndexError` instead of printing usage, which looks like a broken tool. Read
the source for its usage line first, or add `argparse`. See also
`manager-progress-reporting` pitfalls ("probing a mutating script with `--help`").

---

## 3. Cost accounting that survives review

- Report **generated** and **accepted** units separately. If accepted = 0, write *cost per accepted
  unit is undefined* — never divide wall time by the produced length and call the quotient throughput.
- Keep **wait**, **wall** and **server** times as three labels; they differed here
  (client wait 163.7 s, wall 164.7 s, server `Prompt executed in 162.1 s`), and quoting the wrong one
  is how a correct measurement gets retracted.
- A single-sample extrapolation to a long target is an **estimate marked as such**, in its own row,
  never promoted into the results table.
