# S12-R7 two-manager split + Manager-B activation playbook (2026-09-16)

Context: R7 review of `35f6cb2` = CHANGES_REQUESTED with 5 findings split across TWO Managers —
F01 (stale-lease creates final) + F02 (combined-identity duplicate Job) → Manager A with RETRY/VAL;
F03 (producer fabricates source timing) → B01; F04 (S09↔S10 authority bridge) → a NEW cross-sprint task;
F05 (C02 overclaim) → QA + Manager-B's own matrix. Candidate `35f6cb2f2bd540c162d5a2f0e3ae8e152e392b86`
stays the local immutable wave base for EVERY tree (explicit exception; no push anywhere).

## Split semantics (coordination transfer — NOT writer replacement)

- Manager B = the EXISTING manager chat (resumed with a new coordination Task ID, e.g.
  `S12-R7-MANAGER-B-PRODUCT`). Manager A = ONE new Manager chat for export corrections.
- The user activates each prompt independently; the proposal asks for B FIRST so it can record the
  relinquishment before either owner gets a write turn. A user message delivering the prompt IS the
  activation — execute; do not wait for a second go signal and do not re-ask.
- B's registry must state verbatim: RETRY `<sid>` and VAL `<sid>` are dispatched by Manager A from this
  wave; B does NOT resume/dispatch them and never touches their worktrees. Record A's actual session id
  when the user opens chat A (can stay PENDING for a while without blocking B's lanes).
- B keeps exactly: B01 + the new BRIDGE + QA + the SOLE INT. "Manager A never merges; B never commands
  A's writers." No second integration worker.
- Cross-manager data link = ONE immutable handoff file (A writes `EXPORT_HANDOFF.json`: base, exact
  commits/ranges, guards, finite results/raw hashes, no-active-writer evidence). B consumes it via the
  user bridge OR an explicit one-shot local read during active work. No watcher, no auto cross-task
  messages, no scheduled polling.

## Activation checklist (proven order, ~10 min wall)

1. Full rules load from the FILE (never memory) → report `RULES_LOADED` with path + line count + bytes +
   sha256 + ACTUAL HEADs (main + every relevant worktree/branch with dirty counts) + section list.
2. Read the packet docs IN FULL: REVIEW.md, SHARED_CONTRACT.md, ACCEPTANCE_R7.md,
   SESSION_OPENING_PROPOSAL.md, MATRIX_REVIEW.md, MANAGER_<x>_PROMPT.md (+ HANDOFF/ROADMAP/SESSION_PROTOCOL).
   Verify the user-pasted prompt matches the prompt FILE (line count + spot check) — paste drift is real
   and the file footer may carry the activation condition the user quoted.
3. Verify Manager identity + route LIVE: tiny `hermes chat -q "Reply exactly: PROBE_OK" -m <route>
   --provider custom -Q`. Catalog/state rows/prompt text are NOT proof of successful inference.
4. Fresh roots per activation: evidence `outputs/<packet-family>/<uniqueUTC>/B/<lane>/` + runtime
   `work/<family>/<shortUTC>/B/<lane>/`. Persist both in an `00_run_context.txt` AND a scratchpad note —
   compaction will otherwise lose the timestamped paths.
5. Registry (`B/manager/SESSION_REGISTRY.md`): split section + per-lane table
   (Task ID | session | status | worktree/branch | exclusive write-set). Statuses PREFLIGHT → DISPATCHED
   with proc ids, updated as each lane fires.
6. Guard one-pass per lane BEFORE dispatch: `guard-allow-pre.json` + `guard-protected-pre.json` + byte
   snapshots of the changed-set critical files (verify snapshot hash == source hash). B-lane protected
   sets must include the OTHER manager's lane files (publication.py, s12_export_jobs.py, RETRY/VAL test
   files) so accidental cross-lane writes are detectable.
7. Sync ONLY B's existing task branches to the wave base: `git merge --ff-only <wave-base>` inside each
   B worktree (B01 + QA were ancestors of the tip → clean, dirty=0). NEVER sync or touch A's lanes.
   Sync BEFORE guard capture — guards must baseline the exact post-sync tree the workers will edit.
8. Create the NEW task worktree only after an absence check: `git branch --list <branch>` (must be empty)
   then `git worktree add -b <branch> <path> <wave-base>`. If the Task ID was already assigned a
   worktree/owner, RESUME that owner — never recreate/overwrite.
9. Write per-lane prompts: finding text with exact file:line; acceptance rows verbatim; write-set allow +
   protected; evidence/runtime paths; patch-only rule for existing files; gates + COMMAND_LEDGER; commit
   message; closer "không hỏi lại — execute".
10. Dispatch all dependency-ready lanes in ONE batch (background + notify_on_complete): resumes use
    `-r <owner-sid>`; a NEW task gets a fresh `hermes chat -q` (its session id lands in the console/
    registry). Arm the heartbeat collector in the same turn.
11. Heartbeat for this wave: per-family PS1 appending per-lane console size/mtime + live `chat -q` proc
    count to `B/manager/HEARTBEAT.md`, launched as `sleep 1140; powershell -File ...; echo DONE` bg loop
    and re-armed each cycle (desktop chat cron does not deliver).

## Lane-specific R7 notes

- **B01 (F03):** producer must prove source rational timing (frame count + rational FPS + CFR) from
  persisted authoritative probe/artifact facts; missing numerator/denominator or zero duration → typed
  409/422 with ZERO manifest/route rows. No `fps or 30` / `den or 1` / `max(1, round(duration*fps))`
  defaults. Keep B01-A–H green + B01/B02 acceptance rows (supersession, CAS one creator, rollback).
- **BRIDGE (F04):** exactly ONE new session. Phase 1 = `CONTRACT.md` ONLY (scene shots = disjoint
  contiguous partition of the full source timeline; occurrences = active layers that may overlap;
  explicit inclusive/exclusive frame conventions; global vs scene-local coordinates; immutable global
  shot bounds; layer identity + repeated-role distinct ranges; geometry requirements incl. points-only
  typed ineligibility; fail-closed reason codes; legacy checkpoint classification) → freeze with
  Manager+QA BEFORE any production write. Production allow-list = s09_approval.py, s10_full_apply.py,
  s10_chunk_plan.py, workflow/s10_full_apply_jobs.py (+ optional new timeline helper + own new tests).
  The `_stitch_verified_chunks` range-dedup must become real layer composition with decoded-frame
  evidence of every visible layer (B06) — dedup is not composition.
- **QA:** preparation can run alongside disjoint writers. Q01 = correct obsolete matrix/report claims
  (C02 preflight NOT_REACHED etc.); Q02 = bounded T03A migration-TEST compatibility exception
  (separate target revision `c3d4e5f6a7b8` from current sole head `d4e5f6a7b8c9`, both linear edges,
  retained data/FK/Job lineage, NO blind NEW_REV replace / dynamic head assert / xfail); Q03 = configure
  the R5 audit env (`S12_R5_CANDIDATE_ROOT` + `S12_R5_EXPECTED_CANDIDATE_SHA`) with exact real values
  documented for the Manager to export in global gate commands — without weakening provenance asserts.
- **INT:** standby until all input owners terminal + verified (+ A's handoff). Preferred transport order
  VAL → RETRY → B01 → BRIDGE → QA. Local transport is never approval.

## Pitfalls seen this round

- Legacy HANDOFF/ROADMAP snapshots are S11/PLANNED-era — expected drift; the current review decision
  supersedes for the authorized scope only. Note the drift in the registry; do not block dispatch on it.
- `git worktree add` mutates the MAIN repo — run it as ONE plain command (approval-safe), then verify
  clean + `HEAD == wave-base`; keep manifest generation in separate non-mutating calls.
- B01-style foreign-owned worktrees (`.git` owned by another sandbox user) need per-invocation
  `git -c safe.directory='*'` on every git call — bake it into prompts and scripts for that lane.
- When the user says the prompt runs "khi người dùng kích hoạt": treat a user message that delivers the
  full prompt (with the activation footer) as activation and start the checklist immediately — the
  first mandatory deliverable is the RULES_LOADED attestation, then execution ("Execute the work, not
  another plan").

## Post-activation rounds, same day (freeze + QA turn-2 + 502 wave 2)

- **BRIDGE phase-1 closed at `3963d31`** (CONTRACT.md 439 lines + LOG, docs-only, guards allow 4/4 +
  protected 18/18, zero production writes). Its first turn died at the REPORT step (502) — the resume
  "write the report only" landed cleanly; wrapper EXIT=0 + commit + clean tree = phase done.
- **Freeze procedure proven (Manager rulings → QA co-signoff → production):** Manager wrote
  `B/manager/BRIDGE_CONTRACT_FREEZE_REVIEW.md` = ACCEPT + per-Q rulings (Q1 REVISED by acceptance row:
  draft "pick boxes[0] + provenance" contradicted ACCEPTANCE B04 "**ambiguous** boxes honestly
  ineligible" → within-key >1 differing box ⇒ `OCCURRENCE_GEOMETRY_AMBIGUOUS` typed deny; cross-key
  keeps documented precedence; Q5 tie rule deterministic `z_order`→`(logical_id, lineage_version)` with
  NO ambiguity denial so B03 multi-occurrence proceeds; Q7 legacy v2 → public reapproval, bytes never
  backfilled). QA sign-off turn = ONE bounded dispatch with named outputs: Q1-cross-key/Q2/Q3/Q7
  confirmations (or precise pushback), Q9 exact per-layer decoded-evidence sidecar format, D2 B03–B06
  node mapping ("to be frozen by owner" for not-yet-existing nodes).
- **QA turn-2 submission `666dc5e` verified** (6 files +458/−36): Q01 claims fix (C02 NOT_REACHED),
  Q02 T03A migration-TEST compatibility — the 4 stale-head failures now GREEN (Manager re-run: 25
  passed for inventory+prep files + FULL t03a module, incl. `test_single_head_is_new_revision` etc.;
  separate target revision vs current sole head, both edges, no blind NEW_REV replace), Q03 R5-env
  documentation, R7 inventory + `test_r7_prep_inventory.py`. Verify shape: inventory+prep files + FULL
  t03a module + ruff + guard — never the expensive chain node.
- **502 wave 2 (same day):** both resumed lanes died AGAIN ~11 min in (both `RESUME1_EXIT=1`, same
  upstream fetch-timeout). Liveness probe itself TIMED OUT (240s) while local `/models` stayed HTTP 200
  (0.11s) → local gateway up, upstream completions flapping (~15–20 min cycles). Manager waited another
  full cycle, probe OK (`R7_PROBE4_OK` 12:25:54), then wave-3 resumes appended to the SAME consoles with
  `RESUME2_EXIT=$?` markers. Byte-safety re-verified each wave: uncommitted edits intact (B01 production
  M×3 + new file; QA docs/tests), BRIDGE commit untouched.
- **Two-manager process table discipline:** attribute every live `chat -q` python proc to its lane by
  the `-r <session-id>` cmdline fingerprint (PowerShell regex extract). This round: B lanes = 7bb91e/
  aeb5e3/f38ead; A's lanes (80e003 RETRY re-dispatched, 6cb8a7 VAL) appeared alongside — record their
  liveness in the heartbeat, never touch their PIDs/worktrees. A's Manager chat id observed later as
  `20260916_104759_1bb99d` (recorded in B's memory/registry when visible).

## Freeze closure + Q4 amendment + B01 landing (same day, later rounds)

- **QA sign-off delivered `d22d069`** (R7_PREP.md +72, sha `375f1dd5…`, 17,796 B): Q1 CONFIRMED with
  real numbers (10/10 segments have exactly one box per key; `segmentation.boxes == prompt.boxes`
  byte-identical; concrete values quoted), Q2 CONFIRMED (global frames authoritative; occurrences may
  cross scene bounds, chunked per shot; TEST-ONLY adapter note: the deterministic provider persists
  scene-LOCAL ranges for scenes after the first → BRIDGE multi-scene fixtures must seed GLOBAL ranges;
  provider fix = S08 scope, deferred), Q3 CONFIRMED, Q7 CONFIRMED (B05 acceptance = fresh public
  reapproval chain: old row byte-identical after reapproval + new row carries the timeline).
- **Q4 = REVISE (QA-F1)** — the one ruling premise that failed against real data: persisted boxes are
  PIXEL-scale; `_segment_region_from_geometry` returns raw floats while `_region_px` multiplies as
  normalized. Options given: (1) normalize the provider (test-only S08 change), (2) normalize at
  derivation with dims (QA recommended), (3) drop bounds (contradicts B04 — rejected).
- **Q9 FROZEN (normative)**: sidecar `<artifact>.evidence.json` = existing top-level fields +
  `per_layer_evidence[]`, exactly one row per active visible/occluded `(shot ∩ occurrence)` pair with
  17 fields (shot_id, range, layer_id, role_id, route, visibility, z_order, artifact_sha256/size,
  region_norm, region_px, sampled_frames, region_crop_sha256_before/after (pre-occluder at the layer's
  own composition step), final_crop_sha256, changed_pixel_count, changed_ratio, threshold=0.01,
  verdict contributed|no_delta). Acceptance: missing row/field or any no_delta →
  `STITCH_LAYER_EVIDENCE_MISSING` run failed no publication; overlap fixture must show 2 rows with
  DISTINCT artifact_sha256 + before≠after each layer = the no-dedup proof; counts equality
  `decoded_frame_count == plan == timeline.frame_count`. Crop-hash method frozen: sha256 over
  deterministic PNG-encoded RGB8 crop bytes; QA verifies presence/format/coherence, not recomputation.
- **D2 delivered: 23 exact node IDs** (B03×8, B04×6, B05×6, B06×7), production prompt copies them
  name-for-name; marker "to be frozen by BRIDGE owner per this mapping" until the lane inventory lands.

## Q4 amendment v0.2 — dual-mode region derivation (Manager ruling, flagged to Codex)

1. Canonical AFTER derivation = normalized `[0,1]` (`region_norm`); enforcement applies to the DERIVED
   value, never raw persisted bytes.
2. Mode A (normalized): four values finite, `x,y>=0`, `w,h>0`, `x+w<=1+1e-9`, `y+h<=1+1e-9` → as-is,
   `scale_mode="normalized"`.
3. Mode B (pixel): finite, `>=0`, `w,h>0`, positive source dims available, within `(src_w,src_h)` →
   divide by dims; `scale_mode="pixel"`.
4. Pixel-scale but dims unavailable → NEW typed `OCCURRENCE_REGION_SCALE_UNRESOLVED` (zero mutation);
   neither mode valid → existing `OCCURRENCE_REGION_OUT_OF_BOUNDS`.
5. Timeline records per occurrence: `affected_region` (normalized) + `raw_box` + `scale_mode` +
   `geometry_source`.
6. Fixtures: B03/B04 use pixel-scale (real convention) + ≥1 Mode A fixture + a dedicated
   SCALE_UNRESOLVED negative. Provider unchanged this wave (adapter note recorded).

## B01 F03 landed + BRIDGE production dispatch

- **B01 `2871f8f`** (parent 35f6cb2; 8 files +741/−46; then transport-record commit `a027c59`; worker
  run 27 passed): NEW `app/services/structural_lock_source_timing.py` (295 lines) — `prove_source_timing`
  → `SourceTimingProof` with codes `…TIMING_MISSING/_UNPROVEN/_MISMATCH` + `…SOURCE_VFR`; proof =
  all persisted facts positive + READY artifact hash match + probe CFR with equal r/avg rational +
  nb_frames exact + Fraction-arithmetic duration check. **`time_base` stays `"{fps_den}/{fps_num}"` —
  enforcement-only fix**, so BRIDGE's parse path works unchanged (Q8 resolved without waiting).
- **BRIDGE production dispatched** citing the four freeze artifacts by path (contract, freeze review,
  amendment v0.2, QA sign-off with §Q9/§D2) + 23 node IDs verbatim + D1 branch-blocked note; allowed
  files exactly s09_approval.py / s10_full_apply.py / s10_chunk_plan.py / s10_full_apply_jobs.py
  (+ optional new timeline helper + own new tests/docs).
- **B01 MANAGER_VERIFIED (closing state):** tip `a027c59` (docs) ← `2871f8f` (F03). Manager re-run
  27 passed (72.25s) + ruff clean + guard allow 8/8 + protected 18/18 VERIFIED. The worker's final loop
  additionally proved committed blob == worktree bytes (`git show HEAD:<path> | sha256sum` == disk
  sha256, LF-normalized) — when a worker reports repeated green re-runs over an unchanged tip, demand
  exactly this byte-equality proof as the closing check; it distinguishes "frozen, nothing pending"
  from "uncommitted edits hiding behind green runs".

## BRIDGE production delivered + Manager verification (same day, ~14:20–15:00 +07)

- Delivery `c49a578` (branch `codex/s12-r7-authority-bridge`; parent chain `b6108d4` ← `3963d31` ← `35f6cb2`;
  no push; tree clean):
  - `b6108d4` — 4 service files: `s09_approval.py` +373 (timeline block build/validate), `s10_full_apply.py`
    +266 (planner inputs from timeline), `s10_chunk_plan.py` +96, `s10_full_apply_jobs.py` +509 (composition
    replacing dedup + Q9 sidecar) + CONTRACT v0.2 (+78) + LOG (+77).
  - `34e680c` — NEW `app/services/source_locked_timeline.py` (414 L) + test suite (conftest 675, b03 286,
    b04 160, b05 423, b06 383) + REPORT 103.
  - `c49a578` — docs hash-record commit. Status `PRODUCTION_B03_B06_DELIVERED_PENDING_MANAGER_B_QA_REVIEW`.
  - **Re-attestation pattern**: the worker re-ran its gates on the frozen revision with a 13/13 file
    byte-identity pre-check (drift=0) and explicitly attributed its own tracker's "stale" warning to
    intermediate runs — good practice, mirror it when a worker's tooling complains about runs it already did.
- **Manager verification ALL GREEN**: `git show --stat` ×3 (all allowlist); guard allow 4/4 + protected
  18/18 VERIFIED; independent re-run G1 micro **27 passed** (84s), G2 `test_s10_full_apply_api` **71**
  (107s), G3 `t03c+retry` **66** (95s) — counts matching the worker's claims; G4 out-of-gate
  `test_s09_t06_backend_authority.py` **3 failed / 18 passed** = exactly the flagged identities
  (`test_v2_authority_full_from_persisted_hash_verified`, `test_single_head_and_models_unchanged`,
  `test_reapprove_api_201_and_authority_endpoint`). Contain the blast radius: re-run only the affected gate
  sets (+ the one flagged module) — never the broad suite while other lanes still run.
- **Q4 v0.2.1 (clip) accepted after code review** of `derive_region`
  (`source_locked_timeline.py:165–229`): Mode A strict normalized; Mode B = `x<src_w and y<src_h`
  (intersects) + clip `x2=min(x+w,sw)`, `y2=min(y+h,sh)`; fully-outside → `OCCURRENCE_REGION_OUT_OF_BOUNDS`;
  dims unavailable → `OCCURRENCE_REGION_SCALE_UNRESOLVED`. Rationale: the sanctioned chain's OWN padded
  boxes overrun the frame ({400,100,250,250} on 640×360 → 650>640); pixels outside the frame do not exist;
  strict containment would reject the entire sanctioned chain (the QA-F1 failure itself). Companion shapes
  verified in the same read: `_select_occurrence_box` (within-key boxes must be equal else
  `OCCURRENCE_GEOMETRY_AMBIGUOUS`; missing → MISSING; corrupt → TAMPERED) and `parse_time_base` (exact
  `"{den}/{num}"` split + int parse + fps equality via exact double compare; unprovable →
  `TIMELINE_TIME_BASE_UNAVAILABLE`).
- **BRIDGE REPORT's 6 explicit flags — Manager verdict per flag (accepted/recorded, none skipped):**
  1. Q4 hardening → amendment v0.2.1 recorded in the ruling doc, flagged to Codex in the packet.
  2. D2 count = 27 not 23 (dispatch-prompt arithmetic miscount; owner delivered all 27 verbatim + flagged).
  3. Bounded legacy client-copy alias: occurrence→scene for old shot ids; role→occurrence ONLY when the
     role owns exactly one occurrence; ambiguous → fail closed; plan stays canonical, every value mismatch
     still 422. QA asked to confirm no hole.
  4. `test_s09_t06` out-of-gate: 2 contract-mandated (points-only fixture asserts `executable is True` /
     `reasons == []` — superseded by the frozen B04 semantics) + 1 pre-existing (alembic head constant).
  5. Worker composition input = job manifest `render_authority` (scene_manifest.shots +
     structural_lock_manifest.frame_count + canonical mapping, incl. per-occurrence range/z/visibility) —
     no timeline re-read, no live-Scene re-read.
  6. Q9 row granularity per `(shot ∩ occurrence ∩ chunk-run)` unit, 19 fields covering the frozen 17-entry
     list (crop hash = sha256 over concatenated deterministic PNG RGB8 bytes).
- **FINDING R7-B1 filed** (`B/manager/FINDING_r7b1_s09_t06_superseded_assertions.md`): exact proposal =
  flip the 2 points-only assertions to ineligible+typed-reason (or add boxed geometry), keep the alembic
  one labelled pre-existing; proposed owner QA (T03A test-only-exception precedent); Codex decides the
  write-set grant. Contract-mandated reds get labelled in the final broad gate, never hidden.
- **QA phase-2 review dispatched (bounded)**: read REPORT + CONTRACT v0.2 + code (read-only worktree);
  D2 inventory sync (delivered 27 names → R6_INVENTORY §R7); Q9 conformance verdict; v0.2.1 coverage check
  (Mode A fixture + SCALE_UNRESOLVED negative + fully-outside deny); legacy-alias no-hole check; read-only
  micro re-run from the BRIDGE worktree with its own basetemp; commit
  `S12-LC3-QA: BRIDGE phase-2 review (D2 sync 27 nodes + Q9 conformance + v0.2.1 coverage)`.
