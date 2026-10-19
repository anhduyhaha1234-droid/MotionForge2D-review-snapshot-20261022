# S10-C2 — T03 partial recompute + report-finalization + J3 gate (verified 2026-08-29 01:08–02:04)

Continuation of `s10-c2-t01c-meta-max-continuation.md` — same session `20260828_180654_be71b5`, worktree `s08-integration`, after J2 MANAGER_VERIFIED (T01C 23/23×2 Meta-max).

## T03-C2 task shape (what the worker had to do)

Exclusive write-set: `app/services/s10_recompute.py` + `tests/test_s10_partial_recompute.py` + bounded `app/api/routes/s10_full_apply.py` recompute hunk (from C1). Forbidden: migration/model/frontend/S11/S13/J1/data.

Checklist (all PASS on disk, verified by Manager J3):
1. DELETE `chunk_*.bin` production path — `s10_recompute.py:619` `rel = f"s10_recompute/{run_id}/{correction_id}/chunk_{idx:04d}_{sha[:12]}.bin"` with `payload=sha256(payload).digest()*64` + `mr.atomic_write_bytes` + INSERT without sha/size — entire block DELETED. AFTER: `rel = f"s10_recompute/{run_id}/{correction_id}/chunk_{idx:04d}_{layer_id}_{sha_marker}.mp4"` decodable via `write_frames_mp4` → `decode_rgb_frames` → `probe_source_timebase` → `hash_file`.
2. `mkdir parents` before atomic write — `(managed_root/Path(rel).parent).mkdir(parents=True,exist_ok=True)` + `abs_out.parent.mkdir` at 660-661 (plus 693, 824-825 for evidence/restitch) — brand-new managed_root 3-level nested `s10_recompute/{run}/{correction}`; surviving 2 previously-failing tests.
3. Provenance + registry bind — `s10_recompute_record UNIQUE(workspace_id, correction_id)` at :232/:263 + `s10_recompute_provenance PRIMARY KEY(chunk_id, correction_id)` at :293 — per-chunk `INSERT OR REPLACE` with `provenance_json {correction_id, attempt, result_hash}`, replay dedupe `SELECT existing by (workspace_id, correction_id)`.
4. Durable media per affected chunk — deterministic 64×64 frames `base=sha256(recompute:correction:cid:attempt).digest()`, `expected_frames=core_end-core_start+1`, fps from run row fallback 30/1, `write_frames_mp4` → `decode` assert len==expected → `probe` assert fps → `canonical_frame_sha256` → `hash_file` sha len 64 + `size>0` → evidence.json staged atomically → INSERT artifact `sha256, size_bytes, state ready` → UPDATE chunk `verified=1`.
5. `_restitch_after_correction` at :761 — dedup `(shot_id, core_start, core_end)`, decode all verified chunks, `stitch_hash=sha256(recompute-stitch:run:correction:result:len).digest[:12]`, `rel s10_recompute/{run}/{correction}/full_{hash}.mp4`, write+hash+decode, publication `natural_key recompute-pub:{run}:{correction}` with `pub_hash=sha256(pub-recompute:run:correction:sha)`.
6. Seed fix — `tests/test_s10_partial_recompute.py: _seed_run_with_chunks` previously created job `{run_id, workspace_id, project_id, managed_root}` without `render_authority/source pin` → worker fail-closed "render_authority missing" → 0/8 verified. Fixed: `affected_region [0.10,0.10,0.40,0.40]`, `_stage_source_for_seed` 120×160 100 frames `write_frames_mp4+hash_file`, `_stage_asset_for_seed` 40×40 PNG per layer, authority `{approved_checkpoint, structural_lock_manifest, scene_manifest 2 shots, mapping with affected_region, compatibility_policy, chunk_config}`, job manifest `render_authority + source_media_rel/sha256 + replacement_assets` so T02 path `sprite_affine/controlled_redraw` runs real composite.

## Network-transient arc (infra, not product)

| Attempt | Dispatch log | Outcome |
|---|---|---|
| R1 01:08 | `dispatch-meta.log` 90 B | `CommandCode error: {"type":"server_error","message":"Network connection lost."}` wrapper EXIT=0, no worker output |
| R2 01:08→01:29 | `dispatch-meta-r2.log` 90 B | same 90 B drop |
| R3 01:30→01:49 | `dispatch-meta-r3.log` 8096 B | SUCCESS — 9×2 PASS 49s, regressions 23+46, ruff F*=0 — but iteration-limit before REPORT |
| R4 01:49→02:02 | `dispatch-meta-r4.log` 2934 B | REPORT finalization — 9×2 48s, ruff 0 F, LOG+REPORT+5 logs done |

Distinguisher: ping `1.1.1.1` 0% loss (20 ms), `hermes -z ping` pong, 9Router `:20128` ESTABLISHED — upstream transient, not stall/compression (12 s CPU frozen) nor 402 (cmc/OpenRouter). Rules §7: wait+retry same owner same provider/model; 3× persists → BLOCKED_NETWORK, not BLOCKED_WITH_FINDINGS.

## Iteration-limit — code green but report pending

R3 hit tool-iteration limit AFTER code gates passed but BEFORE `LOG.md`/`REPORT.md` + `output/s10/c2/t03-c2/` (pytest_run1/2.log, ruff_F.log, git_diff_check.log, git_status.log) were appended. Worker log explicitly: "Chưa ghi STATUS: TASK_SUBMITTED do hết tool iterations ... code production đã đạt gate, chỉ còn khâu ghi báo cáo". Manager fix: resume SAME owner `20260828_011920_b79bd6` with focused prompt — code already 9×2 PASS per r3 log, only append LOG+REPORT+logs verbatim, no code change expected, same `--provider custom -m meta --yolo`, new log `r4`.

R4 verified:
- `pytest tests/test_s10_partial_recompute.py -v -p no:cacheprovider --override-ini="addopts=" --basetemp fresh` → **9 passed 48.77s + 9 passed 49.05s** deterministic ×2 → `pytest_run1/2.log`; `ruff check --select F` → `All checks passed!` (fixed prior F841 content_hash + F401 numpy); `mypy --ignore-missing-imports` → Success; `git diff --check` 0; `grep chunk_*.bin app/` 0.
- Artifacts: `docs/pm/sessions/S10-T03-partial-recompute/LOG.md` 9.0K + `REPORT.md` 22K + `output/s10/c2/t03-c2/` 5 logs; STATUS: TASK_SUBMITTED.

## J3 Manager gate (independent, not trust worker report)

`mkdir -p output/s10/c2/j3` then:

```
unset MOTIONFORGE_DATABASE_URL
python -m pytest tests/test_s10_partial_recompute.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=C:/Users/Admin/AppData/Local/Temp/s10c2-j3-run1  → 9 passed 49.39s → j3-run1.log
python -m pytest tests/test_s10_partial_recompute.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=C:/Users/Admin/AppData/Local/Temp/s10c2-j3-run2  → 9 passed 49.26s → j3-run2.log
```

Registry: `2026-08-29 02:04 +07 — J3 (C2) GATE MANAGER_VERIFIED — T03-C2 DONE 9/9 x2 (Meta-max)` — opening T04A-C2 (`proc_721ef944e850`, owner `20260828_014304_25d94a`, `--provider custom -m meta`, `dispatch-meta.log`).

## Rules to carry

1. **Report-finalization resume**: when dispatch log shows code PASS×2 but ends with "Chưa ghi STATUS" / iteration-limit, do a report-only resume (focused prompt, no code). Verify LOG+REPORT+output logs exist before J-gate.
2. **Network retry**: 90 B `Network connection lost` + wrapper EXIT=0 + ping/9Router OK = retry same owner; 3× → escalate.
3. **Seed authority**: partial-recompute seeds must carry `render_authority + source_media_rel/sha256 + replacement_assets` + `affected_region` or T02 executor fail-closes.
