# Test drift at a new HEAD — the lane's green suite was run before its own commit

**Case:** MF-RESKIN correction wave `20260922T0955Z`, lane **MF-V1-VIDEO14B**, round **b3** (wave-B
closeout: write the report, copy the chosen raw candidate into the evidence root, commit).
**Date:** 2026-09-22, ~19:15 +07. Companion to `mf-v1-server-completed-job-reconciliation.md` (§29 of the
umbrella) — same lane, next round.

## What the round reported

Lane session `20260922_190127_662ec3`, exit 0, `duration 855.6 s`, terminal `TASK_SUBMITTED`:

```
D2  WAVE_B_REPORT.md         21,849 B      D3  MATRIX_ROWS.md  6,642 B
D4  HEAD   864f63c409a4dcbac92108a96cfaea7896ec3998
    HEAD^  c4b50325afaf77b132bf0e90aa0d00c2ffb2651f
    --stat 38 files changed, 28530 insertions(+), 6 deletions(-)
Disposition: F05 PASS · F06 PASS · F07 PASS · F08 NOT_REVIEWED · F09 PASS
            — 0 FAIL / 0 BLOCKED / 0 RUNNING / 0 UNMEASURED
```

Everything in that report was true except the last block's basis: the row dispositions were derived from
a suite run **before** the commit. Nothing was fabricated; the claim was simply **commit-relative and
stale**.

## What the Manager measured at that commit

```bash
cd C:/Users/Admin/Documents/Codex/work/mfv1/wt-video14b
python -m pytest experiments/mf_reskin_v1/video14b/tests -q -p no:cacheprovider
# → 2 failed, 24 passed, 1 skipped in 2.12s      (at c4b5032: 26 passed, 1 skipped)
python -m ruff check --select F experiments/mf_reskin_v1/video14b/tools/
# → Found 6 errors
git log --oneline -3 | cat
# 864f63c MF-V1-VIDEO14B wave-B closeout: the book4s clip, its evidence and the wave-B tools
# c4b5032 MF-V1-VIDEO14B wave-A closeout: F05 output contract for the stage runner
git rev-parse HEAD^            # c4b50325afaf77b132bf0e90aa0d00c2ffb2651f  (parent intact)
git status --porcelain | wc -l # 0
git branch -r --contains HEAD  # (empty → not pushed)
```

So the lane's git hygiene was perfect and its gate claim was wrong. Both facts had to be reported.

## Failure 1 — over-literal assertion, mechanism intact

```
_____________ test_export_drops_decoded_padding_not_bframe_packet _____________
E  AssertionError: selection must go through the decoded-frame select filter
E  assert 'select_filter(keep)' in ' -> int:\n    raw = _p(sys.argv[1])\n ... '
```

The test asserts on the literal string. The lane's wave-B change folded the F07 geometry crop into the
same step, so `main()` now calls `select_filter(keep, crop_ffmpeg)`:

```python
# tools/v14b_export_decode.py  (current main())
crop = crop_back_filter(raw_probe["width"], raw_probe["height"])
crop_disabled = "--no-crop" in sys.argv
crop_ffmpeg = crop["ffmpeg"] if crop else None
idx = presentation_indices(len(raw_pngs), keep)
... "-vf", select_filter(keep, crop_ffmpeg), "-fps_mode", "cfr", "-r", str(FPS), ...
```

The decoded-index `select` filter — the whole point of the F06 fix — was still there. **Fix = re-anchor on
the call** (`select_filter(` with arguments allowed) and **keep** the two negative assertions the test
already carried:

```python
assert "-frames:v" not in main_body, "packet-count cutting must not come back"
assert "-c:v\", \"copy\"" not in main_body and "-c:v', 'copy'" not in main_body
```

## Failure 2 — stale expectation where the CODE was right

```
E  AssertionError: {'114': {'kind': 'images', 'media_type': 'video', 'server_types': ('output',)}}
E    assert ... == {'114': {'kind': 'videos', 'media_type': 'video', 'server_types': ('output',)}}
E      Differing items: kind 'images' != 'videos'
```

On a real server, `SaveVideo` publishes under the history key **`images`** — the authority is the lane's
own dump `NEW/VIDEO14B/waveB/raw/run_b3_book4s_a3_history.json`, and that is *why* the lane had already
changed `SAVE_NODE_KINDS["SaveVideo"] = ("images", "video")`. The test, not the code, was stale. **Fix =
assert the measured payload and cite the evidence file in a comment** so a reviewer can see it came from a
real history dump rather than from green-chasing. The `input-only ⇒ ArtifactMissing` half of the test
stayed unchanged.

## The six lint findings (all in files that commit added)

```
tools/v14b_geometry.py:139            F401  PIL.Image unused
tools/v14b_preflight_waveA.py:11      F401  sys unused
tools/v14b_prepare_inputs.py:65       F401  PIL.Image unused
tools/w2_preflight.py:10              F401  hashlib unused
tools/waveB_pick_video_candidate.py:228  F841  `rejected` assigned, never used
tools/waveB_presubmit_state.py:19     F401  subprocess unused
```

For the `F841`, the packet said **do not just delete the variable if it records the rejected candidate** —
prefer using it in the recorded JSON (the rejection is evidence) or an explicit `_ =`. A quiet `del` would
have removed a piece of the comparison record.

## The b4 correction packet's rules (reusable shape)

1. `RULES_LOADED` + `PREFLIGHT_OK`: HEAD `864f63c…`, porcelain empty, and **run the suite first to watch
   it fail** — that is the Step-1 baseline, kept as evidence.
2. Patch-only, preimage kept, no file may shrink.
3. Post-fix: `pytest … -q` must be `26 passed, 1 skipped`; `ruff --select F tools/` must be
   `All checks passed`; both raws captured.
4. **Re-hash the delivered clip in the same round** — `ffprobe` + sha256 must still be
   `55daef67162601a073a2f9de0988b95008b08cbe16e4a36f5567981dba776d04`, 1,645,695 B, 640×360, 120 frames.
   A test fix must never move the artifact.
5. Write `raw/b4_test_drift_correction.json`: RED before, justification for each change **with the
   evidence file cited**, GREEN after, lint before/after, clip-hash re-check.
6. Commit exactly the changed allowlisted paths (never `git add -A`), parent `864f63c…` intact, no
   amend/rebase/push/merge; prove with `--stat`, `rev-parse HEAD`/`HEAD^`, `branch -r --contains HEAD`
   empty, porcelain empty.
7. Append a one-paragraph correction note to `WAVE_B_REPORT.md` stating the row dispositions hold **only
   after** the suite is green, and that the RED-at-HEAD finding was caught by the Manager.

## Row-table handling that kept it honest

F05 and F06 stayed **PASS on behaviour and evidence** — the real run record carried
`allowed_types: ["output"]` with declared terminal nodes, and F06's decoded-index identity was proven by
the pixel map against the delivered clip — while being **RED on their registered tests** at `864f63c`.
Both labels went into the same row, plus an explicit sentence that the table is only trustworthy once the
b4 green run is on disk **and the Manager has re-run the suite itself** at the new HEAD.

The report gained a numbered limitation entry too, with the numbers (`2 failed / 24 passed` at the new HEAD
vs `26 passed` at the previous commit, plus the 6 lint findings) and the attribution: *caught by the
Manager, not self-disclosed by the round*.

## Freeze-id collision (one wasted call)

Writing a companion `SNAPSHOT.md` into `manager/frozen/BOOK_waveA2/` **before** freezing made the id
non-empty, and the freeze tool refused:

```json
{"error": "freeze id exists and is not empty",
 "dest": "…/manager/frozen/BOOK_waveA2"}    # exit 2 — by design
```

Recovery: move the companion doc out to `manager/frozen/SNAPSHOT_BOOK_waveA2.md`, run the freeze (40 files,
3,012,219 B, `hash_mismatch 0`, 0 skipped), then copy the doc in. The refusal is a feature — a correction
must take a **new** freeze id, never mutate a reviewed path.

## Load-bearing numbers

| Item | Value |
|---|---|
| Lane HEAD / parent | `864f63c409a4dcbac92108a96cfaea7896ec3998` / `c4b50325afaf77b132bf0e90aa0d00c2ffb2651f` |
| Commit size | 38 files, `+28530 / −6`, all inside `experiments/mf_reskin_v1/video14b/**` |
| Suite at new HEAD | **2 failed, 24 passed, 1 skipped** (previous commit: 26 passed, 1 skipped) |
| Lint at new HEAD | **6 findings** (F401 ×5, F841 ×1) in the commit's own new files |
| Delivered clip (must not move) | `55daef67…`, 1,645,695 B, 640×360, 120 f, 30/1, 4.000000 s |
| Frozen input subtree | 40 files, 3,012,219 B, `hash_mismatch 0` |
| Chosen raw candidate | `ebf49f80a1b5250c434a1ac0dca5f226909fbd759177e6769a99dbf08da296c0`, 157,300 B (3 paths, same sha) |
