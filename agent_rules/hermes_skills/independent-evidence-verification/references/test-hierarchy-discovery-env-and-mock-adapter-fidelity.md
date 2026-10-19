# Test Hierarchy, Discovery Env, and Mock Adapter Fidelity

Evidence and verification pitfalls discovered during isolated test suite completion and gate verification.

## 1. Unittest Subclass Method Inheritance Trap

When constructing test fixtures for multiple variants (e.g., single-actor, multi-actor, no-visible-actor, fully-covered-actor):
- **Trap**: If the base class defines test methods (`def test_...`), every subclass automatically inherits and executes those methods.
- **Symptom**: If `PerActorVerifiedReuseTests` contains `test_p1_single_actor_replay_unchanged` (asserting `calls["crop"] == 1`), a subclass `MultiActorVerifiedReuseTests` inherits and runs it with 2 actors, failing with `AssertionError: 2 != 1`. A `NoVisibleActor` subclass runs it with 0 actors, failing with `AssertionError: 0 != 1`.
- **Rule**: Separate fixture setup from test methods:
  - `BasePerActorFixture(unittest.TestCase)`: carries `setUp`, teardowns, fixtures, and helper methods ONLY. Zero methods starting with `test_`.
  - Concrete test classes:
    - `class SingleActorVerifiedReuseTests(BasePerActorFixture)`
    - `class MultiActorVerifiedReuseTests(BasePerActorFixture)`
    - `class NoVisibleActorVerifiedReuseTests(BasePerActorFixture)`
    - `class FullyCoveredActorReuseTests(BasePerActorFixture)`
  This keeps all test counts exact and prevents cross-variant assertion bleed.

## 2. Test Discovery Environment Variable Trap

- **Trap**: Hardcoding mandatory environment variables at module top-level:
  `WORKER = Path(os.environ["C02B1_WORKER_DIR"]).resolve()`
- **Symptom**: Standard suite discovery (`python -m unittest discover`) fails during module import with `KeyError: 'C02B1_WORKER_DIR'`, blocking execution of unrelated test modules.
- **Rule**: Always supply a safe local default fallback for discovery:
  `WORKER = Path(os.environ.get("C02B2_WORKER_DIR", Path(__file__).resolve().parents[1] / "work/c02b2-worker")).resolve()` or `tempfile.gettempdir()`.

## 3. Multi-Stage Gate Settings Alignment in Negative Tests

- **Trap**: When verifying that a gate rejects a legacy or partial contract with a specific reason (e.g. asserting `"legacy v3 lacks complete per-actor provenance" in why`), passing dummy settings causes an earlier gate check to fire first.
- **Symptom**: `AssertionError: 'legacy v3 lacks complete per-actor provenance' not found in "settings changed now: ..."`.
- **Rule**: Inspect the gate's evaluation order. When testing a downstream rejection branch, ensure all upstream preconditions (such as `cur_settings = cache.settings_now(sid, fid)`) are strictly matched so the test actually exercises the intended denial branch.

## 4. Mock Adapter Fidelity for Boundary Error Injection

- **Trap**: A mock adapter loader that ignores arguments and returns a constant tensor:
  `adapter.load_img = lambda path: frame.clone()`
- **Symptom**: A negative test verifying that blank edit outputs trigger `BLANK EDIT (std < 0.01)` fails with `AssertionError: SystemExit not raised`, because the mock loader returned the non-blank fixture frame instead of reading the blank file.
- **Rule**: Mock loaders must inspect path sentinels or read file bytes:
  ```python
  def _load_img(path):
      if "blank" in Path(path).name:
          return torch.zeros((1, 8, 8, 3), dtype=torch.float32)
      return frame.clone()
  adapter.load_img = _load_img
  ```

## 5. Semantic Review Schema Verification vs Fabricated Signatures

- **Trap**: Assuming an unread schema feature like cryptographic `signature` or generic `status` when mutating a review artifact.
- **Symptom**: `AttributeError: module 'r6_gate' has no attribute 'sha_obj'` or review silently passing because the mutated key was ignored.
- **Rule**: Read the consumer's `require_review` parser first:
  `r6_gate` checks `verdict: "PASS"|"FAIL"` and `artifact.sha256`. Mutating `rec["verdict"] = "FAIL"` or `rec["artifact"]["sha256"] = "0" * 64` directly and deterministically triggers `GateBlock`.
