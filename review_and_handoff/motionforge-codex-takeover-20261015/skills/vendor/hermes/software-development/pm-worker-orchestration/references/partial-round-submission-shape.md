# Shipping a correction round that is allowed to fail

Measured 2026-10-01 (MotionForge M1-01). The correction round produced **zero product
bytes** and still had to be a *reviewable* submission. What made that possible is a
submission shape worth reusing whenever a round ends short.

## 1. Lead with the terminal cause, in the first three lines

Do not bury it. The reader must know immediately whether the round produced work or not:

```markdown
**Headline: the one permitted correction was dispatched, ran 2 m 30 s, and ended on the
recurring output-truncation terminal with ZERO code/evidence delta. Per the stop rule
(two identical signatures, no delta) the round stops here and submits PARTIAL. No second
correction was opened.**
```

Then a small table with the exact facts a reviewer will re-derive: task/session ids,
provider+model+`fallback`, packet path + sha256 + bytes, launch/end UTC, wall clock,
`exit_code`, `timed_out`, message/tool-call counts.

## 2. Show the stop rule was APPLIED, with the measurement that triggered it

A reviewer's first question about a PARTIAL is "did you stop for a real reason, or did you
give up?" Answer it with numbers, not prose:

| Measurement | Value |
|---|---|
| pre-patch bytes (frozen) | 4/4 hash match to the reviewer's own declaration |
| bytes after the worker exited | **identical — delta_files = 0** |
| error signature | `finish_reason='length'` ×5 → truncated args ×4 → refuse-incomplete → terminal |
| same signature in the previous round? | **yes** |
| quota/transport markers | `0` × `503`, `0` × `502`, `0` × `UsageLimit` |

State the rule verbatim (*"two identical failures with no code/evidence delta → stop"*) and
note explicitly that the budget was **not** exhausted — that is what separates this from a
budget stop, and it preempts a reviewer assuming the wrong cause.

## 3. Grade every acceptance row NOT_RUN, never PASS-by-omission

| Row | Verdict | Note |
|---|---|---|
| product rows | **NOT_RUN** | "no product byte was produced; reporting them as anything else would be a fabricated PASS" |
| operational row | **PASS** | with the enforced-vs-observed statement |
| sealing row | **PARTIAL** | real hashes + one deterministic manifest; no commit exists, by construction |

The sentence *"no byte was produced this round"* belongs next to the NOT_RUN block. It is
the whole justification.

## 4. Corrections to a PRIOR packet go in the new report, additively

When the reviewer flags misstatements in an earlier submission, do **not** edit the earlier
files. Add a short table to the new report: *prior claim → truth → where it was measured*.
Two real examples:

- prose said `18/18 PASS` and `16 files`, while the raw artifacts said **19 PASS / 0 fail**
  and **17 manifest entries** (the gate was right; the prose summary of it was wrong);
- `"Manager 0 usage"` was **false** — the exact-session log recorded `api_calls=61/300` and
  `9/16` in the same window.

Then say plainly that the prior files are **untouched**. This preserves the audit trail and
is far cheaper than a dedicated documentation round (which the reviewer will refuse).

## 5. Verify the isolation story, not just the product story

A PARTIAL still has to prove it changed nothing it was not allowed to change:

- candidate HEAD + branch unchanged; all four frozen files byte-identical to the backup;
- INTEGRATION porcelain `0` at the expected HEAD;
- the other protected worktrees at their as-found dirty counts;
- **no commit created**;
- every owned process stopped, with the pid + create_time + exe triple-check;
- ports released;
- the QA runtime root left in place but holding **no listener**.

Also record the one thing that made the QA real: the runtime's `frontend/` was a **junction
to the worktree**, so the UI served the code under edit rather than a stale copy. Say so —
otherwise a reviewer cannot tell whether the browser tests exercised the candidate.

## 6. End with the decision the reviewer must make, not a request to re-run

The round cannot fix itself if the cause is structural. Close by naming the actual blocker
and the options, so the next step is a decision rather than another attempt:

> The blocker is **not** budget: the model truncates a monolithic large `write_file` and the
> runtime then correctly refuses the incomplete arguments. Candidate remedies all live
> **outside** this task's write-set — authorise bounded multi-part writes, or raise the
> effective per-response output ceiling. Without one of those, a third attempt repeats the
> same terminal. The four files are frozen and verified, so nothing was lost.

That last clause matters: state explicitly that **nothing was lost**, so the reviewer is
choosing a mechanism, not assessing damage.
