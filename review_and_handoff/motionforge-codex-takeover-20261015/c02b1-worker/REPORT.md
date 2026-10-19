# C02B1 staged-source freshness — worker submission

Status: `TASK_SUBMITTED_PENDING_ROOT_REVIEW`. Owner `/root/motionforge_c02b1_coder`, GPT-6 Sol Max, no fallback. This is a self-reviewed candidate; it is not Codex-approved and does not close the parent pilot.

`r6_common.stage_frame(sid, gframe, dst) -> Path` now reuses a staged frame only when a versioned adjacent receipt matches the canonical source path and exact SHA256, shot and requested global frame, canonical output path, and exact output SHA256/size. Legacy, malformed, copied, incomplete or stale receipts cause re-extraction. Frame requests outside the current shot plan fail before source access. The existing `-ss gframe/30`, one-frame FFmpeg extraction and 640×360 no-pad behavior remain.

Extraction uses a unique temporary PNG sibling. The helper checks the source identity before and after FFmpeg and requires a nonempty result. Extraction errors leave any old output and receipt bytes intact. After successful extraction, a pending marker invalidates the old receipt, then the frame is published and the final receipt is published. If final publication fails, the next request sees the pending marker and re-extracts. No lock framework was added; this task retains the WIP1 contract.

Self-review pass 1 checked the call signature, global frame mapping, source/canvas behavior, allowlist and S1–S7 matrix. Pass 2 checked strict receipt types/duplicate keys/depth bound, source and output byte identity, failure cleanup, partial publication, and caller compatibility. The only changed live files are `R6/scripts/r6_common.py` and new `R6/tests/test_codex_c02b1_staged_source.py`; the 27 pinned protected files and all byte snapshots match preflight. No duplicate definitions or unexpected Python files appeared. Raw results and exact hashes are in `AUDIT.json`, `common.diff` and `LOG.md`.

Verification:

| Gate | Result | Evidence |
| --- | --- | --- |
| Baseline old helper and red regression | expected fail: 2/7 and 0/1 | `baseline-probe/RESULT.json`, `test_red_01.log` |
| New full staged-source module | 10/10, exit 0 | `test_matrix_s1_s6.log` |
| Real tiny 30fps, 640×360 FFmpeg fixture | source A frame 0 `(253,0,0)`, frame 1 `(0,255,0)`; source B replacement frame 1 `(253,0,0)`; unchanged reuse makes no FFmpeg call | `real-ffmpeg-rx7q9lr_/RESULT.json`, source MP4s and PNGs |
| Root seven-case helper probe | 7/7, exit 0 | `post-probe/RESULT.json` |
| Full approved C01 and C02A modules | 17/17 and 13/13, exit 0 | `test_c01_full.log`, `test_c02a_full.log` |
| Protected byte/scope audit | 27/27 unchanged; no duplicate or unexpected Python definitions/files | `AUDIT.json`, `common.diff` |

All tests ran against isolated files in `c02b1-worker`; the real fixture used FFmpeg on tiny generated MP4s. No production source/model was hashed in a test, and no pilot or full-source render was run. The known C02B2 settings/producer-capture and media acceptance work remains outside this task.

Root should independently review the frozen candidate snapshot and live hashes, run a fresh focused probe/module against those bytes, inspect the diff and confirm protected-file hashes before any next task is opened.
