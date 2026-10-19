# C01 — Complete semantic review input binding

Authority: user15Oct explicitly requests Codex coding + independent root review,
selects gpt-6-sol / max. Read MAIN/AGENTS.md, SESSION_PROTOCOL.md, the full canonical
HERMES_AUTOPILOT_RULES.md (including0.11), this packet and skills/ACTIVE_DIGEST_VI.md.
MAIN=C:\Users\Admin\MotionForge2D
RUN=C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long
R6=C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6
OUT=C:\Users\Admin\Documents\Codex\2026-10-12\a-l-m-video-ra-m-2\outputs\motionforge-codex-takeover-20261015

Goal: a review with missing or malformed dependency binding cannot authorize the
actual assembly consumer. Current require_review iterates only recorded inputs;
omitting deps_sha can bypass dependency identity. Reproduce current bytes first.
No semantic quality claim from this engineering correction.

Write allowlist: R6/scripts/r6_gate.py; a new R6/tests/test_codex_c01_review_binding.py;
OUT/c01-worker/** (checkpoint, preimages, fixtures, tests/output/diff). Change
r6_assemble.py only if a reproduced consumer-wiring defect requires it; report why.
All other production files, historical evidence/reviews/media, runtime/model/DB/
registry/PM files are read-only. Never rewrite/delete existing tests or artifacts.
Root owns PM/lease reconciliation; require OUT/OWNERSHIP_PREFLIGHT.json with ok=true
before production edits. If absent, inspect and reproduce only in isolated fixtures.

Implementation sequence:
1. RULES_LOADED; preflight SHA/size/lines and preimage relevant existing files.
   Read existing gate callers/review writers/schema/examples and existing tests.
2. Reproduce the missing-input bypass and malformed records on current code with
   realistic fixtures; save raw commands and outputs under c01-worker. No GPU.
3. Small patch: validate complete nonempty current/recorded dependency mappings,
   required typed fields and exact review/artifact identity. Reject subset,
   mismatched, empty and malformed records with GateBlock diagnostics. Keep valid
   current producer schema compatible; do not invent a parallel review protocol.
4. Meaningful regression tests: valid positive; omitted current dependency;
   changed dependency; stale artifact; wrong artifact path/review identity;
   malformed JSON/types/frames. False values must not pass by string coercion.
   Actual gate_assemble path must reject invalid records before copying/encoding;
   include one real assembly main call with isolated K paths and encoder tripwire
   (no production output writes), not merely a mock that makes gate throw.
5. Run focused tests and relevant existing gate tests; self-review AC, correctness,
   compatibility, write scope, failure paths; fix within allowlist. Save exact
   candidate hashes + diff against preimages. Submit TASK_SUBMITTED and stop writing
   for root's independent review. Do not mark whole Q05/video/project APPROVED.

Skills to load now (local, actual installed): systematic-debugging,
verification-before-completion, receiving-code-review under
C:/Users/Admin/.codex/skills/<name>/SKILL.md. Apply compact context/checkpoint
contract here; library includes context-compression and Hermes source on demand.
No required meta-superpowers install, automatic commit or new approval round.

Context: one task outcome per context; only targeted reads, raw large logs to disk.
Checkpoint after every coherent patch/test unit or before context pressure, using
intent/current state/files+hashes/decisions/tests+exit/remaining/next command/jobs.
No context percentage claims without telemetry. No subagents. No model fallback.
On quota/credit error, preserve exact error and state; return BLOCKED_QUOTA with
known reset info only. Root notifies original chat; no tight retries.

Root review after writer terminal: inspect diff, run fresh negative/positive probes
and consumer integration independently; route corrections back to this same owner.
No production render until gate review accepted and GPU lease acquired separately.
Start now with preflight + reproduction, then implement; do not stop at a plan.
