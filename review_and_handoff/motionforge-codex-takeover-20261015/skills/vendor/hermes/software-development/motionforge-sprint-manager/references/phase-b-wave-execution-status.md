# Phase B wave execution — repeating loop + live status snapshot

Companion to `delivery-takeover-20260928.md` (contract). This file is the
EXECUTION playbook as actually run on 2026-09-28, plus the measured status so a
later session can resume mid-delivery without re-deriving anything.

## The per-task loop (proven ~24×)

1. **Create worktree** from the dependency's commit:
   `git worktree add -b codex/mf-end-NN-0928 <RUN>/mf-delivery-20260927/MF-END-NN <dep_commit>`
   If the task's other deps live on other branches: `git merge --no-ff <dep_commit>`
   once per dep (transport), then
   require `git status --porcelain` == 0 BEFORE dispatching.
   Transports stay conflict-free while write-sets are disjoint; the first conflict
   of the run (MF-END-25 ← MF-END-10, 2026-09-28) was two sides ADDING to the same
   registration list in `app/workflow/job_handlers.py`. Resolution rule: keep BOTH
   additions (mechanical composition — no logic choice), commit the merge, and
   record a `transport_with_mechanical_conflict` ledger row. Locate conflicts with
   `git diff --name-only --diff-filter=U`; transport is the ONLY place the Manager
   hand-touches code, so it must be disclosed.
2. **Before-guard** (`manager/guards/MF-END-NN_before.json`): existence + bytes +
   sha256 of every write-set path; for migration-bearing tasks add
   `python -m alembic heads` (never regex-scan — see independent-evidence-verification
   ref). Launch packets get: rules pointer, measured facts the worker would otherwise
   re-discover, guard excerpt, budget advisory.
3. **Launch** via `mfv1_launch_delivery.py <packet> <worktree> <log> <receipt>`
   (add `--resume <session_id>` only for finish/relaunch of an existing owner).
4. **On exit** (never trust `exit=0`): read log tail + `git show --stat HEAD`
   (scope must equal the allowlist) + run the task's test file yourself + check
   porcelain + note disclosures. Record a ledger row; only then dispatch the next
   dependency-ready task.
5. **Two lanes max** while the Manager streams. When a finished task has several
   dependents, branch ALL of them from that same commit and run them in parallel
   (e.g. 24+26 both from 4444f8c, staggered 45 s).
6. **Session role**: `actual_session` resolved by first-message match on the
   launch packet path; record it in the ledger row at dispatch time.

## Frontend tasks: mandatory UI-convention block in the packet

The user has complained twice about dark-theme legibility. Every FE packet MUST carry:

> Mỗi nút/điều khiển dark-theme: **helper text tiếng Việt ngắn NGAY DƯỚI nút**,
> màu `text-gray-400` hoặc sáng hơn (gray-500 không đọc được trên gray-900),
> cỡ **≥11px**; chuỗi UI tiếng Việt; bám palette hiện có.

Applied in the MF-END-10 and MF-END-24 packets; treat as non-negotiable for FE scope.

## Measured status at 2026-09-28 ~20:20 +07 (ledger 144 rows)

| Task | Commit(s) | Task | Commit(s) |
|---|---|---|---|
| 01 | 3602eb2 | 13 | 4500af7 |
| 02 | af0a005 | 14 | 88ef530 |
| 03 | 44b62b3 | 15 | 9b10d1e |
| 04 | fda3df1 | 16 | a2d7cc8 |
| 05 | 2d7a328 | 17 | 29bc006 |
| 06 | 213832a | 18 | 72e3c15+bc87fa3 |
| 07 | 3844ac8 | 19 | 2dbb590 |
| 08 | 1ce1a4b+fedd33b | 20 | df4e3d4(2e403fc) |
| 09 | 07fab8a | 21 | 7cfdfa2 |
| 10 | 4d60a2f | 22 | e4cb958 |
| 11 | 8fa87b8 | 23 | 4444f8c |
| 12 | 50a50a6 | 24 | 9b8759d |
| 25 | ff1f38c | 26 | 3e37485 |

Status at 2026-09-28 ~21:40 +07 (ledger 150 rows): **26/28 verified**;
**27 running** (session `20260928_210647_069401`, base `2214b25c` = ff1f38c(25)
+ merge 3e37485(26)); **28** is the last task (←18+25+26+27) — branch from 27's
commit with MF-END-18's commit transported in.
All commits LOCAL, no push, MAIN untouched. `QUALITY_ACCEPTED=0` everywhere.

## Three 160-cap incidents — triage by WHERE the cap landed

The cap kills the turn, not the work: ALWAYS measure the disk before deciding.

- **Cap BEFORE commit** (work on disk, HEAD still = transport/base commit):
  MF-END-19 (~36 min) and MF-END-23 (55m42s) — both exited `exit=0` with
  "160/160 budget reached" and NO commit. Recovery = measure porcelain + run the
  task's test yourself → resume the SAME session with the ≤40-call finish packet
  (template at `independent-evidence-verification/templates/finish-packet.md`).
  Measured recoveries: 5m46s (19) and 3m28s (23).
- **Cap AFTER commit + evidence** (porcelain clean, REPORT.md present): MF-END-26 —
  the cap landed in the final summary turn; nothing to recover, verify normally.
- Prevention that works: the "commit + REPORT by ~110 tool calls" advisory in the
  packet (carried by the 24/25/26/27 packets; 26 committed before the cap). Keep
  BOTH the advisory and the finish-packet fallback.

## Open items to carry into the S12 review packet

- Proof findings F1–F6 (TURN f60 doubled text; book-state policy; VACE watermark;
  artwork placeholders; RAM unmeasured; research doc not on host).
- MF-END-23 O1–O5: argv escaped-length ceiling (25,001 B spawns OK / 32,501 B →
  WinError 206, ~2 KB overhead ⇒ file-based payloads); export gate wiring into
  s12_export preflight; `created_at` tie-break; 12 pre-existing red tests in
  s10_partial_recompute (disclosed by MF-END-20); lock-module cross-check.
- `lease.py:613` first-write-wins receipt defect (R27-6-F1) — routed delta, not fixed.
