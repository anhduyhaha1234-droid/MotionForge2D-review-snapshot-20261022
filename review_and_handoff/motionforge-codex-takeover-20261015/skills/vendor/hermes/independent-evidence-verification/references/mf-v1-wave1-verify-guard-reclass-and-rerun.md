# MF-V1 wave-1 manager verification: guard reclassification + independent dry-run re-run

Session: 2026-09-22, MotionForge MF-RESKIN-MODEL-UPGRADE wave 1 (3 disjoint CPU workers,
GPU serialised behind a gate). Manager session `20260922_104152_8d11d1`; evidence root
`.../outputs/mf-reskin-model-upgrade-20260922/20260922T0345Z/`.

## 1. The manager composed a protected manifest that overlapped the live write-set

Pre-dispatch capture (`manager/guard/wave2/protected-baseline.json`) listed 52 files: source
film, demo/arm-rig sources, S12 product files, canonical docs, old before/after media, the
GOLDEN fixture — **plus the COMFY adapter modules and tests**, which are that lane's own
exclusive write-set. Pre-dispatch re-verify said `VERIFIED` (nothing had changed yet), so the
composition defect stayed invisible until the first worker actually wrote.

First post-worker verify:

```
{"status": "FAILED", "failures": 7, "files_checked": 52}
 - protected_file_changed | wt-comfy/.../mf_comfy/adapter.py       before 05F41D8A… after C93E39B1…
 - protected_file_changed | wt-comfy/.../mf_comfy/lease.py         before 76C8BA68… after E2AD8720…
 - protected_file_changed | wt-comfy/.../mf_comfy/gpugate.py       before 709718B7… after 55D91758…
 - protected_file_changed | wt-comfy/.../mf_comfy/contract.py      before D1664E05… after 935A6DB9…
 - protected_file_changed | wt-comfy/.../mf_comfy/errors.py        before E2AE2FC3… after FD5B3247…
 - protected_file_changed | wt-comfy/.../mf_comfy/__init__.py      before 754E82E6… after 1EA9885B…
 - protected_file_changed | wt-comfy/.../tests/fake_transport.py   before 178CACB1… after 0A590B5A…
```

Byte attribution (computed against the separate write-set preimage, not guessed):

| file | lines | bytes | direction |
|---|---|---|---|
| `adapter.py` | 442 → 700 | 20,448 → 34,746 | + |
| `lease.py` | 208 → 442 | 7,799 → 17,662 | + |
| `gpugate.py` | 140 → 263 | 4,690 → 10,823 | + |
| `contract.py` | 132 → 136 | 4,828 → 5,067 | + |
| `errors.py` | 196 → 222 | 5,779 → 6,651 | + |
| `__init__.py` | 23 → 36 | 1,093 → 1,367 | + |
| `tests/fake_transport.py` | 236 → 255 | 9,691 → 10,697 | + |

All seven grew; no file shrank; all seven are inside the lane's authorised write-set. So: not
drift, not a violation — **the manager's manifest was wrong**.

Repair (all recorded in the corrected manifest itself, so the reviewer can audit the move):

```python
base = protected-baseline.json            # 52 entries
ws   = writeset-COMFY.pre.json            # the lane's 21 owned files
kept = [f for f in base['files'] if f['path'] not in owned]   # 33 protected-only
corr['files'] = kept
corr['reclassification'] = {'moved_to_task_write_set': moved, 'count': 19,
                            'reason': 'active lane exclusive write-set, not protected files'}
```

Re-verify against the corrected manifest → **`VERIFIED`, failures 0, 33 files checked**. The
lane's own files stay guarded by its write-set preimage + per-file byte snapshots in
`manager/snapshots/comfy-prewrite/` (21/21 snapshot hash-match, 0 mismatch).

**Lesson:** keep protected and write-set manifests disjoint by construction. A protected set
that overlaps a live write-set guarantees a false red on every verify, and a guard that cries
wolf on schedule is worse than no guard.

## 2. Independent re-run of the finished BENCH lane

The lane's report advertised its own reviewer command:

```
cd C:/Users/Admin/Documents/Codex/work/mfv1/wt-bench
python experiments/mf_reskin_v1/bench/run_dryrun.py --steps golden,extract,propagate,stills,negatives,sheets,report
```

Manager ran it verbatim, redirecting the raw into `manager/guard/wave2/bench-rerun-manager.log`:

- **exit 0, 17.7 s, 305 commands** (lane reported 17.5 s / 305) — MATCH.
- All 7 incumbent windows scored **`TECHNICAL_FAIL`** — kept, not softened.
- 10/10 negative controls printed with `proved=True`:
  `frame_count_exact←TAIL_TRUNCATE`, `pts_contract←DROP_RANGE`, `duration_contract←FPS_25`,
  `video_codec_contract←DOWNSCALE`, `audio_contract←NO_AUDIO`, `non_degenerate←BLACK_TAIL`,
  `not_frozen←FREEZE_TAIL`, `not_source_copy←SOURCE_COPY`, `cut_timeline←SHIFT_3`,
  `frame_pairing←SHIFT_3`.

Reproducibility proof — evidence tree hashed before and after the manager run
(`manager/guard/wave2/bench-evidence-pre.json` vs a fresh walk):

```
pre=31 now=31 byte-identical=30 changed=1 added=0
  changed: raw/cmd_transcript.jsonl        # the command ledger the re-run itself appends to
```

The one delta is expected-by-construction; a differing report/metric/media file would have
been the red.

## 3. Lane transport check (BK: keep it apposite)

```
branch  codex/mf-reskin-v1-bench
HEAD    36c912e MF-V1-BENCH: finite QC harness + acceptance checklist, dry-run on frozen artifacts
HEAD^   2594de06cd5b2355e7e874ae4d6deb8a7b5b1b64   == declared wave base  ✔
porcelain  (empty)                                   ✔
files   probe.py 200L, compare.py 171L, assertions.py 358L, sheet.py 67L, run_dryrun.py 591L,
        common.py 130L + CHECKLIST.md 47L / GATE_VOCAB.md 46L / EVAL_PLAN.md 78L
```

Mislabel to avoid: `git log --branches --not --remotes --oneline | head -5` was labelled
"remote refs (must be none)" but returned five commits **including two sibling lanes'**
(`9e57f3e`, `449de4d`, `bf3b28f`, …). It answers "which commits are not reachable from any
remote-tracking ref" — not "is my lane unpushed". Use the §17 three-part check instead.

## 4. Disk accounting that is safe to run

`du -sh` over the lane's model tree hung past the foreground tool timeout once downloads
began (52 GB `diffusion_models`, 17 GB `text_encoders`, 1.2 GB `clip_vision`, 704 MB `loras`,
485 MB `vae`). The safe measurement was the `df -h /c` delta across the download window
(476 GB free → 399 GB free ⇒ ~77 GB fetched), then `du -sh` on the individual
`models/<subdir>` only. Reserve full-tree walks for background jobs with the raw kept.
