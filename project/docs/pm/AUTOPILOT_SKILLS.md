# MotionForge2D Autopilot Skill Ledger

This ledger records skills the Hermes autopilot creates, modifies, or installs.

| Skill | Source/version | Purpose | Trust review | Validation | Status |
|---|---|---|---|---|---|
| `motionforge-autopilot` | local, 2026-08-04 | Durable phased roadmap execution | Local rules reviewed; no external hooks or credentials | Pending first bounded runner turn | Enabled |

## Quality skills added for Hermes — 21/10/2026

These are **instructions**, not new code or automatic gates. Canonical
`HERMES_AUTOPILOT_RULES.md` and the current task packet take precedence. Source
snapshots were copied into `C:/Users/Admin/AppData/Local/hermes/skills/`; no
plugin hook, package dependency or model route was installed. GitHub HEAD and
local `SKILL.md` SHA-256 below pin exactly what was inspected. Hermes lists all
five as `local / enabled` (106 local skills after install, previously 101).

| Skill / local path | Source, commit, license | Use for MotionForge | Overlap / routing | SKILL.md SHA-256 |
|---|---|---|---|---|
| `receiving-code-review` | [obra/superpowers](https://github.com/obra/superpowers/blob/b739a8af570e10a95898f2bdf6cec97467fa6c12/skills/receiving-code-review/SKILL.md), `b739a8a`, MIT | Worker verifies each Codex finding against actual code, fixes one item at a time, tests it | Complements existing `requesting-code-review` (asking for review) and `mf-code-review-and-quality` (reviewing a diff); do not load all three for every patch | `091df1629510af1b92fc4abd6f96732ebedb4cb2c0f3457e8f2740b0504a2438` |
| `property-based-testing` | [Trail of Bits](https://github.com/trailofbits/skills/blob/a3131740a39291e42fd15b9eac07e0b393ad71b1/plugins/property-based-testing/skills/property-based-testing/SKILL.md), `a313174`, CC-BY-SA-4.0 | Generate non-vacuous invariants for manifest/receipt/hash/path validators | Complements existing TDD and Python test patterns; use only if there is a real property and an authorized test/dependency write-set | `70965d420dd6d4324562ffb8eaef6df9881851701688d6b1f5a7aa404cb449f7` |
| `variant-analysis` | [Trail of Bits](https://github.com/trailofbits/skills/blob/a3131740a39291e42fd15b9eac07e0b393ad71b1/plugins/variant-analysis/skills/variant-analysis/SKILL.md), `a313174`, CC-BY-SA-4.0 | After one fake-proof bypass, search other callers/fields for the same root cause | Complements `systematic-debugging` (root cause) and `independent-evidence-verification` (artifact truth); narrow search can be manual, no agent dispatch required | `4d7dfdf8ec8f8260e3b52f5742253332bd6adde8a10bb77f5557da510957f89e` |
| `testing-anti-patterns` | [obra/clank](https://github.com/obra/clank/blob/2db8793f93061c6dbe924aec3a8080b748d7970f/skills/testing/testing-anti-patterns/SKILL.md), `2db8793`, MIT | Reject tests that assert mocks/self-labels rather than real adapter behavior | Complements TDD; choose it only for test-double/oracle design, not as a second generic TDD checklist | `ee3772cbe8ba52d06d1b5b5cd217728e37c64dc890b7be6277e23051fb1ec4a4` |
| `modern-python` | [Trail of Bits](https://github.com/trailofbits/skills/blob/a3131740a39291e42fd15b9eac07e0b393ad71b1/plugins/modern-python/skills/modern-python/SKILL.md), `a313174`, CC-BY-SA-4.0 | New, authorized Python tooling/scripts with ruff/pytest/typing | Not a G1 correction skill by default; **never** auto-migrate this repo, delete requirements/venv, install deps or replace its toolchain | `7e41e5f434ce30f512b64fafb23b5bd04f0bc064868641e6fb3773732fdb65a5` |

### Active routing; no duplicate removal

- G1-R1: Manager loads `independent-evidence-verification`; writer loads
  `systematic-debugging` plus `receiving-code-review`. For fake/missing proof
  tests add `testing-anti-patterns`; for related bypasses add `variant-analysis`.
  Use `property-based-testing` only after identifying a specific invariant and
  obtaining any required dependency/test-scope approval. Do not load all five.
- Existing `test-driven-development` remains installed but its upstream advice
  to delete code after a process mistake conflicts with the project's protected
  preimages/patch-only rule; **do not apply that deletion**. Keep the RED/GREEN
  test technique. `modern-python` migration examples are likewise inactive for
  this existing repository. Skills cannot override canonical rules or user scope.
- Keep existing `ai-code-review-resilience`, `mf-code-review-and-quality`,
  `independent-evidence-verification`, TDD and systematic debugging. They serve
  different roles; removing global/user skills would affect unrelated tasks.
  Reduce context by routing 1-3 relevant skills per packet, not by deleting them.

Installation note: `hermes skills install` via Skills Hub hit unauthenticated
GitHub API rate limiting. These exact Git snapshots were fetched directly from
GitHub and copied locally. `hermes skills audit` currently reports only
hub-installed skills, so it cannot attest these local copies; source files and
installed hashes were compared directly. Skill presence does not prove G1 PASS.
