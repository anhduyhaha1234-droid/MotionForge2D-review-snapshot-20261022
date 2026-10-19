# Re-running a reviewer's probe, and disclosing interface deltas

Measured 2026-09-24 while verifying two correction lanes (adapter + schema contract) against a
reviewer's published probe JSONs. These are the mechanics that turn "the worker says it is fixed"
into evidence a reviewer can re-derive.

## Never run a reviewer's probe from the reviewer's evidence root

Reviewer probes commonly write their output next to themselves (`OUT = Path(__file__).resolve().parent`)
and reuse a fixed scratch root. Run verbatim, they **overwrite the review's own evidence** — which
destroys the "before" half of the comparison.

Pattern that works:

1. Copy the probe into **your own** scratch and rewrite ONLY (a) the scratch root and (b) the output
   filename; assert the rewrite landed (`assert "<my_scratch_marker>" in text`) and that the target
   tree path is untouched.
2. Use a **short Windows-native temp root** for that scratch (`C:/Users/<u>/AppData/Local/Temp/<tag>`).
   A deep evidence path plus a generated reservation filename blows past MAX_PATH (260) and dies with
   a confusing `FileNotFoundError` partway through the case list — after some cases already passed,
   which makes it look like a case-specific defect. (See terminal-engineering-discipline #44.)
3. Never edit the reviewer's file, and never "tidy" the reviewer's output afterwards.

## Prove the probe ran against the bytes you think it did

- A probe that reports `source_sha256` / `adapter_sha256` is self-documenting: recompute that digest
  yourself from disk and require equality **before** reading any case result. Measured: the probe
  reported `925f911704…` and an independent `hashlib.sha256(open(path,'rb').read())` matched → the run
  really exercised the fixed bytes, not a stale copy.
- Cross-check the worker's JSON against the reviewer's published JSON **field-for-field** on the
  decisive keys (`status/error/submit_calls/receipts/staged`). "worker `probe_before` ≡ reviewer
  published 9/9" and "worker `probe_after` ≡ my independent run 9/9" are re-derivable claims; "the
  worker says it passes" is not.

## Wrap each case so one refusal cannot hide the rest

A probe written as a straight-line script aborts at the first `raise`. For a correction whose *expected*
outcome IS a typed refusal, that leaves you with evidence for one case and nothing for the others.

Encode every case as `{outcome: RETURNED|RAISED, type, code, message, value}` in try/except and write
the whole matrix. A table of typed refusals (`MF_..._CORRUPT_RESERVATION`, `MediaEngineRefusal`,
`ValidationError`) plus the preserved positive controls IS the evidence.

## A correction that removes a caller-supplied parameter breaks the reviewer's repro — disclose it

Deleting a parameter can BE the fix. Measured: `resolve_replay(reservation, *, requester_session,
identity_matches)` → `resolve_replay(reservation, *, proof: BackendIdentityProof)`. The finding was
"the caller's boolean must not be the authority", so removing that boolean is the correction; the
reviewer's one-line repro then raises `TypeError`, which reads like a regression unless you say so.

Do both halves:

1. **Verify the intent with the new API.** Foreign identity → refuse
   (`reservation_owned_by_other_session`); the **true owner** → still re-attaches (positive control);
   a hand-forged integrity digest → refused as `identity_proof_integrity_failed`. A correction that
   refuses *everything* is not a fix — the two-sided proof is what closes the row.
2. **Disclose the delta in the verification doc**: old signature, new signature, the fixture/helper
   that builds the new argument (with file:line), and the reason the old shape is gone. Never leave
   the reviewer to discover the `TypeError` alone.

## Re-anchor the suite after the last edit, not before

A pass count measured before the final hunk is not the final number. When a worker reports
"N passed" and its own log shows a later edit, re-run the affected module yourself at the frozen
HEAD and quote both (worker's number, your number) — they must agree. Same for a module digest the
worker quotes (`ee5e60a3…`): recompute it.

## When your re-run's stdout digest differs, name the volatile field — never waive it

Re-executing a recorded fixture is only a stability check if you interpret a difference correctly.
Measured: 4 recorded `argv` cases re-run verbatim → **rc 4/4 and verdict 4/4 identical**, but **one
stdout sha256 differed**. The payload embedded *live process state* (`manager_pids`,
`survivor_pids_rechecked`, `alive: true`) which changes between runs by design.

Rules:

1. **rc + verdict are the deciding fields**; the stdout digest is a stability signal, not the verdict.
2. When the digest differs, grep the payload for time/pid/live-state keys and report the delta as
   **EXPLAINED with the field named** ("embeds live process state, not fixture data"). Neither
   silently waive it nor grade it as a failure — both hide information a reviewer needs.
3. A digest mismatch on **every** case is a bug in *your* comparison (encoding, newline
   normalisation, hashing the wrong stream), not a finding — suspect the harness before the code.
4. Where the fixture is synthetic, say so in the same table (`engine_started=false`,
   `pid_stopped=false`) so nobody reads a fixture result as a real end-state proof.

## Prove a gate fires BEFORE its side effects (dry runs in each pin state)

When the claim is "this guard blocks bad input early", do not read the code path and agree — run the
guarded entry point once per pin state and **count what it wrote**:

| state | expected | measured (chain driver, 2026-09-24) |
|---|---|---|
| pins absent | gated skip | exit `0`, nothing attempted |
| pin present, wrong SHA | refusal | exit `1`, **4 directories / 0 files** created |
| pin present, integration SHA | proceeds / typed block | exit `1`, still no DB, no managed root, no rows |

The measured filesystem effect (dirs-but-no-files, no `<db>.db`, no managed root) is the evidence that
the assertion runs **before** the migration / first HTTP call. A gate description alone is a design
intention; the side-effect count is the verified ordering. Make the harness report that count itself,
so a later reviewer re-derives it without trusting prose.

## See also

* `references/media-fidelity-and-metadata-verification.md` — media artifacts: pixel equality is not
  fidelity (probe the container tags too), the 4-file tag matrix with a stripped negative control,
  and why a freeze must be pinned by digest rather than mtime.
