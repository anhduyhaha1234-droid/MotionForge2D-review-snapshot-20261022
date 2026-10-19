# R6 CHECKPOINT — appended R6b (LONG01-R6b-20261012T0825Z-1d8c)

## R6b done (invocation #2)
- Seeds: 7 vision sheets (26 shots) + fix sheets (S31/41/57/62/63/67/73/21/70) -> r6_sam2.SEEDS extended
  (all entry-aware: S61 @103, S62 E1/E2 @31, S31 E2 @19, S41 E2 @29, S21 E4 @42, S57 E1/E2 @0).
- SAM2 R6 masks: 36 shots main batch + fix reruns. Bugs found&fixed WITH evidence:
  * start_frame min-bug (falsy 0) for mixed seed frames -> 2-pass group mode (R6_GROUP=base|late);
  * SAM2 dtype crash on mixed-frame prompts (bf16 mat mismatch) -> grouped runs;
  * validation now LEdger-wide (ledger-visible actor w/o seed = violation; was silently passing);
  * S70 E2 reclass PARTIAL->FULLY_OCCLUDED (fresh vision f1+f60: not visible);
  * S57 visible window measured by SAM2 = [1..96] (tail zero), ledger updated.
  Final mask state: ALL 37 people-shots 0 violations (S43 EXCLUDED - SAM2 1078f collapsed to 4.6s/it;
  killed at 284/1078 to protect the batch; S43 mask strategy = 2 chunked passes - next invocation).
- Keygen batch (36 shots, no S43): 507+ keys via upstream crop+stitch path; prompt delta v2 applied
  (background immobility emphasis). Fixed mid-flight: cache graph=None for keep_source frames (crash at
  S57 f101/S61 f1); bound_check refined with measured bars (core8/24 margin; real leaks 0.3+ still block).
  Remaining gaps at 11:36Z: S28(16) S27(14) S64(4) S61(23) missing fids = transient Comfy URLError;
  retry runner (health-check + backoff 5m) launched 11:37Z.
- S27 f1 checked through refined bounds: frac_core8 0, leak-free (max_out 0.037 = resampler band).

## Next (resume same SID)
1. Confirm retry runner closed the 4 gap shots (receipts/R6_KEYGEN_RUNS.jsonl); S43 masks via 2 chunked
   SAM2 passes (frames 0..538 / 538..1077 re-seeded from chunk1 last mask centroids).
2. Vision semantic reviews for keys (sheets of 8-12 keys/shot, gross-error focus: extra person, wrong
   role/count, identity absent; rim/pose spot-checks) -> r6_gate.write_review per key (batch), then
   gate_shot_before_propagate unblocks. Quality loop queue: rim-bleed (bbox-edge redraw), pose-turn.
3. S4 VACE rebuild with TrimVideoLatent + paired S62/S73 vs keys + actual-ref perturb; S5 decision.
4. S6 propagation event-aligned (fresh-complete check, no tail-fill) + CoTracker paired S34/S61/S73
   (tracks+visibility raw). S7 excerpts + zero-shot asset reskins (S32/35/37/40/42/45/47/49/50/52/54/58/59/60/65/66/74).
5. S8 master + comparison source|R5|R6 + QA; S9 matrix/evidence/manifest; record.


## R6c append (LONG01-R6c-20261012T1215Z-8e2b)
- Record naming FIX acknowledged: this invocation writes evidence/terminal/LONG01-R6c-20261012T1215Z-8e2b.json ONLY.
- S61-tail DONE (36/36 keys; NoneType was transient, retry wrapper). S43 chunked SAM2: chunk1+chunk2 (2-chunk auto re-seed) + keys chained.
- Keygen quality bug hunt: E4/E5/E2 masks were WALL-BLOBS (seeds on background from approximate sheet reads; e.g. S27 E2 88k px wall).
  Vision-confirmed via solid-red overlay sheets -> 6 shots reseeded (S21 E4, S27 E2, S28 E4/E5, S31 E2 f60, S44 E2, S64 E2)
  -> SAM2 rerun -> keys regenerated (13:11-14:00Z). S27 v2 spot-check: bulk garbage CLEARED; residual tail f101-159 -> repair queue.
- Keygen hardened: z-order mask subtraction (later actor cannot re-edit pixels claimed by front actor); bound_check bars
  re-calibrated with measured evidence (resampler-band outliers soft-flagged to review, real leaks 0.3+ still hard-block).
- Reviews: 30/36 shots reviewed (12-key even-sampled sheets, per-key verdicts) -> receipts/R6_REVIEW_RESULTS.json.
  6 pending (S67/S69/S70/S71/S72/S73) due to vision throttling. Repair queue concentrated: single-key pose/face fails,
  outfit flickers, S41 E2 presence UNKNOWN.
- S4: r6_vace.py (TrimVideoLatent contract: KSampler->Trim.samples, output3->trim_amount, Trim->VAEDecode) built;
  S73 base + S73 actual-ref-perturb + S62 window [32,112] runs launched (r6/receipts/R6_VACE_RUNS.jsonl).
- TODO next: complete reviews + write per-key review records; repair queue; S5 decision; S6 propagation+CoTracker; S7-S9.


## R6d append (LONG01-R6d-20261012T1435Z-f304)
- Record FIX: writer dedupe enforced + name==invocation_id assert (R6c dup path lesson).
- Reviews COMPLETE: all 36 shots reviewed; per-key records written; ~450 PASS / ~70 FAIL-flagged entries in total across rounds (reviews/keys/*.review.json).
- REPAIRS round-1 (ctx1.15+seed7, 50 fids): 47/50 OK on re-review (sheets REPAIR_1..4). Residual: S62 f33, S69 f101, S72 f71 = round-2.
- v2 keys verified for S21 (f61/f96 still bad), S27 (tail f101-159 residual), S28 (f131/f143 giant head), S31 (E2 window), S44 (unreviewed), S64 (ALL OK).
- S5 DECISION written: keys-route SELECTED; VACE NOT_SELECTED (reason: multi-role identity weak S62) + validated alternative (S73 perturb proof: ref-binding works, neighbors/props kept). receipt R6_S5_ENGINE_DECISION.json.
- S6 propagation RAN: r6_propagate.py built with fresh-complete/no-tail-fill/BLOCK gates; GMFlow fix = frames pad 368 (div by 16) with explicit inverse at assembly. Batch 35 shots: 27 rc=0 clean, 8 blocked by review gate (documented). S63 smoke 36.4s; batch done 15:45Z.
- Next: repair round-2 -> re-review -> propagate blocked 8 -> S7 zero-shots -> assemble/QA -> S9 record.


## R6e append (LONG01-R6e-20261012T1555Z-3e9b)
- S21 E4 FIXED: neg-prompts on wall -> person-scale masks (3.9-4.6k px) -> keys regen -> strip verified (giant-head gone).
- S31 false-alarm corrected: strip vs source shows KEY faithful (prompt-expectation artifact); 7 fids -> PASS.
- r2 repairs (12 fids S27/S28/S62/S69/S72 + S21/S31 full): re-review 10/10 OK (S28 f131/143 verified vs source).
- S43: full delta regen (38 fails -> R2 re-review ~clean); f821/f841 recheck (f841 pose note); records rebound after race audit (29 missing filled incl S61).
- S44: repair 4 fids; f31/f51 outfit note.
- ASSET pass: 17 zero-shots whole-frame restyle w/ text-preservation prompt; 4 review sheets: text legible (S42/45/47/49/50/52/54/58/59/60/65/66/74 + S35/37/40 phone UIs + S32 with black-passthrough); S32 f561 regen.
- PROP batches: batch1 27 shots rc=0; prop_r2 6 shots rc=0 (S21/27/28/62/69/72); prop_r3 S31/S44 rc=0, S43 rc=1 (race->retry queued); prop_asset running (S32..S60 rc=0; tail S65/S66/S74 + S49 retry).
- CoTracker: weights = r5/models/co-tracker (reuse); S34 T=214 drift 0.91px; S61/S73 running.
- r6_assemble.py + r6_qa.py + r6_matrix.py built+compiled; wait for blends to run.
