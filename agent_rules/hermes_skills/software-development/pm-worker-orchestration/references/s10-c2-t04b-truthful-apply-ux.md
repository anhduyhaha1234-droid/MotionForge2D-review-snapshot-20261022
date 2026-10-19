# S10-C2 — T04B truthful Apply UX + J5 gate (verified 2026-08-29 02:57–03:35)

Continuation of `s10-c2-t04a-measured-gate.md` — same session `20260828_180654_be71b5`, worktree `s08-integration`, owner `20260828_020206_b1f8af` (T04B-C1-R1), route `custom/meta` (Meta-max, `meta` via `custom` — the only pong that survived 02:47–00:35 probe matrix; `ocg/muse-spark-1.2-contributor` via `muse`/`opencode` 404s that night).

## Why this exists
T04B-C1 is the **truthful Apply UX** — the frontend had fabricated constants in `ApplyCard.tsx` and `apply/page.tsx` that bypassed the server authority chain (T01C/T02/T03/T04A). The correction makes the UI explicitly authoritative or explicitly disabled, with no synthetic plan/metric fallback, no `shot_a` ghost, and Vietnamese helper text at 11px as required.

## Fabricated surface removed (before → after)

### Before (grep on T04B preflight)
- `ApplyCard.tsx:92` `source_generation gen-1`, `:93` `frame_count 100`, `:98` shots `shot_a 0-49` `shot_b 50-99`, `:99` mapping `layer_bg sprite_affine` + `layer_fg mesh_warp`, `end_frame 49/99`
- `apply/page.tsx:190-201` `trajectory_errors/scale_errors/rotation_errors/contact_errors` + `shot_a` fallback + `shotOrder/shotCuts` synthetic derived from chunks, `source_cut = rendered`

### After (patched, verified `grep ... => 0` both files)
#### `frontend/src/features/apply/ApplyCard.tsx`
- Implicit `checkpoints[0]` → `checkpoints.find(c=>c.id===checkpointId)` with explicit `const [checkpointId,setCheckpointId]` state
- New `<select id=apply-checkpoint-select data-testid=apply-checkpoint-select>` with placeholder `— Chon checkpoint duyet —` + `text-[11px] text-gray-400` helper text; no auto-select; `onProjectChange` clears checkpoint; `loadProjects` preserves only if still belongs to project
- `approvedCheckpoint` strict server-truth: `{checkpoint_id, checkpoint_hash, revision, project_id, reskin_config_id, structural_lock_manifest_id}`
- `structuralLockManifest` truth: `manifest_hash: timebase_fingerprint` (no fallback to `checkpoint_hash`), `policy_version || v1`, optional `source_generation/frame_count` ONLY if snapshot carries them
- `sceneManifest = snap.scene_manifest ?? snap.structural_lock_manifest ?? snap.shots ?? snap.scenes ?? null`; `mapping = snap.mapping ?? snap.mappings ?? snap.renderer_routes_per_segment ?? null`; `sceneManifest===null || mapping===null => selection null`
- **Vietnamese** (text-gray-400 11px) disable reasons: `timebase_fingerprint missing → "Checkpoint thieu timebase_fingerprint — bang chung lock chua duoc pin day du, khong the Apply."`, `snapshot null → "Checkpoint thieu snapshot..."`, cross-project, video missing, `selection null → "Checkpoint chua du bang chung scene/mapping tu backend — khong the gui Apply voi du lieu gia."`, loading/empty project/video/checkpoint
- `effectiveIsDisabled / effectiveDisabledReason` drive button `disabled/aria-disabled/class/helper` + `data-testid=apply-submit-helper`, `onSelectionChange + onApply` guard; every button carries `HELPER="text-[11px] leading-snug text-gray-400"`

#### `frontend/src/app/(app)/apply/page.tsx`
- Delete 55-line fabricated body (`shotOrder/shotCuts/totalFrames/source_shot_order` + hard-coded `trajectory_errors [0.1,0.2,0.15]` `scale_errors [0.5,0.8,1.0]` `rotation [0.4,0.9,0.6]` `contact [0.1,0.15,0.2]` `z_order/visibility/clipping` + `annotations shot_a/50`)
- Replace with server-derived only: `const body: Record<string,unknown> = {}; // empty hint extra=allow, server ignores, computes from pinned StructuralLockManifest + publication + evidence hashes`
- `ApplyEvidenceLinks` + `ApplyProgress` via `GET /api/v2/full-apply/{run_id}` remain hash-bound; cancel/retry/resume/recompute survive reload via `localStorage s10:apply:lastRunId` + URL `run_id/project` + `useApplyStatus` polling (no synthetic local completion)
- After-patch: `gen-1/shot_a/layer_bg/mesh_warp/trajectory_errors => NONE` in both files, `fetchEvidence` only `api.structuralCompareS10(runId,{})` , Vietnamese diacritics intact, helpers all `text-gray-400`

## Iteration-limit → report-finalization resume (same owner)

- R1 `dispatch-meta.log` (03:19, 5655 B, RULES_LOADED 180 SHA 987386c5): fabricated removal DONE, but `docs/pm/sessions/S10-T04B-apply-ux/TASK.md+LOG.md+REPORT.md` empty (0 files) + validation chain not yet run (`max tool iterations reached`)
- Manager resume `R2` same owner `20260828_020206_b1f8af` `custom/meta` with focused prompt `dispatch-meta-r2.log` (7 B wrapper now, but REPORT 14K landed — the real evidence):
  - `TASK.md` 7.7K + `LOG.md` 12K + `REPORT.md` 14K + stray `_tmp_patch_page.py` removed
  - `output/s10/c2/t04b-c1-r1/` isolation dir: `fileline-after.log` (gen-1 0 shot_a 0 trajectory_errors 0), `tsc.log` TSC_EXIT=0, `eslint-apply.log` ESLINT_EXIT=0, `next-build.log` 1678ms `Route /apply` present BUILD_EXIT=0, `playwright-list.log` 6 tests (18/48/76/115/146/157), `pytest-api-workflow-run{1,2}.log` 23/23 each, `api-origin-scan.log` fallback `http://localhost:8888` + `next.config.ts` apiUrl + `.next/required-server-files.json` 4 hits no 8201/8099, `ui-audit.log` zero synthetic + helper visible + `body: {}`, `git-status-diff.log` diff 0 only allowlist + pre-existing dirty, no `8888` drift

## J5 Manager gate (independent, not trust worker; T01C regressions)

```bash
mkdir -p output/s10/c2/j5
unset MOTIONFORGE_DATABASE_URL
python -m pytest tests/test_s10_full_apply_api.py tests/test_s10_full_apply_workflow.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=C:/Users/Admin/AppData/Local/Temp/s10c2-j5a -> 23 passed 47 warnings 62.29s -> j5-run1.log
python -m pytest tests/test_s10_full_apply_api.py tests/test_s10_full_apply_workflow.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=C:/Users/Admin/AppData/Local/Temp/s10c2-j5b -> 23 passed 47 warnings 61.48s -> j5-run2.log
```

Registry `2026-08-29 03:33 +07 — J5 (C2) GATE MANAGER_VERIFIED — T04B-C1-R1 DONE 23/23 x2 + TSC/ESLint/build (Meta-max)` — opening T04C-C1 (`proc_640db904559a`, owner `20260828_023122_76b87e`, `custom/meta`, `dispatch-meta.log`). On Windows, `terminal` rejects `&`-backgrounded pipes — use `background=true` + `notify_on_complete=true` then `process wait`.

## Rules to carry
1. **Truthful UI = disabled-or-authoritative**: no synthetic plan/metric body; every disabled reason is a user-visible Vietnamese string (text-gray-400 11px), not a silent no-op; checkpoint identity is explicit select, not `checkpoints[0]`.
2. **Report-finalization on iteration-limit**: worker `R1` can land fabricated removal before exhausting iterations; Manager must do a same-owner report-only resume (focused prompt, same route) and verify `TASK+LOG+REPORT+output/s10/c2/**` exist before J-gate.
3. **Meta-max at 03:19**: `custom/meta` is the only pong that night; `ocg/muse-spark` long-form 404s — probe the EXACT manager-chat pair before every resume.
