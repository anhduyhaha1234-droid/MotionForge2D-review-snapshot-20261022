# G2-PREP-01 transport handoff

**Status:** `SELF_VERIFIED_PENDING_ROOT_REVIEW` for transport/preflight only. G2 exact 300-second pilot: `NOT_RUN`. Media readiness: `NOT_ASSESSED`.

## Authority and scope

- Frozen input: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-04-20261020/submissions/g1-candidate-16`, manifest SHA-256 `4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82`, 74 declared files.
- Codex G1 review: `C:/Users/Admin/Documents/Codex/g1c16-review/REVIEW_G1_C16_VI.md`, SHA-256 `8a466b1aa14b1a1761b69c75540213bcd631c5add749ea8e9acdceb90f8fcfdc`. Guard JSON SHA-256 `ccc43a4808f10772128c490c2aa227d3708714fceaf9f275160e61acb35799a7`; guard process receipt SHA-256 `47d092661bf5c86c61ffc569ffe02861bf60f67ae1d2b608e20debafbee1c47e`, exit 0.
- Original video: `C:/Users/Admin/.gemini/antigravity/scratch/goha_mmo_clone/backend/downloads/Tại sao thật tệ khi ĐỨNG TÊN HỘ công ty？.mp4`, 36,971,916 bytes, SHA-256 `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`; ffprobe H.264/AAC, 640×360, 30/1 fps, 1321.215420 seconds.
- Exclusive write root `C:/Users/Admin/Documents/Codex/g2p01-transport/` was absent at preimage. All created files are beneath it. Frozen C16, original source, owner work, MAIN, old RUN, GPU and ComfyUI were not written.

## Implementation and failure semantics

`transport.py` pins the review, guard, guard process, C16 manifest, and video; it checks full C16 relative-path inventory, size and SHA-256 before copying. It rejects reparse inputs, malformed or case-colliding manifest paths, output escape, nested/duplicate pilots and receipts. It copies every manifest-declared file plus `MANIFEST.json` and a byte copy of the video to a new pilot root at `task/source/source_full.mp4`. It hashes every copied file, compares the exact 76-file postimage, and rechecks original authority/input bytes. `xb` and a new directory prevent overwrite. Blocked preflight returns 2 and records a UTC receipt without creating a pilot; an unexpected error returns 3. If failure occurs after pilot creation, the partial directory is retained for investigation.

The CLI accepts only the pinned C16 and source paths. The Python API accepts read-path overrides for disposable negative fixtures, while retaining all hash and authority pins. No candidate code was imported or executed. Python ran with `-B`; frozen C16 has zero `.pyc` files.

## Repro and raw evidence

Working directory for the Python commands: `C:/Users/Admin/Documents/Codex/g2p01-transport/`.

1. `python -B 'C:/Users/Admin/Documents/Codex/g2p01-transport/negative_repros.py'` → process exit **0**. Its eight challenged transport calls each returned **2** with the expected block code: missing source, same-size tampered source, extra `.pyc`, missing C16 file, same-size changed C16 file, escaped pilot path, existing pilot, and existing receipt. No attempted new pilot was created; the existing pilot sentinel and existing receipt stayed unchanged. Raw summary: `negative-repros/23798ccf12e1/NEGATIVE_SUMMARY.json`, SHA-256 `82fcf81a599469a1d7bf81e8f8c5b52cc1676d9b228e5357cf7b6cdf370a6ada`; each case links to its raw UTC receipt.
2. `python -B 'C:/Users/Admin/Documents/Codex/g2p01-transport/transport.py' --pilot 'C:/Users/Admin/Documents/Codex/g2p01-transport/pilot-g2p01-001' --receipt 'C:/Users/Admin/Documents/Codex/g2p01-transport/receipts/positive-001.json'` → process exit **0**, `SELF_VERIFIED_PENDING_ROOT_REVIEW`. Raw receipt: `receipts/positive-001.json`, SHA-256 `e9bf67facc7e6a0debc0d8251460551a26d7cface9a264ae8d78f3ec388bb47f`; it includes UTC start/end, paths, expected and observed SHA-256, raw ffprobe stdout/stderr/exit, 74 source entries, 76 copied entries, and post-copy rechecks.
3. `& 'C:/Users/Admin/Documents/Codex/g2p01-transport/verify_postimage.ps1'` → process exit **0**, `POSTIMAGE_VERIFIED`: 75 frozen candidate files including manifest, 76 pilot files, zero candidate `.pyc`, all 74 manifest-declared bytes correct in both places, and original/copied source both at the pinned size/hash.

Pilot: `C:/Users/Admin/Documents/Codex/g2p01-transport/pilot-g2p01-001/`. Its `MANIFEST.json` SHA-256 is the C16 pin; `task/source/source_full.mp4` has the source pin. Implementation SHA-256: `transport.py` = `c72bf8cbed600f3882affcfccba849dbbd7934c21312d30c2ab95745d94193d6`; negative harness = `5d5a1bfaea0da10703a978461f920802543070bf6bbe250667c1a63723c5108d`; independent verifier = `81b7b46932d936724ff185dc3fb50b95b76d79bbe344a264dbca19aa4c1d502c`.

## Stop boundary

This transport proves bytes and source media shape. It does not establish CAST/assets, runnable media environment, process/queue/lease clearance, render quality, or product acceptance. The G2 exact 300-second pilot requires root review and a separate process/queue/lease audit before any inference or render.
