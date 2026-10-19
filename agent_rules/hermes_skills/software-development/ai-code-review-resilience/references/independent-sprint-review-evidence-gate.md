# Independent Sprint Review — Evidence Gate

Use this reference when reviewing an agent-built sprint after a manager says
`MANAGER_VERIFIED` or `SPRINT_SUBMITTED`.

## 1. Freeze and reconcile

Run read-only checks in the target worktree:

- `pwd`
- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git status --short`
- MAIN branch/HEAD/status separately
- `MOTIONFORGE_DATABASE_URL` must be unset
- `python -m alembic heads`
- protected file hashes and DB sizes
- process table for the exact owning session plus wrappers/tee/log writers
- relevant listeners/ports

A writer process can still mutate the reviewed tree even if the manager state
says `writers: none running`. Do not kill it as a reviewer; record the review as
unfrozen and reject evidence produced while it was live. Compare report claims
against actual evidence directory existence, file mtimes, hashes, and raw logs.

## 2. Mocked versus real evidence

Classify every test separately:

- **Mocked UI:** `page.route`, `route.fulfill`, mocked fetch, fabricated response
  objects. Useful for loading/error rendering only.
- **Backend integration:** real route/repository/temp DB, but no real product UI.
- **Real vertical:** real product page -> real frontend API client -> real backend
  route -> real repository -> isolated temp SQLite -> reload from persisted DB.

`page.route("**/*")` in a Scenario I spec is not real vertical evidence when it
fulfills the business endpoints. Do not report it as end-to-end merely because
Playwright passes on desktop and mobile.

## 3. Production-realistic fixtures after stricter invariants

When a correction changes a write boundary from advisory evaluation to
fail-closed enforcement, all compatible fixtures must satisfy the production
contract. For a published character pack requiring core poses, create every
required pose asset (`front`, `three_quarter`, `side`, `back`, `sitting`,
`walking`) with valid workspace/artifact relationships.

A test that creates an empty `status="published"` pack and expects repin success
is stale after completeness enforcement. Repair the fixture and assert exact
outcomes; never weaken the production check or add `if state: skip` branches.

For every rejected POST/PATCH assert:

- exact status and stable reason;
- `compatible is False`;
- `blocked is True`;
- fallback cannot enable submit;
- no row or idempotency-key mutation;
- old mapping fields and revision remain byte-identical.

## 4. Authority and contract checks

For generation or freshness policies:

- verify the authoritative backend call is used;
- reject direct comparison of unrelated domains such as role generation versus
  pack version;
- do not swallow authority exceptions into `current_generation=None`;
- authority failure must fail closed with zero mutation.

For CAS endpoints, verify all four surfaces:

1. repository signature;
2. route signature;
3. OpenAPI requiredness/schema;
4. runtime missing/stale behavior.

A runtime `if revision is None: 422` does not fully satisfy a required CAS
contract if OpenAPI still publishes `revision` as optional.

For workspace isolation, the workspace context must be server-owned. A default
value on a client-controllable query parameter is still client authority unless
an explicit authenticated tenant resolver is enforced.

For UI submit state, `fallback_allowed` is advisory unless the contract
explicitly defines durable fallback acceptance. `compatible=false` must always
disable create/repin and the backend must enforce the same rule independently.

## 5. Verdict gate

Return `APPROVED` only if all of these are true:

- evidence is frozen and process state matches manager state;
- focused tests pass on final source;
- relevant regressions pass;
- quality gates pass;
- migration/API contract is verified;
- product surface is really mounted;
- at least one real vertical scenario passes without business-endpoint mocks;
- protected MAIN data is unchanged;
- no P0/P1 remains.

Otherwise return `CHANGES_REQUESTED` with:

- priority;
- exact file/function/line;
- reproduction command or source vector;
- expected versus actual;
- product impact;
- missing/weak test;
- owning Task ID and owning session;
- a complete correction prompt that resumes the old session and stops at the
  next Codex review gate.
