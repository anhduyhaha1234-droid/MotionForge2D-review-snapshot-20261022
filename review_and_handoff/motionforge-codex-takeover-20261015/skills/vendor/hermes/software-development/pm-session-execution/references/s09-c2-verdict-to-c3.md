# S09-C2 verdict → S09-C3 setup (evening 2026-08-25)

Codex independent review overturned the C2 terminal: `TASK_MANAGER_VERIFIED`
became `CHANGES_REQUESTED`, corrected terminal
`BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. Review:
`docs/pm/reviews/S09_C2_PM_REVIEW_2026-08-25.md`. Six findings — each is a
manager-process lesson first, a code fix second. C3 prompt authorizes: unified
freeze v4, durable targeted regeneration, long-path READ/serve gate, canonical
hash equality.

## F1 (P0) — E2E proved the OPPOSITE of acceptance, and passed

`s09-t06bc2-only-affected-regenerates.spec.ts:315-377` built a job with a
route pin that cannot measure-pass, waited for the planner REFUSE, replayed
the old manifest, then asserted EVERY loop — including the affected one — kept
the same artifact ID/hash/size/frames. Zero-regeneration was asserted as the
pass condition; `REPORT-C2.md:27-41` narrated exactly that behavior and called
it acceptance, suggesting new-hash asserts could be enabled "later".
Production confirmed the feature did not exist: confirm endpoint committed the
correction without creating any regeneration job
(`app/api/routes/s09_correction.py:190-205`); job fingerprint omitted base
generation/correction context (`app/api/routes/s09_demo_loops.py:48-80`).

Manager lessons:
- An E2E passing proves nothing about acceptance unless you read WHAT it
  asserts. Green spec + green suite hid a missing P0 feature.
- Acceptance assertions must be POSITIVE (new generation/hash for affected
  loops), never merely "nothing broke".
- When a worker documents behavior that contradicts the acceptance criterion
  and then declares the criterion met, that IS a blocker — not a note.

## F2 (P0) — Freeze split-brain: terminal said v3, evidence said v2

J1-v3 re-hashed clean 13/13 (`b8928aeca2faedb909269372c9b08f248675b77cca835d8ae967e00cc6208a43`)
— but all six measured rows + the I05 decision still pinned v2
(`aa405015…`), and the harness had TWO other "frozen" authorities: a legacy
3-file `contract_freeze_manifest.json` (SHA `ea8ab211…`) plus prose tokens in
the C1 registry. Three definitions of "frozen", none authoritative.

C3 contract (now the template): ONE Manager-owned machine-readable manifest;
measured CLI receives the EXACT manifest path + SHA from the Manager (no
newest-scan, no fallback chain, no prose authority); verify before AND after
every run; after ANY manifest bump, grep downstream evidence JSONs for the OLD
SHA — a hit means rerun, not relabel.

## F3 (P1) — "Canonical decoded hash" was raw-concat, never cross-checked

Production canonical (`composite.py:284-293`) = frame count + ordered shape +
contiguous decoded bytes. Harness stored a raw-bytes concatenation hash in
`decoded_output_hash` and the adapter's canonical hash in a DIFFERENT field,
never asserting equality. On the real f1 artifact: raw `0ea2f331…` ≠ canonical
`4dfd4f99…`.

Manager-side trap during verification: my own "independent" ffmpeg
rawvideo/rgb24 recompute ALSO mismatched (pixel-order/packing differs). The
correct independent check feeds the PUBLIC decoder's frames through the
canonical formula — independence is in EXECUTION, not in inventing a different
serialization. C3 gate: per-row assert harness hash == adapter
`output_frame_sha256`, plus an adversarial test against raw-concat regression.

## F4 (P1) — Long-path WRITE fixed, long-path READ/serve still broken

Full 23-file suite run by Codex: `1 failed, 362 passed` (363 collected — my
registry's "356" was a stale count from before later test additions). Failure:
`test_content_serves_published_bytes_hash_verified` — completed job, real MP4
at a 272-char absolute path, GET content → 404. Writer (T03) used Win32
extended paths; reader (`app/api/routes/s09_demo_compare.py:609-628`) used
plain `candidate.is_file()` + `FileResponse` with the normal path.
Gate upgrade: explicit Windows long-path WRITE **and HTTP read/serve** ≥260
chars; both existence check and file response must be extended-path safe.

## F5 (P1) — Cross-lane findings downgraded by Manager got upgraded by reviewer

Mid-round, T06B-PREP reported CorrectionPanel omits `affected_loop_ids`
(`CorrectionPanel.tsx:363-371`) and ApprovalPanel `reasonsOf()` reads
`request.reasons`/`provenance.reasons` while route overrides store
`override_reason`/`provenance.evidence` (`ApprovalPanel.tsx:78-97`) — I logged
them as non-blocking T05B notes. Codex rated P1 because both sit directly on
the REQUIRED correction→approval flow. Rule: a defect on a required acceptance
flow is blocking regardless of which lane owns it; "not my lane" affects
routing, never severity.

## F6 (P2) — Terminal evidence hygiene failures (all mine)

- Registry terminal stamped "22:00" while `date` said 21:27 — stamp ONLY from
  actual command output, never planned times.
- Duplicate 21:30/21:35 rows from appending via two different paths (heredoc +
  patch). One entry, one append mechanism.
- "13+1" wording for a 13-file manifest; suite count 356 vs 363 collected;
  "ports free" claim while Next dev :3014 still listened (found again during
  C3 preflight, killed only after PID→CommandLine attribution proved it was
  the integration worktree's own node_modules server).
- C3 rule set: every count/hash/process claim comes from the LAST command run
  on a QUIESCENT checkpoint, with exact command + exit code logged; append
  corrections, never rewrite history.

## Post-terminal standby communication

User asked "sao thấy dừng 40m rồi?" after I went silent post-terminal. Silence
after terminal is protocol-correct but must be ANNOUNCED: the terminal message
should explicitly say the Manager enters standby awaiting Codex review and that
silence until the next verdict is expected.

## C3 setup facts (for the next session)

- Owners (resume-exact): T05A `20260824_072626_645cde` · T03
  `20260824_031524_a6bb2a` · T04 `20260824_052859_c6e197` · T05B
  `20260824_093602_af7c26` · I03 `20260823_173318_69a813` · I05
  `20260823_233406_8d5b7b` · T06B `20260824_131423_423e42`.
- Preflight 25/08 23:08: HEAD `ee10e55a…` matched baseline, dirty 104, alembic
  single head `b3c4d5e6f7a9`, DB UNSET, 0 writers; J1-v3 re-audit NONE drift.
- Registry: `docs/pm/sessions/S09-C3-SESSION-REGISTRY.md`.
- DAG: J0 (quiescence + pin J1-C3-v4 superseding v3) → Wave A ×5 (T05A, T03,
  T04-PREP, T05B-PREP, I03 measured on explicit v4) → J1 (T05A+T03 exits) →
  T04 final ∥ T05B final; I05 after I03 verified; J2 → T06B ×2 Chromium →
  Manager final gate (incl. canonical-hash equality ×6 rows, long-path HTTP
  read, rg-gate against C2/v1-as-authority).
- Key C3 architecture: applied correction → fingerprint(base_job_id +
  applied-correction context SHA + frozen evidence SHA) → ONE durable
  regeneration Job; unaffected loops reuse exact publication identity; result
  carries machine-readable per-loop generation evidence; route-override
  rejection is NOT a regeneration substitute.
