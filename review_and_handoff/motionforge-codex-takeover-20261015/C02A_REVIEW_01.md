# C02A — CHANGES_REQUESTED (C02A-R01)

Root independently reviewed candidate-01 after the writer stopped. Manifest
SHA256 d3478b534182dd6cc34e219f7da12fe71bb9fde3abdbe2a6978e17c3d8fe2a18;
cache SHA256 946935906625d79b95153a92d4cf86310551cfbc4533a3661f2011854aeae7a7;
gate SHA256 8c2e3f9eedd4d8e11832809c2b72293db17df1fb5a4012bd39fa396f93143f94.

Fresh root recorded-dependency matrix: 55/55 pass, exit 0, at
root-review/c02a-candidate-01/RESULT.json. Root scope/AST audit verifies all four
submitted files and snapshots, pinned diffs/receipts, 24 protected files unchanged,
all 17 C01 test names/assertion ASTs unchanged, no duplicate definitions; receipt
root-review/C02A_SCOPE_CANDIDATE01.json. Worker reports 28/28 tests; root has not
used that result as an independent broad-gate verdict. The additional micro
failure below must close first.

## C02A-R01 [P2] Parsed nested records escape verification as RecursionError

Location: R6/scripts/r6_cache.py, `_json_value` recursion and its two calls in
`verify_deps`; consumed by R6/scripts/r6_gate.py `key_inputs_now`.

The new catch in `load_deps` handles parser recursion, but the parser can accept
more nesting than the recursive Python value validator. Root constructed normal
v3 records with tiny valid files, correctly recomputed self-digest, a bound PASS
review, and nested JSON arrays in settings. At depths 10 and 200, both direct
verify and real gate_key return normally. At depths 400 and 800, load_deps says
ok, but both verify_deps and gate_key raise uncontrolled RecursionError.

Evidence: root_probe_c02a_nesting.py and
root-review/c02a-nesting-candidate-01/RESULT.json, 4/8 pass, exit 1. Copied exact
modules and tiny fixture files are preserved in that directory. This is a
controlled-error contract failure, not evidence of encoder execution or semantic
acceptance. The actual consumer can abort outside GateBlock diagnostics despite
the stated malformed-input contract.

Required fix: handle nesting through the entire validation path, including the
settings traversal, whole-record traversal and digest computation, with a bounded
controlled rejection or a safe traversal. Keep ordinary valid inputs passing.
Do not raise interpreter recursion limits, swallow arbitrary unrelated exceptions,
weaken assertions, or treat only a parser-depth failure as verification proof.

## Session Opening Proposal and complete correction prompt

Read the entire current C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md
before preflight or continuing. Resume exact owner `/root/motionforge_c02a_coder`,
same CODEX-C02A-DEPENDENCY-VERIFICATION, gpt-6-sol / max, no fallback. Status
AUTHORIZED_TO_DISPATCH; old writer terminal and frozen candidate hashes verified.
No new context/owner needed for this focused correction. One CPU writer, no GPU,
Hermes, C02B, Git operations or producer/common/assembler changes.

The original TASK_C02A.md remains the complete required-reading and write scope.
For R01 change only the cache validation and new C02A regression tests as needed,
plus c02a-worker evidence. Preserve candidate-01 bytes/manifest and make byte-
matching preimages before bounded patches. Approved C01 assertions remain intact.

Finite anti-omission matrix: nested settings and a nested extra top-level value;
depths 10, 200, 400, 800 and a parser-rejected depth (1200). Depth 10 is a valid
positive. All depths must either verify/return or reject with false+reason /
GateBlock, never an uncontrolled exception. Exercise strict loader followed by
verify_deps, real gate_key and skip_allowed (skip may deny on existing settings
policy; do not remove that policy to force a positive). Include real assembly
consumer coverage for a parsed-but-rejected nesting case and retain ordinary
assembly and source-passthrough positives. Check both recursive traversal sites;
do not use a mocked validator. Keep original A1–A6 and the 55-case matrix intact.

Reproduce -> bounded correction -> focused nesting matrix -> original matrix ->
full affected modules -> self-review. Save commands/exit codes, raw receipts,
exact hashes/diffs, updated checkpoint and an immutable candidate-02 manifest.
Stop all source/test writes at submission. Root reruns independently; parent and
C02B remain blocked. No further approval is needed to implement this correction.
