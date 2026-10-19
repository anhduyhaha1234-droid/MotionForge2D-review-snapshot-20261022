# R6 GATE RESTATEMENT — LONG01-R6-20261012T0810Z-2731

Written BEFORE any mutation, per packet §1. If any item below were unstatable, the rule is
STOP + CONTINUE_REQUIRED with the blocker — not guess. All statements restated in my own words
against: manager/packets R6 §1/§3/§6, O/REVIEW_VI.md (R5-F01..F09, T-F01..F06), N/TECH_CONFORMANCE_MATRIX.md
(T01–T15), O/TECH_DECISION_VI.md, O/CORRECTION_MATRIX.md (Q01–Q12).

## A. GATES (what must block, and where)

1. KEY gate (before ANY propagation):
   - Every key must be backed by an artifact-bound SEMANTIC REVIEW record: reviewer id, review
     output hash, input lineage (source span + frame map + cast refs used + masks used + graph hash +
     model/settings hashes), expected actor set / roles / contacts for that frame, and the final-frame
     evidence inspected. Absent / stale / tampered / UNKNOWN review ⇒ BLOCK.
   - Expected actors come from the SOURCE LEDGER (source), never from output or from a previously
     wrong ledger. Visible actor whose mask is missing or empty ⇒ FAIL (never silent passthrough).
     NaN/invalid candidates ⇒ FAIL, never publish. Key showing wrong pose / count / role ⇒ REJECT
     before propagation. Zero-actor frames only when the ledger says ZERO_VISIBLE explicitly.
   - Actor edits are per-actor from the source pose/view; front+profile refs are the SAME ID and must
     remain reachable in EVERY branch (normal/repair/fallback). Actual-ref perturb test: the target
     actor's appearance changes, neighbors/props do not.
2. PROPAGATE gate (Rerender = stage 2 `video_blend` adoption ONLY — no stage-1 claims):
   - Event keys must be consumed at their EXACT source times (no nearest-grid snapping, no dropped
     events); internal ranges split at approved event/cut boundaries; exact endpoints and seams checked.
   - Engine rc != 0, partial runs, or stale outputs ⇒ BLOCK; no tail-fill to fake completion. The
     wrapper must verify FRESH COMPLETE valid outputs even when the outer process rc=0 (upstream
     video_blend does not propagate inner EbSynth failures; local VideoSequence rounds end to grid).
   - Flow/EbSynth caches are namespaced by CONTENT dependencies (source/guide/mask/model/settings
     hashes), not by path existence; changed bytes at same path/size invalidate the correct descendants.
3. ASSEMBLE gate (before the encoder):
   - Verify the reviewed artifact hashes (keys/blends/reviews) BEFORE encoding; missing/invalid ⇒ no
     resample/duplicate/drop to reach counts. 9000 frames, 30fps, 640×360, 300s; audio = source
     [94,394)s exactly; correct PTS, cuts, full AV decode; head/mid/tail lag measured.
4. SUBMIT gate:
   - Matrix = exactly Q01..Q12, PASS only with real proof (source/function/test/command/owner +
     expected counts + output hashes); UNKNOWN blocks; no residual P1 may be moved out of
     remaining_work to force PASS. Record at C/r6/evidence/terminal/<invocation>.json, schema below.
5. CACHE CONTRACT (R5-F05/R5-F07 / T07):
   - Cache key = exact consumed bytes of source span, refs, view, masks, graph, model, settings and
     approved-key hashes. Same-path/same-size mutation must invalidate exactly the right downstream;
     unchanged inputs may reuse only after a verified control. No exists-only skip logic.
6. RECORD SCHEMA (packet §6) + RECORD-LAST:
   - schema_version "1.0"; run_id "20261005T1643Z-wan-long"; task_id "MF-DEMO-LONG-01"; revision "r6";
     owner_sid "20261007_234033_cc0b6d"; invocation_id "LONG01-R6-20261012T0810Z-2731";
     packet_sha256 "aa17a4d4185c6c1d76c9a6208284b9c31a38cbcab1b3ff96a371e542f2045933";
     status ∈ {CONTINUE_REQUIRED, TASK_SUBMITTED, USER_STOP, BLOCKED}; remaining_work empty ONLY for
     TASK_SUBMITTED; artifacts = [{kind ∈ master/comparison/matrix/checkpoint/receipts/other, absolute
     path inside C/r6, fresh sha256}]; matrix exactly 12 keys. ≤1MB, no duplicate keys.
   - RECORD-LAST: the terminal record refresh is the FINAL write of the invocation; every artifact
     hash is recomputed after all writes stop; if anything writes after a record, the record must be
     refreshed again before stopping. Manifest is regenerated immediately before the final record so
     its pinned hash is fresh; no write may follow the record.
   - TASK_SUBMITTED only when 12/12 rows PASS with real proofs + exactly one kind of each
     master/comparison/matrix/checkpoint/receipts + remaining_work = [].

## B. INVARIANTS (do not break)

1. Fallback/repair keeps CAST refs reachable (traceable from sampler to each used CAST loader).
2. Visible actor with missing/empty mask ⇒ FAIL before model; never passthrough.
3. Zero-actor must be EXPLICIT: ZERO_VISIBLE (source-confirmed) ≠ missing data; UNKNOWN blocks.
4. Source-copy ≠ reskin; file existence / hash match ≠ quality.
5. One UNKNOWN entity does not exempt a shot's known actors; only the unknown entity is exempt.
6. All outputs (masks/tracks/receipts/caches/keys/media) go under C/r6/** or
   D/{input,output,temp}/identity5m_20261008/r6/** — nothing else; R4/R5 are strictly read-only.
7. Canvas contract: canonical source canvas 640×360; pad 4/4 → 368 applied ONCE with explicit
   inverse; every image/mask in a pipeline must share shape/time; source frame0 → f0001, NO 1-frame
   shift; no positional fallback for missing masks; no implicit mask substitution.
8. Rerender adoption = stage 2 only; VACE = official reference-v2v graph with TrimVideoLatent
   (KSampler→TrimVideoLatent.samples, WanVaceToVideo.output3→trim_amount, TrimVideoLatent→VAEDecode);
   no "trim 4 decoded frames" workaround.
9. Semantic review must attach to the FINAL bytes; pixel correlation, file count or a handwritten
   matrix is not a review; Manager holds the held-out visual QA; no self-approval.
10. No new framework/core; no training; model/settings pins stay; GPU1 sequential; measure real
    peaks (allocated/reserved/process-tree/sampled separately); no seed sweeps; after two failed
    attempts of the same method, change method from evidence.
11. Do not claim docs/clone/unit-test as quality PASS: technology chain verdicts are graded
    SOURCE_READY < ENV_READY < SMOKE_PASS < SOURCE_UNIT_PASS < PILOT_PASS with actual consumers.
12. RECORD-LAST; QUALITY_ACCEPTED=0; worker never calls APPROVED/CLOSED.

## C. Scope guard

Write-set: C/r6/** + D/{input,output,temp}/identity5m_20261008/r6/**. Read-only: R4/R5 (incl R4
tracks — T-F01), W7/C1/C2/R3, source/style/CAST board, MAIN, INTEGRATION, reviewer packets, manager
frozen evidence. Incident evidence reconciliation (F08) belongs to Manager; worker must not touch it.
