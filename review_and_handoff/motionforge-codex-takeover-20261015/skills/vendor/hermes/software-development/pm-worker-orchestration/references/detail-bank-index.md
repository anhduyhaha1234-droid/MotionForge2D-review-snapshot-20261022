# Manager detail bank — full annotations

SKILL.md carries the compact name list; this file keeps the original per-reference
annotations (moved here 2026-10-11 to keep SKILL.md under the 100K limit).

> `references/s11-isolated-worktree-full-sprint-playbook.md` — isolated-worktree full-sprint playbook.
> `references/parallel-verify-and-prestage.md` — parallel verify, read-only pre-staging, merge-state checks.
> `references/t03-required-reading-death-pivot.md` — reading-death pivot, overlay trap, vision-vs-file, lineage, stale watchdog.
> `references/model-route-inheritance-and-mid-sprint-switch.md`.
> `references/s11c1-watchdog-terminal-marker-design.md`.
> `references/gate-calibration-and-prevalidation.md` — calibration, sweep triage, prevalidate-before-burn, hashing, live-check traps.
> `references/hermes-cli-worker-dispatch-and-owner-transfer.md` — Hermes-CLI workers, readiness, owner transfer, guards, heartbeats.
> `references/worker-ack-without-commit-and-verifier-gaps.md` — worker ack-without-commit, zero-byte TASK_SUBMITTED, $TEMP hijack, per-dir pytest (duplicate test basenames), watchdog edit-vs-running-process, model quota fallback.
> `references/correction-round-immutable-evidence.md` — per-round immutable before/after evidence roots (P2 evidence-integrity), RED-first contract-repro pattern with JSON sidecar-before-asserts, path-depth-tolerant repo-root discovery, per-round exact model proof.
> `references/structured-terminal-contract.md` — NEW (2026-10-11): structured terminal records bound to the immutable dispatch receipt (replaces prose PASS classification), controller lock + GPU lease semantics, actual-consumer test scaffold, takeover/guard cadence. Template: `templates/fake-terminal-worker.py`.
> `references/structured-terminal-records-and-consumer-patching.md` — deep measured build-out of the same adoption (verbatim patch/test recipes, 70/70 adversarial matrix detail, heartbeat closure one-tick lag, census self-match, lease watch-list for detached runners, stall-kill during a detached batch: NR-is-correct, anti-stall packet discipline, reconcile-then-resume checklist, psutil attrs-completeness false negative, stale-lease bookkeeping; **R5 v2 upgrades (2026-10-12): spawn-shape render probe (no whole-cmdline substring), RESERVED lease barrier + adopt rules, UNKNOWN-children-never-submit, stall-audit kill gate, heartbeat binding revalidation + revalidate_terminal, revision Literal r4|r5; record-first/record-last; new-Manager takeover audit w/ unanswered-prompt detection**). NOTE: overlaps `structured-terminal-contract.md` — consolidate when convenient.
> `references/byte-exact-patching-crlf-escaping-and-truncation.md` — NEW (2026-10-12): CRLF/escape/truncation-safe byte-exact patching of live harness files (open('w') truncates BEFORE validation errors → tmp+os.replace + preimage recovery; chr() escape sentinels for tool payloads; count==1 anchor proof; post-verify hash/bytes/lines). Runner: `templates/byte-exact-patch-runner.py`.
