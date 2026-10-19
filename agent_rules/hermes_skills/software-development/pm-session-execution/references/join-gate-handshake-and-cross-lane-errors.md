# Join-gate handshake & cross-lane transient errors (S09-C1, 2026-08-24 night)

Two patterns from the 5-worker fast-track round that the main liveness reference doesn't yet carry.

## Hash handshake derivation is often undocumented — reverse-engineer before accepting

J1 context: T02-C1 published `CONTRACT_FROZEN: SHA-256 = 46c6a41f…` for "renderer_contract.py + renderer_routes/__init__.py + composite.py" but its dispatch.log never showed the command that produced it. The manager must reproduce a freeze hash before trusting it — accepting an unreproducible hash defeats the handshake.

What did NOT match (try these first anyway, they're common):
- raw concatenation of file bytes
- per-file sha256 hex strings joined by '' / '\n' / ' '
- same variants with CRLF→LF normalization
- adding the router as a 4th file

What DID match (byte-exact): **path\0-content accumulation**
```python
import hashlib
h = hashlib.sha256()
for f in files:            # in the order the worker listed them
    h.update(f.encode())   # relative path string
    h.update(b'\0')
    h.update(open(f, 'rb').read())
# h.hexdigest() == worker's published hash
```
Procedure when a freeze hash can't be reproduced:
1. Enumerate schemes systematically — raw concat → per-file-hash joins → path\0-content accumulation (with/without router, with/without CRLF normalization).
2. Don't accept OR reject until one matches byte-exact; never "trust" the worker's quote.
3. Once reproduced, RECORD THE FORMULA in the registry so later handshakes on this sprint reuse it instead of re-deriving.
4. Then broadcast the named gate signal (`T02_CONTRACT_FROZEN_FOR_I03`) via a resume packet to the dependent lane.

## In-flight sibling edits cause transient cross-lane errors — attribute by write-set

T56's mypy surfaced `s09_demo_jobs.py:203: "object" not callable` while T02-C1 was mid-edit of `select_route()` in `renderer_routes/**` (its return type changed shape mid-wave). `s09_demo_jobs.py` imports `select_route`, so the type error was a CONSEQUENCE of a live sibling edit — not a T56 defect and not a defect at all yet.

Correct response:
1. Record the error WITH attribution ("consequence of T02-C1's in-flight edit of select_route; will resolve when T02 exits") instead of reopening the verified lane or dispatching a fixer into another live writer's write-set.
2. Re-check mypy at the final gate AFTER the owning worker exits.
3. Rule: during parallel waves, only errors inside a VERIFIED lane's own allowlist reopen that lane; cross-lane transients get attributed and deferred to the gate.

## Recurring Python gotcha — PEP 562 lazy re-export kills mypy types

Package `__getattr__(name) -> object` (the standard trick to break circular imports, used in `renderer_routes/__init__.py`) makes mypy infer EVERY static import routed through it as `object` → downstream `error: "object" not callable` (real case: `s09_demo_jobs.py:203 select_route`). Runtime works; static typing silently dies.
Fix belongs in the PACKAGE's write-set, not consumers: add a `if TYPE_CHECKING:` import block re-exporting the lazy names in `__init__.py`, keeping the runtime `__getattr__`. After the fix `mypy app --no-incremental` must reach 0 errors across all source files — verify with the full app scope, not just the touched package.


Related: verify-by-discovery trap from the same round — when checking "adversarial coverage exists", discover the lane's actual test files first (`ls tests/<prefix>*`) rather than grepping only packet-named filenames; workers add new files (real case: +39-test validation file). And docstring hits are not code hits: after "remove stale literals", one grep hit remained — inside the comment explaining the removal.

## C2 upgrade — recursive freeze manifest replaces combined hash

C1's 3-file combined hash went stale when `renderer_routes/__init__.py` changed post-freeze and nothing caught it until review (F3, P0). C2's join therefore mandates:
- Manager hashes RECURSIVELY every behavior-critical file (`renderer_contract.py`, `renderer_router.py`, `app/adapters/renderer/**`, `app/services/renderer_routes/**`) into a machine-readable `path -> SHA-256` JSON at a pinned evidence path; manifest SHA goes into the registry.
- The measured lane verifies the manifest BEFORE and AFTER each run; any drift ⇒ stop, invalidate ALL downstream runs/decisions, resume the owner that drifted, rebuild the join, re-run everything downstream. Patching just the recorded SHA constant is forbidden.
- Workers must stop at explicit phase states (`WAITING_JOIN`, `CORRECTION_SUBMITTED_Cn`) instead of `TASK_SUBMITTED` when their final binding depends on an unlanded join — this gives the manager clean resume points for Wave B/C without re-opening scope.

## Terminal-state discipline (the F1 lesson)

Honest worker evidence is not sufficient for `TASK_MANAGER_VERIFIED`: in C1 both routes failed to measure two REQUIRED risk classes and the workers truthfully reported FAIL_OPEN_QUESTIONs — but the manager still wrote TASK_MANAGER_VERIFIED, which Codex graded as a P0 protocol violation. Rule: before writing ANY terminal line, re-read the prompt's verification/terminal section and check each listed blocker condition against current evidence; "required class fail/unknown/FOQ" ⇒ terminal MUST be `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. The registry/packet should quote the exact prompt clause that determined the choice.

