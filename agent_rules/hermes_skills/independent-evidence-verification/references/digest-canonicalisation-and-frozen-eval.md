# Digest canonicalisation, single-variable proof, and frozen-candidate evaluation

Measured 2026-09-23 while verifying a GPU round (Wan-Animate-2, BOOK 4 s) and its frozen
evaluator round. Complements `references/artifact-path-and-digest-verification.md`: that file
lists "unreproducible digest" as a defect class — read this refinement **before** declaring one.

## 1. A digest that does not reproduce is usually YOUR canonicalisation choice

A worker reported a canonical graph digest `97045d0f…`. Recomputing with the obvious
`json.dumps(obj, sort_keys=True, separators=(",", ":"))` gave `d33bb57b…` — which looked like a
fabricated number. It was not: the adapter additionally passes **`ensure_ascii=False`**, and the
graph body carried **133 non-ASCII characters** (a CJK negative prompt), so the default
`ensure_ascii=True` escaped them and changed every byte after the first one.

Before writing "unreproducible", enumerate and state the candidate canonicalisations:

| Knob | Effect |
|---|---|
| `sort_keys=True` | key order |
| `separators=(",", ":")` | whitespace inside the serialised body |
| **`ensure_ascii`** | **escapes non-ASCII (`\uXXXX`) by default — differs whenever the payload has CJK/accents** |
| LF vs CRLF normalisation | line-ending class of the raw bytes |
| float formatting / trailing newline | last-byte differences |

Report the digest with the recipe that produced it. A hash without its canonicalisation is not a
reproducible claim, and "unreproducible" is itself a claim you must be able to defend.

## 2. One key name can hold two different quantities

In the same run, a record's `file_sha256` held the **LF-normalised** digest for one file and the
**raw** digest for another — same key, different measurement. When you verify or quote such a
field, say which normalisation it is, and prefer the byte-exact raw digest as the authority. This
is the same failure family as a freeze manifest whose per-file entry stores the digest of the
*frozen copy* in one field and the original path in another: hashing the other column answers a
different question and turns intact files into a 100 % "corruption" report.

## 3. Proving a single-variable round

For a "change exactly one thing" experiment, the mechanism proof is a **structural walk of both
documents**, not a claim: recursively diff the two JSON trees and enumerate differing paths. The
run's M1 round reported one changed field; the independent walk found **exactly one** path —
`<node>.inputs.pose_end_percent: 0 -> 1` — matching the native template's widget order, which the
worker had derived from the **live `/object_info` schema** rather than guessing widget positions.
Confirm the native reference value yourself; "the template says 1" is only usable if you read the
template's widget list through the schema that defines the order.

## 4. A template's multi-pass loop is not a duplicate submit

The server log showed two 6-step sampler passes and two output files, which reads like a
double submit when the packet allowed one. It was the template's normal s1+s2 loop. Resolve it
with server-side counters, not with arithmetic: **one prompt id**, `submit_calls = 1`, one
`got prompt`, and one `Prompt executed` — plus the two outputs being different shapes (single
frame vs a 2-up composite), only one of which is a candidate.

Beware the coincidence: a cross-check "4 `Prompt executed` <-> 4 stage lines" looked like a clean
1:1 and was a **2x2** (2 Animate prompts x 2 passes, plus 2 other prompts with no stage line).
Count per prompt before concluding anything about missing or extra work.

## 5. Shutdown proof needs a blocking probe

`10061 WSAECONNREFUSED` from a blocking connect is evidence a port is closed.
`10035 WSAEWOULDBLOCK` from a non-blocking socket is **not** — it only means the connect did not
finish immediately. A worker that refuses the weaker reading and re-probes blocking is doing it
right; record both values with the reason rather than keeping only the convenient one.

## 6. Evaluate only a frozen candidate, and prove the evaluator appended nothing

Sequence: writer session goes **terminal** -> freeze the subtree into a new freeze id (per-file
sha256 + real source path) -> evaluator reads **only** the frozen copy. A corrected candidate
means a **new freeze id**; never edit inside an existing freeze.

Then run the evaluator's own suite yourself and assert a protected evidence ledger is byte-stable
across that run — same `size`, `rows`, and `sha256` before and after (here: 184,680 B / 422 rows /
sha `21d5b178…`, with the original 173,959-byte prefix still `ed95c099…`). A previous round in
this project lost 306 ledger rows to a `"w"` open, so this class of fix is only credible with a
same-run zero-append sentinel, not with a passing test.

## 7. Reporting a GPU round's cost

Keep three clocks separate — **server** (`Prompt executed`), **client wait**, **wall** — and keep
`accepted seconds` explicit. With zero accepted output, **cost per accepted second is undefined**;
dividing wall time by generated duration and calling it throughput is exactly the overclaim the
gate exists to catch. Extrapolating from a single sample is labelled an estimate, never a
benchmark, and a comparator model measured on different geometry is not a like-for-like
comparison.
