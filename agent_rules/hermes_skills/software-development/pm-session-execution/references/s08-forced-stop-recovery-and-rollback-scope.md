# Forced-stop recovery: LOG/REPORT divergence + per-path rollback scope

Verified 2026-08-18, S08-H02-C1 recovery (Hermes manager session) and
2026-08-19 S08-H02-C2 (Codex CHANGES_REQUESTED on preset containment).

## 1. LOG vs REPORT can DISAGREE after a force-stop

Scenario: the previous H02-C1 worker was force-stopped mid-turn while appending
REPORT.md. Disk state afterward:

- LOG.md contained a CORRECTION C1 entry that claimed "REPORT.md appended
  CORRECTION C1 section — Status: SUBMITTED."
- REPORT.md had NO CORRECTION C1 section (only the C2 round + validation).
- The worker log tail literally stopped at "Let me append to REPORT.md."

Lesson: a force-stopped worker's own doc claims are UNVERIFIED. The manager
must check the claimed section EXISTS in the target file on disk before
launching the next gate. The recovery packet (e.g. `RECOVERY_PROMPT.md`) must
STATE this gap explicitly so the writer audits rather than trusts prior claims.

## 2. Grep false-negative on section headings

- `grep -cE '^## (CORRECTION|Outcome|Manager)'` returned 0 → looked like the
  section was missing.
- Actual heading was `# CORRECTION C1` (single `#`), and later rounds used
  `## CORRECTION ROUND C2` / `## CORRECTION (PM review round N)`.
- Use a broad pattern: `grep -cE '^#+ CORRECTION'` or just read the tail of the
  file before declaring a section missing. Do not trust a narrow regex 0-count.

## 3. Metadata-update-failure rollback is NOT transitive across sibling publish paths

- `tests/test_s08_h02_security.py` had `test_metadata_update_failure_rolls_back_file_and_state`
  passing — but it only exercised the REPLACEMENT IMAGE path (monkeypatched
  `api_deps._project_wf.update_object`).
- The VIDEO-SOURCE path was unprotected: `upload_video` did
  `staging.replace(proj_dir / stored_name)` inside try/finally, then called
  `pwf.set_video(project_id, stored_name)` AFTER the try/finally. A
  `set_video` / project-metadata write failure left the just-published
  `source_<uuid>.mp4` as an orphan and prior state unrolled-back.
- Fix pattern (smallest safe): wrap the metadata update; on any exception
  remove the just-published artifact (`(proj_dir / stored_name).unlink(missing_ok=True)`)
  and re-raise — previous valid source stays present and SELECTED, project.json
  stays valid, no orphan.
- Rule: for EVERY publish-then-update-metadata endpoint, add one rollback test
  PER DISTINCT publish path, named for its path
  (`test_video_metadata_update_failure_rolls_back_file_and_state`). Assert:
  response 500 (stable), new file REMOVED, only previous file remains,
  project.json byte-identical, previous artifact still SELECTED, GET project
  200, no staging/publish-temp orphan.

## 4. Client-string → stored-filename joins recur beyond uploads (S08-H02-C2)

Codex CHANGES_REQUESTED on S08 (2026-08-19):

- P1#1 preset save (`app/api/routes/projects.py` ~L1943):
  `output_path = presets_dir / f"{body.name.lower().replace(' ', '_')}.json"`
  — body.name is client-controlled; `..\project` yielded
  `<presets>/../project.json` → overwrote `project.json` (Codex repro: 322 B → 118 B).
- P1#2 preset apply (~L1982):
  `preset_path = proj_dir / "presets" / preset_filename` — path-param
  `preset_filename` unvalidated, Windows backslash traversal.
- Secondary: `app/services/video_probe.py` uses `subprocess.run(capture_output=True)`
  with `-show_streams` — stdout/stderr/stream-count have no explicit hard
  ceiling (timeout + dimension caps exist). Close with: query only required
  ffprobe fields + first relevant streams; explicit bounded output contract;
  oversized/malformed probe output fails closed without publishing media.

The H02 containment class applies to ANY name-derived filename:
- server-owned storage name, OR strict single-segment validation for BOTH the
  save-name and the apply-filename;
- reject slash/backslash/dot-dot/absolute/drive-qualified/control-byte inputs
  with stable 422 BEFORE the join;
- resolve + containment-check output under the managed subdir (`<project>/presets`);
- reject symlink/junction escape; hostile input → stable 4xx never 500;
- audit SIBLING endpoints (export.zip paths, etc.) for the same unchecked join —
  do not stop after fixing the two reported lines.

Required test list (from Codex brief): save `..\project` and `../project`
cannot overwrite project.json; multi-level traversal cannot write outside
project/presets; isolated channels.json/sentinel byte-identical; absolute /
drive-qualified / slash / backslash / dot / control-byte → 422; apply traversal
cannot load project.json or sentinel outside presets; resolved/symlink escape
rejected; no new file outside presets; valid save/list/apply still succeeds;
all rejected requests zero-side-effect + never 500.

## Manager workflow notes for the round

- Confirm each finding on disk BEFORE dispatching the writer (grep the exact
  vulnerable lines). Both P1s verified present.
- Materialize the full packet (TASK.md / START_PROMPT.md / LOG stub / REPORT
  stub) at `docs/pm/sessions/S08-H02-C2-preset-path-containment/` before launch.
- Resume the task's OWN session (20260818_020323_151164), model flash, launcher
  `output/run-s08-h02-c2.ps1`, watcher `scripts/watch-s08-h02c2.sh`.
- Session id must be re-verified via `hermes sessions list` each round (the
  handoff may carry a truncated id, e.g. `e9f2b` vs real `e9f2b8`).
- Validation order per brief: new preset tests → full test_s08_h02_security.py
  → + test_api.py → cross-suite (golden + h02 + object_extraction_api + r01) →
  ruff → mypy → diff-check → baseline 7/7 → protected MAIN hashes + ports.
- Never APPROVED/CLOSED; stop at SPRINT_SUBMITTED awaiting Codex.
