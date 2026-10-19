# Structured terminal recheck — verify the record from bytes yourself (2026-10-11)

When a worker's outcome is a structured terminal record bound to an immutable dispatch receipt
(see `pm-worker-orchestration/references/structured-terminal-contract.md`), the Manager must
RE-VERIFY, not trust the dispatcher's cached verdict:

1. Re-run the validator on the record FILE bytes (not on the receipt's cached
   `terminal_validation`), with the expected binding rebuilt from the append-only ledger row.
2. Recompute every artifact sha256 in the record and compare; assert every path is under the
   allowed root and is not the record itself.
3. Check reconciliation: child process identity gone (psutil pid+create_time), GPU lease
   released-or-detached-consistent, and the heartbeat row agrees with the record status.
4. `quality_accepted` is always false — a validated TASK_SUBMITTED is eligibility for Manager
   QA, never acceptance. The prose classifier output (`legacy_prose_outcome`) is a reference
   field: keep it, never let it decide.

Claims to distrust by default (each measured in the field):

- "exit 0" — context exhaustion, API batch failures and turn-budget yields all exit 0.
- A prose token anywhere in the log — plan/future/quoted/negated lines contain status words
  ("after gates -> PASS", "not PASS now"); only the record is a verdict.
- "evidence not available" — locate the exact path on disk before believing it; a required
  Manager-owned file may exist OUTSIDE the worker's allowed root and simply needs to be copied
  into the worker's root (kind `other`, hashes recorded) before the submission window.
- A registered controller SID — the actually-dispatched controller can be a DIFFERENT session
  (user opens new chats). Reconcile registered-vs-actual via message history (first user message
  marker in the read-only session DB), receipts and process identity; find your own SID by
  searching the DB for your prompt marker; record the takeover with a registry preimage.
- "no writer active" — prove zero-writer at multiple layers: newest write mtime on disk
  (compare epochs, not wall-clock strings), process identity (psutil pid+create_time, never a
  bare pid), and the render queue (Comfy /queue). Heartbeat rows alone are not proof.
