# Cross-lane gate×seed interaction triage (integration-owner pattern)

When an integration merge lands ZERO-CONFLICT but the combined gate goes RED,
the failure is usually a contract interaction between lanes — not a defect in
either lane alone. Route it wrong (loosen the gate, or blame the wrong owner)
and you burn a full gate cycle plus a misdirected worker turn. Triage first:

## 1. Isolate the single RED item

Record which gate items are GREEN (diff-check, each lane suite with counts)
and the one RED item with its EXACT assertion text plus actual values
(e.g. expected `blocked`, actual `status=not_run run_state=never_run` with
file:line). One RED item with everything else green = interaction, not rot.

## 2. Trace both sides of the interaction

- Which lane changed the GATE CONTRACT (new conditions the old seed never
  satisfied — e.g. "newest FULL-scope run + N coverage conditions" replacing
  a looser "latest run wins" rule)?
- Which lane's SEED/FIXTURE predates that contract (e.g. submits AUDIO scope
  that can never pass a FULL-scope gate, so readiness degrades to `not_run`)?

Read the failing test's seed lines (:line refs) and the gate function — the
mismatch is usually visible in under 10 lines on each side.

## 3. Decide gate-correct-seed-wrong vs gate-wrong

If the new gate closes a REAL loophole (a narrower scope masquerading as full
coverage, a fallback path that hides unproven state), the gate STANDS — do
NOT loosen it to make the old seed pass. The seed is wrong. Only if the gate
demands something no legitimate seed can provide is the gate wrong.

## 4. Route to the SEED owner with an exemplar, not a description

Dispatch the lane that owns the failing seed/test (never the gate owner).
Give a concrete exemplar commit to copy — ideally a sibling lane that already
solved the same seeding problem on the new contract (e.g. "seed FULL via
`scope_detectors(SCOPE_FULL)`, no hard-coded list — see <sha>"). Exemplar >
prose: it pins both the API and the no-hard-code discipline in one pointer.

## 5. Re-run the FULL combined gate after the seed fix

Merge the seed-fix commit into the integration tree, then re-run EVERY gate
item, not just the fixed one — interactions cut both ways and a seed change
can shift neighboring assertions. Append raw output to the same gate log.

## 6. Product-bug escape hatch

If no legitimate seed can satisfy the gate (the interaction exposes a real
product defect, not a fixture gap), stop seeding work and escalate to a
`NEEDS_<OWNER>_PRODUCT_FIX` terminal with raw log — that becomes its own
conditional lane with the owning team, not a seed tweak.

## Follow-on nudge narrowing (wrapper exited before commit)

Resume-based workers often finish patch + GREEN gate but the wrapper exits
before commit: file modified, tip unchanged, no terminal line. Each successive
nudge must SHRINK to only the unfinished steps — never re-run green gates:

1. Nudge 1: gate + commit + terminal.
2. Nudge 2 (gate GREEN on disk, still uncommitted): commit-only —
   "do NOT re-run tests, copy evidence + commit + one terminal line. STOP."
3. Verify the commit yourself by re-running the DECISIVE test on the committed
   tree (counts + seconds), never by trusting the worker's quoted numbers.
