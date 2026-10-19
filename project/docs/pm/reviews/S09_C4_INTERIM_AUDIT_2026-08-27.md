# S09-C4 interim Codex audit — 2026-08-27

Status: `IN_PROGRESS / NOT_READY_FOR_CODEX_FINAL_REVIEW`

## Authority and snapshot

- Canonical rules read in full: `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`, 180 lines, SHA-256 `987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25`.
- Integration worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Branch / HEAD: `codex/s08-integration` / `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`.
- Dirty count at audit: 117. No reset, restore, checkout, clean, stash, commit or push was performed.
- `MOTIONFORGE_DATABASE_URL`: unset. Alembic: one head, `b3c4d5e6f7a9`.
- At 02:05 +07 no process command line matched Manager `20260826_210525_884070`, T04 owner `20260824_052859_c6e197`, T05B owner `20260824_093602_af7c26`, T06B owner `20260824_131423_423e42`, Muse/Meta, or this worktree. The lane is quiescent, not still running in the background.

## Actual progress

| Item | Evidence-backed state |
|---|---|
| S09-T05A-C4 | Previous Manager-focused backend verification passed; conditional correction owner remains `20260824_072626_645cde`. |
| S09-T03-C4 | Previous focused verification passed; conditional correction owner remains `20260824_031524_a6bb2a`. |
| S09-T04-C4 | Owner `20260824_052859_c6e197` wrote `TASK_SUBMITTED (S09-T04-C4)`. Worker evidence says 21/21 x4; Codex independently reran the exact focused file: **21 passed, 39 warnings, 45.81s**. |
| J1-C4 | Not run to completion after the Muse T04 submission. |
| S09-T05B-C4 | PREP only / `WAITING_JOIN`; final C4 work not dispatched after T04. |
| J2-C4 | Not run. |
| S09-T06B-C4 | PREP only / `WAITING_JOIN`; production C4 x2 not run. |
| Final Manager gate | Not run. |

Therefore S09-C4 is not `TASK_MANAGER_VERIFIED` yet and cannot be submitted for final Codex approval.

## Findings

### F1 — P0 gate blocker: byte freeze is 6/13, caused only by EOL conversion

The v4 manifest file itself still hashes to:

`ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5`

Direct byte re-hash currently reports 7 drifted protected files:

- `app/services/renderer_contract.py`
- `app/services/renderer_router.py`
- `app/adapters/renderer/benchmark_harness.py`
- `app/adapters/renderer/encode_base.py`
- `app/adapters/renderer/ffmpeg_binary.py`
- `app/adapters/renderer/pose_swap_adapter.py`
- `app/adapters/renderer/sprite_affine_adapter.py`

All seven were batch-stamped at `2026-08-26 22:57:38 +07`. Binary analysis proves each current CRLF file becomes the exact expected manifest SHA when converted to UTF-8 LF with no BOM. The remaining six manifest entries already match their expected byte format; `composite.py` is intentionally represented by the CRLF hash in v4.

Impact: semantic source content was not lost, but v4 is a byte-level freeze. J1/T05B/T06B must remain blocked until a dedicated worker normalizes exactly the seven files and re-establishes 13/13 direct byte match. Do not pin v5 and do not rerun I03/I05.

### F2 — P1 test-integrity risk in T04 helper

`tests/test_s09_t04_demo_compare.py` passes, but `_seed_applied_zorder_correction` still has three false-green risks:

1. Lines 650-655 default an unknown/empty affected-loop list to `d4_group_occlusion` / `d4_group_1` instead of failing closed.
2. Lines 658-662 describe the segment ID as deterministic while including freshly created `scene.id`, `role.id` and `project.id`; it is not deterministic across an equivalent fresh fixture database.
3. Lines 686-707 catch a segment conflict and reuse by only `(workspace_id, logical_id)`, without proving project/video/role/scene/source-generation ownership matches. That can attach a correction to a lineage from a different fixture chain.

Impact: the focused suite can be green while its setup silently targets d4 or a different ownership chain. Resume exact T04 owner for a narrow correction/proof before J1.

### F3 — P1 orchestration/liveness cause

The old Manager is not a daemon. Hermes logs show normal `finish_reason=stop` at each completed chat turn, followed by cleanup of the inactive terminal environment. Long `sleep 570` / `sleep 480` commands only polled; they did not keep autonomous work alive.

The upstream route also had repeated 120-second time-to-first-byte kills and later HTTP 500 responses from `opencode-go/muse-spark-1.2-contributor`. T04 nevertheless completed and persisted its report before the Manager stopped. The next Manager must keep making tool calls in one active turn until the authorized terminal state, use bounded process waits, and raise the worker TTFB cutoff for the large resumed contexts.

### F4 — Corrected route finding: Hermes selection is combo `meta`

The earlier provider-alias interpretation was incorrect. The audited 9Router state defines `meta` as a real combo with `round-robin` strategy and exactly two members:

- `cmc/meta/muse-spark-1.2-contributor`
- `ocg/muse-spark-1.2-contributor`

Therefore the Hermes Manager and every resumed/new worker must select the exact model/combo name `meta` with reasoning `max`. They must not translate it to provider alias `muse`, directly pin `ocg/muse-spark-1.2-contributor`, or select another model. Round-robin within those two members is intended combo routing; fallback to any model outside the combo remains disabled and is a blocker.

## Required remaining DAG

`J0-META -> S09-FRZ-C4 byte normalization -> T04 narrow test-integrity correction -> J1-C4 -> T05B final -> J2-C4 -> T06B production x2 -> Manager final gate -> Codex final review`

No S10, production S11 or production S13 authority is opened by this audit.
