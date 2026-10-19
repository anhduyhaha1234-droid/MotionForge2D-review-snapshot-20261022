# Two-Manager export wave (S12-R7, verified 2026-09-16)

Concrete record behind the SKILL.md section "Two-Manager split with a single
ownership-transfer gate". Task: `S12-R7-MANAGER-A-EXPORT` — Codex returned
`CHANGES_REQUESTED` on candidate `35f6cb2f2bd540c162d5a2f0e3ae8e152e392b86`
(base `83af5167`), F01 → VAL, F02 → RETRY, F03/F04/F05 → the *other* manager.

## Topology that was dispatched

| Lane | Owner session (existing, resumed) | Manager | Write-set | Head before → after sync |
|---|---|---|---|---|
| S12-LC3-RETRY (F02) | `20260915_201417_80e003` | **A** = `20260916_104759_1bb99d` | `app/workflow/s12_export_jobs.py`, `app/api/routes/s12_export.py`, identity sections `docs/contracts/s12-export.md`, own tests/docs | `1d9ed94` → `35f6cb2` |
| S12-LC3-VAL (F01) | `20260915_201612_6cb8a7` | **A** | `app/services/s12_export/publication.py`, lease-serialization portions of `app/persistence/s12_export.py`, own tests/docs | `535d7c1` → `35f6cb2` |
| B01 / BRIDGE / QA / INT | `…7bb91e` / new / `…aeb5e3` / `…9c9e7c` | **B** = `20260915_194636_b5ea4c` | producer, S09/S10 bridge, QA harness, Git transport | — |

A performs **no** Git integration; the sole integrator stays INT under B. Each
Manager keeps its OWN registry/output root — never edit the sibling Manager's
registry file.

## 1. Ownership-transfer gate (must pass BEFORE the first write turn)

The prompt required B to acknowledge that it no longer dispatches RETRY/VAL.
Verified, not assumed:

1. Read B's own registry: `outputs/s12-r7-two-managers/<B_UTC>/B/manager/SESSION_REGISTRY.md`
   — it contained verbatim *"RETRY … and VAL … are dispatched by Manager A …
   Manager B does NOT resume/dispatch these owners and does not touch their
   worktrees. Coordination transfer only — writers unchanged."*
2. Cross-checked B's live activity from `state.db` (read-only): B's newest
   messages were B01/QA/BRIDGE/INT guard+snapshot work, i.e. **no** RETRY/VAL
   dispatch. B's registry table listed only its own four lanes.
3. Recorded A's actual session id in A's registry for the user to bridge back
   (A must not write into B's file).

Gate result: A's write turn authorized. Without step 1+2 you can end up with
two Managers driving the same writer.

## 2. Finding your OWN session id (when the chat has no handle for it)

Dispatch payloads land in the DB under the *persisting* session:

```sql
SELECT rowid, session_id, role, substr(content,1,80) FROM messages
ORDER BY rowid DESC LIMIT 8;                       -- who is writing right now
SELECT rowid, role, substr(content,1,100) FROM messages
WHERE session_id='<candidate>' ORDER BY rowid;     -- is this really me?
```

A same-day probe session (`…105044_548d88`, user text `Reply exactly: R7_PROBE_OK`)
looked like a candidate; its content proved it was only a route smoke test. The
session whose rows held *this* session's own tool results is the identity.
Also read each owner's LAST message rowid vs the global `max(rowid)` to prove
"idle": `ended_at = NULL` proves nothing about liveness.

## 3. Byte guard recipe (allow + protected + snapshots, per lane)

`docs/pm/tools/write_set_guard.py capture` per lane, one manifest each; the
driver script expanded directory entries to explicit file lists and recorded
`missing_*` (files that arrive only with the sync). VAL had an untracked
`work/` (58 files, 1.2 MB) that had to survive the whole wave → captured as
byte-for-byte snapshots via `--snapshot-dir` (the tool fails closed if any
snapshot hash ≠ source hash; it did not). Counts: RETRY 35 entries
(25 allow / 10 protected), VAL 116 (47 / 11 / 58 snapshots). `ruff` counts and
hash sets were NOT treated as the guard; only the tool's CAPTURED/VERIFIED is.

Post-sync and post-writer `verify` must run with `--allow-change` limited to the
lane allowlist; `destructive_shrink` = stop the writer immediately.

## 4. Wave-base sync proved conflict-free by construction

```bash
git merge-base --is-ancestor <lane_head> <candidate> && echo ANCESTOR_YES
```
TRUE for both lanes ⇒ the sync is a pure fast-forward, so no 3-way merge and no
conflict resolution can ever be needed (and `reset/clean/stash/rebase/force`
stay forbidden). The ff itself is run BY THE WORKER inside its own worktree,
not by the Manager.

## 5. Simultaneous upstream 502 (both lanes at the same second)

Both owners died mid-turn at `04:41:43Z` with
`API call failed after 3 retries: HTTP 503: [<route>] [502]: fetch connect timeout`
— temporary connection class ⇒ `RUNNING_RETRY_WAIT`, **not** terminal, and the
3 internal retries are explicitly not a terminal state.

Per-lane audit before resuming (do NOT assume both lanes need the same redo):

| Lane | Head after failure | Meaning |
|---|---|---|
| RETRY | `1d9ed94` (unchanged) | ff-sync never ran — resume must redo it |
| VAL | `35f6cb2` (moved) | **ff-sync had already completed** before the drop — resume only verifies it (`git merge --ff-only` → `Already up to date`, a no-op) and must NOT replay it destructively |

Then: report immediately → wait a full 5 minutes from the failure timestamp →
audit the gateway (`curl -s -o /dev/null -w '%{http_code} %{time_total}' …/v1/models`
×3 plus an exact-id membership check) → resume the SAME owner/model/provider/
api-mode/thinking/scope with `--resume <exact sid>`. Fallback stays OFF; no model
substitution; no new session for the same Task ID.

Guard against a stale completion notice: the OLD turn-1 wrapper's
`notify_on_complete` fired ~30 min late and looked like a fresh lane death.
Triage by reading the notifying process's OWN log (`turn1_run.log` vs
`resume1_run.log`) and by re-measuring lane state — never by the notice alone.

## 6. Turn structure that satisfies the "gate before code" rule

Turn 1 per lane (no production/test writes at all):
(a) ff-sync to wave base, (b) context-health audit, (c) re-read the exact
authority files for this finding, (d) **submit the finite INVENTORY** — exact
executable node IDs, parameter IDs per variant, expected typed status + all-row/
file deltas, new-vs-existing nodes, raw output destinations.

The Manager freezes that inventory into coordination docs before any code turn,
so an owner can never shrink the node set later. Inventory submissions are also
where you learn a node/file must be NEW — which is when you can still enforce
"new file must be proven absent".

## 7. Route/model readiness evidence kept for the reviewer

`GET /v1/models` → 200, 145 ids, exact `ocg/deepseek-v4.1-flash` present (the
near-miss ids `ocg/deepseek-v4-flash`, `ocgfree/deepseek-v4-flash`,
`cmc/deepseek/deepseek-v4-flash` are ALSO advertised — which is exactly why
`-m/--provider` is pinned on every dispatch and resume). Provider used:
`providers.custom` = 9Router `http://127.0.0.1:20128/v1` with **no `api_mode`
key** ⇒ OpenAI-compatible `chat_completions` (the sibling entries carry
`api_mode: codex_responses` and were excluded). No `fallback*` key anywhere in
`config.yaml` ⇒ fallback OFF by construction. One live end-to-end probe through
the real launcher returned the exact token, exit 0.

## 9. Completion half — freeze, independent verify, handoff (same wave)

The wave finished 5h39m inside its buffered ETA (commit `4ce3b136` RETRY 3 files
+421/−27, `86b1a2a4` VAL 8 files +1427/−4). What the second half required:

1. **Re-capture the guards AFTER the ff-sync, before any code turn.** The
   pre-sync manifests are stale at the new wave base: protected files that
   legitimately changed with the sync would report `protected_file_changed`. Capture
   a `*-postsync-manifest.json` per lane (same file lists, snapshots re-taken) and
   `verify` it against itself → `VERIFIED 0 failures` is the authoritative baseline
   for the post-writer check. Allowance lists are then the lane's own committed paths.
2. **Verify the owners' claimed hashes yourself before freezing.** Every hash the
   two owners reported (inventory .md/.json, lane files, reviewer probe) was re-hashed
   from disk and matched — cheap, and it converts a self-report into evidence.
3. **Prove new files are absent in BOTH lanes** before allowing whole-file writes
   (`test -e` over each proposed path ×2 worktrees). Do this at freeze time; afterwards
   it is unprovable.
4. **Run your own verification in an isolated runtime**, not the worker's: private
   TMP/basetemp, `S12_*` env cleared before import, and reviewer probes copied
   **from the review root** — never from the worker's copy (a worker copy could have
   been edited). Assert the probe's sha256 before AND after the run (identical before
   and after = no test-authoring during the gate). Result here: RETRY 58/58 + 97/97,
   VAL 44/44 + 95/95, 0 failures, 0 new skips.
5. **Gate-1 harness trap (cost one exit-4):** a reviewer probe may
   `import test_publication as base` from a SIBLING test directory. `PYTHONPATH`
   must include that sibling dir (`tests/s12/s12-t03c`) as well as the lane dir and
   the repo root, or collection fails with
   `ERROR: found no collectors … ModuleNotFoundError: No module named 'test_publication'`
   (pytest exit 4). This is a HARNESS defect, not a product finding — fix the
   PYTHONPATH, re-run into a FRESH `S12_REVIEW_OUT` (probes write with mode `'x'`),
   and keep BOTH the failing stderr and a `…CORRECTED.NOTE.txt` in the same run dir.
6. **Never feed a non-Python file to `py_compile`.** A changed-file list containing a
   `.md` yields `SyntaxError: invalid character '—'`. Gate static checks per file type
   (`ruff --select F` + `py_compile` for `.py` only) and record the harness correction.
7. **Owner stray-path incident → triage, don't escalate blindly.** VAL mis-resolved a
   write path, created `C:/Users/Admin/app/...`, deleted it in the same turn and
   disclosed it unprompted. Correct response: after the writer exits, verify the stray
   is gone, verify no existing file was destroyed, verify the real artefact is committed
   in the worktree, then classify as *non-destructive disclosed scope deviation* — one
   such deviation does not justify owner replacement (a second destructive/out-of-scope
   violation in the lineage would). Also verify the owner honoured the protected half of
   their file: grep the diff of the shared file for the other lane's terms
   (`lineage|identity|orphan|sibling`) → zero added lines proves the split held.
8. **No-active-writer evidence must be a settled measurement, not a timestamp:** sample
   lane HEAD + porcelain + per-owner last-message rowid twice, 25 s apart, and require
   all three unchanged, plus absent launcher processes. State explicitly that
   `ended_at = NULL` is not liveness proof.
9. **Close out with a machine-readable handoff, not prose.** `EXPORT_HANDOFF.json`
   (base, exact commits/ranges, per-file allowlist check, guard results, finite
   node/raw results, no-active-writer block, limits, `fact_corrections_recorded`,
   incidents) + `NEXT_REVIEW_PACKET.md` for the user to bridge to the other Manager.
   Include the limits verbatim: no broad/global gate (other Manager's license), no
   media/UI/playback claim, and the exact findings left open elsewhere.
10. **Record your OWN wrong assumptions as fact corrections.** My pre-freeze read that
    the typed-error mapping lived in `routes/s12_export.py` was refined by VAL's
    measurement (the real claim path is the durable-worker classifier, and the route
    mapping is submit-path only). The frozen mandate survived because it was strictly
    compatible — but the correction is written into the handoff so the reasoning is not
    overstated to the reviewer. Harness defects and owner incidents stay in the same
    run directories rather than being cleaned away.

## 10. Reporting shape the user accepted for "bao giờ xong"

Lead with measured status (what is done / what runs now / what has not started),
then an ETA table anchored to the current `+07` clock with plan vs buffer
columns, then — mandatorily — a *"đã trượt"* section naming the ETA previously
promised, the concrete cause (here: 502 kill + turn-1 redo = ~+1.5h), and why it
is a **time** slip and not a quality slip (0 production files written, 0 partial
patches, guards not failed, untracked `work/` intact). Close with remaining
risks already inside the buffer. Do not wait to be asked for any of it.
