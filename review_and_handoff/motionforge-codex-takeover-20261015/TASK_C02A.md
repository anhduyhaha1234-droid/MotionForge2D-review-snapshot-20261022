Read the entire current `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md`
before preflight or implementation. Apply §0.11: this is the user-authorized Codex
lane, not a Hermes dispatch. Do not start Hermes.

# CODEX-C02A-DEPENDENCY-VERIFICATION

One outcome: a missing, malformed, misidentified or byte-stale recorded key
dependency cannot authorize the actual key/assembly consumer. A complete valid
current producer v3 record passes verification. CPU only, one writer.

MAIN=C:/Users/Admin/MotionForge2D
R6=C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6
OUT=C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015
PY=C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe

## Required reading

Full canonical rules, MAIN/AGENTS.md, MAIN/docs/pm/SESSION_PROTOCOL.md;
OUT/C01_REVIEW_02.md, OUT/C02A_PREFLIGHT.json, OUT/skills/ACTIVE_DIGEST_VI.md;
current r6_cache.py, r6_gate.py and relevant r6_common.py frame/path functions;
actual build_deps call sites in r6_keygen.py and r6_keygen_asset.py; existing C01
tests. Load only systematic-debugging, verification-before-completion and
receiving-code-review from C:/Users/Admin/.codex/skills/<name>/SKILL.md.

## Optional evidence

OUT/NEXT_SCOPE_DOCKET.md and root-review/c02-baseline/RESULT.json explain the
baseline; reproduce on current files before patching. Historical v2/v3 deps and
reviews may be read to clarify compatibility. Do not import unsafe historical
test modules that write/delete real production artifacts. Read function bodies
first and isolate all paths. No whole-repo cleanup/search for extra work.

## Allowed write scope

- R6/scripts/r6_cache.py: strict recorded-dependency validation.
- R6/scripts/r6_gate.py: necessary actual-consumer validation wiring and controlled
  GateBlock diagnostics. Preserve approved C01 review binding.
- New R6/tests/test_codex_c02a_dependency_verification.py.
- Existing R6/tests/test_codex_c01_review_binding.py: bounded fixture setup updates
  only where a real dependency record is now required; retain all prior assertions
  and 17 tests. Explain every such fixture edit. No skip/ignore/weakened expectations.
- OUT/c02a-worker/**: preimages, fixtures, logs, raw receipts, diffs and checkpoints.

Existing source/tests are patch-only. Verify the root preflight and create your
own byte-matching snapshots before edits; log hash/byte/line counts after each
patch. Missing files or unexplained shrink => stop and preserve evidence.

## Forbidden scope

No producer/graph/common/adapter/assembler changes, no dependency schema migration
or historical artifact/review rewrite, no model/runtime/DB/registry/PM changes,
no GPU/Comfy/post/upload/ffmpeg/render, no Git commit/push/reset/stash/clean, no
subagents or fallback. Tiny fake source/model files only inside isolated tests.
Do not hash the full real model repeatedly for tests. Root remains the PM writer.

## Current defect and contract boundaries

`verify_deps({})` currently returns `(True, 'ok')`; missing model/source hashes
also pass. `key_inputs_now` hashes a deps JSON without validating its current
underlying files, so an unchanged JSON/review can authorize changed source/model/
cast/mask/graph bytes. Current v3 build_deps includes source/model hashes and a
self digest; older incomplete v2 cache must fail closed and require regeneration,
not be silently upgraded or blessed. A review hash is not dependency verification.

Keep the existing v3 producer format for this step. Validate all mandatory
structure/types/identity before path/index access, including kind, shot/fid,
source path/hash/gframe/span, model path/hash, cast/mask lists, graph field,
nonempty settings and deps_sha integrity. Known explicit no-visible-actor source
passthrough may have empty lists and graph=None; do not reject that valid mode or
use it to exempt source/model identity currently required by v3. Generated modes
must not gain a blanket graph omission exemption. Pin source/model to the current
canonical paths, and compare shot/fid/frame/span to the actual consumer request
and K.PLAN mapping, not just the record's own claims. Return a controlled false
diagnostic or GateBlock for malformed/unreadable dependencies; no uncontrolled
TypeError/KeyError/JSON errors on the consumer path.

This step verifies the recorded dependency contract; it does not prove that the
old producer recorded every consumed graph/ref. Producer completeness, effective
settings equality (ctx default 1.02 vs 1.3, seed offset and entity selection),
asset reuse wiring, staged-source freshness and actual end-to-end unchanged reuse
are C02B, outside this write-set. Do not remove settings comparison to obtain a
green skip. Preserve that open limitation explicitly.

## Finite acceptance matrix

A1. Current build_deps v3 positive with tiny files verifies; valid no-visible-actor
    passthrough verifies. Use actual builder, no hand-built incompatible schema.
A2. Empty/nonobject/partial dependency records, missing required fields, wrong
    types (including bool as int), empty/nonhex hashes, malformed JSON/duplicate
    fields/non-JSON constants, missing file/unreadable path all fail controlled.
A3. One-field and combined wrong kind/shot/fid/source path/model path/gframe/span
    fail even when file bytes match and the self digest has been recomputed.
A4. Self-digest tamper fails. Same-path same-size byte mutation of source, model,
    cast, mask and graph independently fails; restored unchanged files pass.
A5. Actual gate_key and gate_assemble/assembler entry wiring block stale/missing
    deps before copy/encoder. Cover a valid positive and the omitted-source/hash
    negative through the real consumer, using isolated fixtures and tripwires.
A6. Existing C01 integrity expectations remain intact: full 17-test module plus
    new complete module; audit duplicate definitions and exact final hashes.

For broad error categories use a table-driven matrix with explicit case counts,
expected outcomes and raw results. Red repro -> small patch -> micro matrix ->
full affected modules -> self-review. Avoid broad tests before micro closure.
Tests may substitute external I/O/GPU boundaries but must exercise real cache and
gate functions. Never turn verify_deps/require_review into a mock that simply fails.

## Context, quota and submission

Owner `/root/motionforge_c02a_coder`, model gpt-6-sol, reasoning max, no fallback.
One task/context with targeted reads and 3 skills; raw large outputs go to files.
After each coherent patch/test unit and before compaction, save CHECKPOINT with
intent, exact files/hashes, decisions, test command/exit, remaining, next command,
owner/model and live jobs. Do not invent remaining context percentages. No new
arbitrary total budget/deadline/continuation cap.

On provider/quota error preserve the exact message and checkpoint; report the
observed block. No purchase/reset, no alternate task/model to bypass quota.
Self-review correctness, negative controls, producer compatibility, untouched
assertions and write scope; repair within this packet. Then submit immutable
candidate manifest, diff, REPORT, LOG, raw test receipts and checkpoint, set
TASK_SUBMITTED_PENDING_ROOT_REVIEW and stop all source/test writes. Root alone
approves exact bytes. No parent/Q07/video/project acceptance claim from this task.

Start with baseline and reproduction now, then implement the authorized patch.
