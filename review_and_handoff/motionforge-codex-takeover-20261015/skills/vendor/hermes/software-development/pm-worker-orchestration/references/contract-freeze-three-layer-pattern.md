# Cross-module contract freeze — three-layer pattern (owner draft → Manager rulings → QA co-sign)

Proven on S12-R7 BRIDGE (2026-09-16): a cross-sprint interface task ("First produce CONTRACT.md
and freeze with Manager B/QA before code"). The three layers caught a false premise that would
have broken the entire real product chain — the pattern exists to make that catch routine.

## Layer 1 — Owner draft (docs-only, zero production code)
- Grounded in REAL code: file:line refs, exact schema pseudo-blocks, per-phase fail-closed code
  tables (approval-time / submit-time / worker-time), worker-consumption rules.
- Ends with a NUMBERED open-questions list (Q1..Qn), each with the owner's recommendation.
- Commit docs-only; the draft commit is the freeze candidate (`CONTRACT_DRAFTED_PENDING_FREEZE`).

## Layer 2 — Manager rulings (per question)
- Rule each question: ACCEPT / REVISE / RESERVE-TO-QA. Tie the ruling to acceptance rows —
  R7 example: acceptance row said "points-only/missing/ambiguous boxes → honestly ineligible",
  which flipped Q1 from the draft's "pick boxes[0]" to **deny typed on differing boxes**
  (AMBIGUOUS code) while keeping documented key precedence across keys.
- Where the draft's premise is wrong, amend it in a VERSIONED ruling doc:
  `*_FREEZE_REVIEW.md` (rulings) + `*_RULING_<topic>_v0.2.md` (amendment). Flag amendments in
  the final packet for the external reviewer (they go beyond the original question list).

## Layer 3 — QA co-sign (evidence-grounded, not assumption-grounded)
- QA must verify each open question against REAL evidence (its own public-chain runs, persisted
  DB rows, byte-level fixture values) — not the draft's assumptions. This is where false
  premises get caught.
- R7 catch (QA-F1): contract assumed normalized `[0,1]` regions; real persisted boxes are
  PIXEL-scale (`{x:400,y:100,w:250,h:250}` on 640×360) → a plain bounds-deny would have
  rejected the ENTIRE sanctioned extraction world. QA produced 3 options + a recommendation;
  Manager ruled dual-mode derivation (normalize at derivation using source dims; typed deny
  `*_SCALE_UNRESOLVED` when dims unavailable) — a v0.2 amendment to the contract.
- QA writes the sign-off into ITS OWN docs (write-set discipline). QA NEVER edits the owner's
  contract file; it states the normative text and the OWNER pastes/cites it. Record who pastes
  what in the freeze artifacts.
- QA also defines acceptance artifacts it owns: e.g. exact per-layer evidence sidecar format
  (field table + acceptance rules + threshold) and the proposed test node-ID mapping per
  acceptance row (owner freezes those names VERBATIM into the lane inventory).

## Production dispatch (post-freeze)
The production prompt must cite ALL freeze artifacts by absolute path:
contract commit + ruling docs + amendment + QA sign-off location + exact node IDs +
dependency handling (e.g. "parse-and-validate path now; block only the dependent branch
until upstream fix lands") + write-set (allow/protected) + gates + ledger/commit rules.

## Why it works
- Each layer has a different bias: owner (design), Manager (acceptance rows + coordination),
  QA (real evidence). Conflicts between the biases surface as findings BEFORE code exists,
  when they are cheap to fix.
- All freeze docs are committed artifacts with hashes → the external reviewer can audit the
  decision chain (draft → ruling → amendment → sign-off) end to end.
