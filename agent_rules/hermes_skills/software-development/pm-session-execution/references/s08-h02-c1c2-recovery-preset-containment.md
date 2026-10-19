# S08-H02 C1/C2 recovery rounds — forced-stop repair, rollback audit, preset containment, bounded probe

Session-specific detail behind the "Forced-stop recovery", "Post-publish metadata
rollback", "Client-controlled filesystem joins", "Bounded subprocess stdout" and
"Manager verify-script traps" sections of SKILL.md. Full playbook verified
2026-08-19 on `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
(branch `codex/s08-integration`, HEAD `a43b20d`, dirty baseline ~169-171).

## Round 1 — H02-C1 recovery (forced stop)

State at manager handoff:
- Worker resumed OWN H02 session `20260818_020323_151164`, wrote code+tests,
  appended a LOG entry that CLAIMED "REPORT.md appended / Status SUBMITTED",
  then was force-stopped mid-turn.
- REPORT.md had NO CORRECTION C1 section (only the C2 round + validation).
- The worker log tail literally ended at "Let me append to REPORT.md." — the
  death marker proving the report append never completed.
- Mandatory audit §5 gap: `upload_video` published via
  `staging.replace(proj_dir / stored_name)` inside try, then called
  `pwf.set_video(project_id, stored_name)` AFTER the try/finally — no rollback
  of the just-published file if set_video/meta-write failed (replacement-image
  rollback existed; source-video rollback did NOT).

Detection commands (read-only, before dispatching writer):
- `tail -5 output/<task>-c1-hermes.log | tr -d '\000'` → truncated final line.
- `grep -nE '^## (CORRECTION|Outcome|Manager|RECOVERY|VALIDATION)' REPORT.md`
  → 0 sections + LOG claiming them = fabricated/over-claimed record.

Recovery writer scope (exactly ONE writer, resume same session):
- Fix: wrap `set_video` in try/except; on exception
  `(proj_dir / stored_name).unlink(missing_ok=True)` and re-raise — previous
  valid source stays present AND SELECTED, project.json byte-identical.
- New test `test_video_metadata_update_failure_rolls_back_file_and_state`:
  upload video 1 (valid), then inject set_video failure after a second publish;
  assert 500, new source_<uuid>.mp4 REMOVED, only previous source remains,
  project.json byte-identical, previous source bytes intact, GET project 200
  with previous source_video, no staging/publish-temp orphan.
- Docs: append RECOVERY entry to LOG (correcting the false append claim) +
  append the real CORRECTION C1 section to REPORT; LOG/REPORT agree.

Manager gate numbers (fresh basetemps, `-p no:cacheprovider`):
focused 62/62 (30.55s) • rollback test 1/1 (2.82s) • T01-T05 184/184 (97.53s)
• R01 18/18 • S05 41/41 (97.28s) • S02 87/87 (41.14s) • ruff/mypy/diff 0
• migration head f6a7b8c9d0e1 rows 2/2 • smoke health 200 / untrusted 403 /
trusted ACAO / hostile 422 • protected MAIN unchanged.

## Round 2 — H02-C2 preset path containment (Codex CHANGES_REQUESTED)

Two P1 findings + one secondary, all verified on disk before dispatch:

- P1#1 SAVE: `presets_dir / f"{body.name.lower().replace(' ','_')}.json"`
  — client `body.name` only lower/space-normalized, so `..\project` escapes
  `<project>/presets` and overwrites project.json (Codex repro: 322 B → 118 B).
- P1#2 APPLY: `proj_dir / "presets" / preset_filename` — unvalidated join,
  Windows backslash traversal read outside presets.
- SECONDARY: `video_probe.py` `subprocess.run(capture_output=True)` +
  `-show_streams` — all stdout captured, every stream parsed, no size ceiling.

Fix (central resolver in `app/workflow/preset_service.py`, not per-route):
- `safe_preset_output_path(presets_dir, display_name)`: client name
  display-only; file name = strict server slug. Reject slash, backslash, `..`,
  dot-only, absolute, drive-qualified, control bytes (detect BEFORE
  null-stripping so `a\x00b` is refused), empty, reserved slugs (case-
  insensitive, incl. `project.json`) → 422 BEFORE any write;
  `Path.resolve(strict=False)` containment proven under presets.
- `safe_preset_path(presets_dir, preset_filename)`: single safe segment ending
  `.json`, same hostile class rejected, symlink/junction escape rejected by
  resolve+containment. Hostile → 422; well-formed-but-missing → 404; never 500.
- `video_probe._run_ffprobe`: line-buffered 1 MiB hard ceiling + deadline,
  fails closed (`ProbeOutputTooLargeError` / `TimeoutExpired`);
  `-select_streams v:0/a:0` + `-show_entries` field restriction; parse ceiling
  `PROBE_MAX_STREAMS = 4` + JSON-shape validation. Probe failure → route 415,
  NO media published, NO project-state change.
- Rest-of-file audit: only the two preset joins were the remaining
  client-controlled filesystem joins (character preset set_key/pose resolved
  against fixed dict keys; project/object ids already centralized).

13 new mandatory tests incl. `test_preset_save_traversal_names_cannot_overwrite_
project_json`, `test_preset_apply_traversal_cannot_load_project_json_or_sentinel`,
`test_preset_apply_symlink_escape_rejected`, `test_preset_valid_save_list_apply_
succeeds`, `test_preset_rejected_requests_never_500`, `test_video_probe_oversized
_output_fails_closed`, `test_video_probe_stream_ceiling_fails_closed`,
`test_video_upload_probe_failure_does_not_publish`.

Validation order (Codex-mandated, run in this exact order):
1. new preset/video_probe tests (`-k 'preset or video_probe or oversize or
   malformed or stream_ceiling'`) → 20 passed
2. full test_s08_h02_security.py → 50 passed
3. + test_api.py → 75 passed
4. cross-suite: golden_object_intelligence + h02 + object_extraction_api +
   r01_queued_cancel_lifecycle → 77 passed (golden vertical re-runs green)
5. ruff app tests → All checks passed
6. mypy app → 88 files, 0 issues
7. git diff --check → 0
8. frontend tsc/lint/build ONLY if shared/API behavior touched (backend-only
   round → not touched)
9. one fresh 7/7 quality baseline (NEW Run ID; this round: 20260819-015528)
10. protected MAIN hashes + QA ports NO_LISTENERS

Manager verification numbers (independent, fresh basetemps): 20/20 + 50/50 +
75/75 + 77/77 + ruff/mypy/diff 0 + migration head f6a7b8c9d0e1 unchanged +
protected MAIN unchanged + git status 171 (baseline + packet + golden evidence).

## Reusable manager patterns exercised

- Heartbeats every ~5-10 min with: Time, Active Task ID, session, writer count,
  last progress, current action, next check, next gate, liveness state.
- `MANAGER_STATE.md` persisted with last_progress_at, writer session/PID,
  current/last/next action, blocker, exact resume command — enables cold-start
  recovery for a replacement manager session.
- Verify ONE writer released before pytest; the manager stays read-only while
  the writer is alive (single-writer handshake). Pytest deferral for .ps1/.sh
  tooling documented once, then not re-litigated.
- Kill stale watchers by exact script path match on CommandLine; treat
  `CommandLine -match 'watch-s08'` counts as phantom self-matches until the
  PID's actual commandline (fetched by PID) shows the `.sh` path.
