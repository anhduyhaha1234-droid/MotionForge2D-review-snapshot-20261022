# Proving a worker's "nothing changed" claim — and the traps in manifest comparison

Two verification patterns, both from a wave where a worker claimed a zero-byte append and a freeze check
reported total corruption that did not exist.

## 1. Manifest / hash-set comparison: a blanket result is a BUG SIGNAL, not a finding

An independent re-verification of 4 freeze manifests reported **194/194 corrupted** while every file was
intact. Two trivial comparison bugs, either of which alone produces a uniform verdict:

- **wrong column.** The manifest stored the digest of the **frozen copy** in one field (`frozen`) while the
  original path sat in another (`src`). Hashing `src` answers a different question than the manifest asked.
- **case mismatch.** The manifest stored **UPPERCASE** hex; `hexdigest()` returns lowercase, so
  `got != want` was true for every row regardless of content.

**Protocol before declaring any integrity failure:**
1. print the manifest's own schema and **one full sample entry**;
2. compare `hashlib.<algo>(path.read_bytes()).hexdigest().lower()` against `want.strip().lower()`;
3. confirm you are hashing **the same artifact the manifest hashed** (frozen vs source path);
4. cross-check the manifest's **own recorded counters** (`hash_mismatch`, `file_count`, `bytes_total`).

Interpretation rule: **100 % failure or 0 % failure on a heterogeneous set is far more likely a bug in the
check than a mass event.** Stop and inspect the check.

## 2. "The run appended 0 bytes" — make the worker's own sentinel independent

A lane claimed its run appended **0 bytes** to a previously submitted evidence ledger kept in a different
root. The claim is checkable without trusting anyone:

- read the protected ledger **before** the run and **after** it;
- assert **bytes, row count, and sha256 are all unchanged** — a byte-equal-but-reordered file is not
  "unchanged", and a same-size rewrite is not either;
- assert the **prefix** the reviewer owns still hashes to its recorded digest (a frozen prefix digest
  catches the case where only the tail moved);
- report the delta explicitly (`+0 bytes`, before/after hash) rather than a prose "unchanged".

Also verify the *mechanism* the worker claims, not just the outcome: read the code path that resolves the
ledger location, and check that the fallback **fails closed** when the resolved path lands inside a
submitted evidence root. An outcome that happens to hold is weaker than a mechanism that cannot leak.

**Corollary — do not let an independent evaluator write into a submitted packet.** Any evaluator run must
address its own scratch/temp root; a submitted packet's bytes stay byte-identical, and the reviewer's own
appended rows stay **attributed**, never truncated or concealed.

## 3. Re-run the decisive command yourself, on the exact reviewed commit

Worker reports are self-reports. For each claim, re-run one command that would fail if the claim were
false, on the frozen/committed bytes:

- a suite green claim → run the suite, capture pass/skip counts;
- a lint-clean claim → run the linter **on the changed files only**, and separate **pre-existing**
  findings (disclose them, do not silently fix files outside the write-set);
- a build-fix claim → run the build yourself on the committed tree;
- a "counterexample now refuses" claim → read the recorded before/after JSON for the **same** case and
  compare the decisive field (e.g. staged-artifact count, submit count, typed error code), not the prose.

When a claim is not reproducible, say exactly which quantity failed to reproduce and either have it
re-stated reproducibly or drop it — never restate an unreproducible number as if it were verifiable.
One case: a canonical digest that "did not reproduce" turned out to be reproducible once the
canonicalisation's `ensure_ascii` setting (non-ASCII characters present) was named; the fix is documenting
the exact canonicalisation, not deleting the number.

## 4. Negative controls must be able to fail

A green suite proves nothing unless a control demonstrates the assertion fires on broken input. Require,
per fixed row, a recorded **pre-fix RED** (the same check run against the preimage) or an injected
mutation that makes it FAIL, plus a **positive** control (an independent, legitimately-new case still
passes). Report a control as non-vacuous only when it actually returned FAIL on the broken input —
`UNMEASURED` does not count as a control firing.
