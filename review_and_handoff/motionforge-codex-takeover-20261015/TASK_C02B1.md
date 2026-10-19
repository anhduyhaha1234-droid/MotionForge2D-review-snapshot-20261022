Read the entire current C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md before preflight or implementation. Apply current user-authorized Codex lane §0.11. Do not dispatch Hermes.

# CODEX-C02B1-STAGED-SOURCE-FRESHNESS

One outcome: r6_common.stage_frame must not return an existing frame from a different source identity, source bytes, requested global frame or modified output. Reuse the existing FFmpeg extraction path with provenance validation. This is a small adapter/cache fix, not a new renderer or full C02B producer redesign.

MAIN=C:/Users/Admin/MotionForge2D
R6=C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6
OUT=C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-codex-takeover-20261015
PY=C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe

Owner /root/motionforge_c02b1_coder; gpt-6-sol, reasoning max, fallback disabled. One CPU writer, no subagents. Prior C02A owner is completed and candidate02 independently approved in C02A_REVIEW_02.md. Parent remains NOT_APPROVED. Status AUTHORIZED_TO_DISPATCH after C02B1_PREFLIGHT.json ok=true. MAIN HEAD a40e368f7c47c232cf2eeed9fb185c5972cb98ba, preexisting dirty protected; INTEGRATION HEAD a52fca897906fd61a088016dd802718fdf06d217 clean. Exact source authority is external R6 byte snapshots, not Git.

## Required reading and context

Read full canonical rules, MAIN/AGENTS.md and MAIN/docs/pm/SESSION_PROTOCOL.md. Then this packet, C02A_REVIEW_02.md, C02B1_PREFLIGHT.json, skills/ACTIVE_DIGEST_VI.md, current r6_common.py and the stage_frame call sites in r6_keygen.py/r6_keygen_asset.py. Load only systematic-debugging, verification-before-completion and receiving-code-review skills from C:/Users/Admin/.codex/skills/<name>/SKILL.md. Preserve user/model/current scope over conflicting generic skill instructions.

Optional: root_probe_c02b1_staging.py and root-review/c02b1-baseline/RESULT.json; current C01/C02A tests to understand isolation. Do not inspect whole repo/history. Existing historical test modules may touch production; do not import them blindly.

## Reproduction and reuse decision

Current stage_frame returns any nonempty dst immediately; it does not check SRC or gframe. Root isolated real-helper probe gets2/7 in a sequential mutation exercise: initial/unchanged pass, stale changes go undetected. Its FFmpeg boundary is substituted; this is not real extraction proof. After C02A correctly invalidates a key, the producer may still use a stale staged source and record a fresh source hash. This task closes only that staging gap.

Use installed FFmpeg (root verified8.1.2) and Python standard-library hashing/atomic-file APIs. Do not install anything or write optical flow/render core. Existing callers must retain the stage_frame(sid,gframe,dst)->Path contract and current global frame mapping. Preserve640x360 canonical fixture/source behavior and no extra padding.

## Allowed and forbidden writes

- R6/scripts/r6_common.py: stage_frame and tightly related private provenance/extraction helpers/imports only. Leave unrelated source/cast/style/frame-map/network functions untouched.
- New R6/tests/test_codex_c02b1_staged_source.py.
- OUT/c02b1-worker/**: byte preimages, isolated fixtures, logs, commands, receipts, diffs/checkpoints/candidate snapshots.

All27 other source/test files are protected, including approved cache/gate/C01/C02A tests and both key producers. MAIN/INTEGRATION, PM state, source media, model, cast/style, historical outputs/reviews/receipts, DB/config/runtime are read-only. No Git commit/push/reset/stash/clean, GPU/Comfy/upload/WAN or pilot/full-source rendering. Tiny local CPU FFmpeg fixtures and extraction are explicitly allowed inside c02b1-worker isolation only. Never call stage_frame against real production paths while testing. Do not hash the real model/source for unit tests.

Existing file patch-only: verify preflight, make byte-matching preimages, bounded patches and hash/size/line receipts after each patch. New test skeleton then patches allowed. Missing file/unexplained shrink => stop and preserve. Root never edits implementation.

## Contract and finite acceptance matrix

Choose a small versioned sidecar/provenance record adjacent to staged output. Bind canonical source path and exact SHA256, sid/requested global frame, canonical output path and output bytes/hash, and the extraction contract version. Do not trust mtime/size alone or mere receipt existence. Regenerate legacy outputs with no trustworthy record rather than claiming provenance retroactively. Strict malformed/type/identity errors must never silently bless cached bytes.

S1. First extraction succeeds; same unchanged valid request/output reuses with no FFmpeg execution. Verify exact output and return path.
S2. Same-source-path same-size byte change, changed canonical source path with identical bytes, changed requested frame, and same-path output-byte mutation each invalidate. Restored controls behave according to current provenance. Copying a receipt between frames/destinations cannot bless the wrong output.
S3. Legacy existing nonempty output without receipt, empty/missing output, malformed/nonobject/duplicate/type-invalid/incomplete receipt, wrong source/output digest or frame identity: no stale reuse. Bound or safely reject deep malformed JSON too. No forced broad schema framework.
S4. Failed extractor, success exit with missing/empty temp output, unreadable/missing source, invalid requested frame (bool/negative/outside current shot plan) and source bytes changing during extraction return controlled errors. Extraction failure preserves any previous valid output/receipt bytes. A partial publication failure must never report successful reuse and must be detected on the next call. Do not delete unrelated files.
S5. Extract into a unique temporary sibling and publish only a validated result; finish provenance after successful output publication. Check source identity remains the one consumed across extraction. Retain old frozen artifacts; the helper is tested only on isolated paths. WIP1 is the concurrency contract; do not build a new lock framework.
S6. A real tiny CPU FFmpeg fixture with distinguishable frames at30fps640x360 proves requested frame mapping, source replacement invalidation and unchanged reuse. Compare actual image content or decoded pixels, not only existence/hash differences. Keep fixture command/raw result. Mock external I/O only for failure injection; do not mock stage_frame/provenance validation.
S7. Real common helper coverage, root seven-case probe, full new test module and full approved C01+C02A modules; all prior protected hashes/assertions unchanged. Audit duplicate definitions and diff scope. Run micro -> finite matrix -> affected modules, with no broad gate before micro closure.

Current C02B2 effective-settings mismatch, complete graph/ref/mask capture, asset reuse and media semantics remain open. Do not fix those here or claim unchanged whole-key reuse from unchanged staged-frame reuse.

## Checkpoint, self-review and submission

Use small coherent patch/test units. After each unit and before compaction/provider errors save intent, task/owner/model, exact files+hashes, commands+exit, decisions, remaining, next command and live jobs. Large logs go to files; concise summaries in messages. Do not estimate context percentage from message count. No arbitrary total time/token/candidate cap. Quota errors keep this owner/checkpoint; no reset/purchase/model fallback/new task to evade limits.

Self-review against S1-S7, negative controls, transaction failure, caller compatibility, source binding and protected bytes; repair within this scope. Save immutable candidate manifest with live paths+snapshots+SHA/byte/line counts, preimages, diffs, raw command receipts, REPORT/LOG and terminal checkpoint. State TASK_SUBMITTED_PENDING_ROOT_REVIEW; stop source/test writes and no live jobs. Root independently reruns and approves exact bytes before any next task.

Start with preflight and bounded reproduction, then implement now. No additional user confirmation is needed.

