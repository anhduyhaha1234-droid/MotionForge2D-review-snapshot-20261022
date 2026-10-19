# An unreachable gate is a finding — never a licence to loosen it

When a lane reports that a gate **cannot** pass through the public path, the deliverable is an
**asserted negative control**, not a relaxed gate. This rule exists because the tempting shortcut
(seed the state, drop to a cheaper scope, or edit the gate) produces a green that hides a real
product defect.

## Measured case (2026-09-24, S12 export preflight)

- The export preflight answered `S12_EXPORT_NOT_READY` — **1 of 9 complete checks failing** on
  `readiness`.
- Root cause: `readiness = 'ready'` requires a **completed current-scope `SCOPE_FULL` QC run**, but a
  full-scope run is itself refused `422 QC_RUN_EVIDENCE_UNAVAILABLE` for a fixture whose single
  `occurrence_segment` can never satisfy the cut detector's per-scene requirement. So **no PASS is
  reachable through public APIs** — the gate is unreachable by construction, not by a bug in the
  runner.
- The lane's acceptable response (and what to demand of any lane in this position):
  1. Accept **exactly** the expected refusal — `reasons == ['S12_EXPORT_NOT_READY']`,
     `failed == ['readiness']`, `readiness_status == 'not_run'`.
  2. Record that the gated action was **not attempted** (here `s12_export_submitted=false`).
  3. **Fail the node on any other ineligibility** — the control must be narrow enough that a different
     failure reason cannot sneak through it.
- Forbidden moves, all of which were explicitly ruled out and must stay ruled out: seeding QC or
  eligibility rows, SQL-manufacturing the state the gate wants, downgrading full scope to audio-only
  (or any cheaper band) to obtain a green, or editing the gate itself.

## Corroborate before escalating

A single red node can be a test bug. Before calling the gap **product-level**, require ≥2 independent
corroborations. In the measured case there were three:

1. a sibling regression node that hit the same wall (`test_r6_b01i_public_chain.py`),
2. the frontend's own e2e helper (`frontend/e2e/s12-export-seed.py`) **seeding a completed full run**
   — i.e. the app's own tooling works around the gap,
3. the server's own `check_state_detail` naming `readiness` as the failing check.

Then hand the finding upward with the **smallest exact delta** (file / DTO / Task ID) that would make
the gate reachable legitimately, so the next grant can be bounded instead of a vague "connect later".
Do not implement that delta in a verification lane, and do not let the demo line claim the journey
completed while this control is red.

## Reviewer rule of thumb

A lane that reports "PASS" by relaxing a gate is **worse** than a lane that reports the asserted
block, because the block is auditable and the green is not. When verifying, ask which one you are
looking at: read the assertion, confirm it pins the exact refusal values, and confirm the gated action
was skipped rather than attempted-and-ignored.
