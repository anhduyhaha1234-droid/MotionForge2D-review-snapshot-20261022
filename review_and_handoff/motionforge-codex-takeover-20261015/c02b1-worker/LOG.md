# C02B1 worker log

Task: `CODEX-C02B1-STAGED-SOURCE-FRESHNESS`. Owner: `/root/motionforge_c02b1_coder`, GPT-6 Sol Max, no fallback. One CPU writer. Scope: `r6_common.py` stage-frame helpers/imports, the new C02B1 test module, and this worker evidence directory.

- Read the complete current canonical rules, packet, MAIN `AGENTS.md`, `SESSION_PROTOCOL.md`, C02A approved verdict, preflight, active skill digest, three pinned skills, common helper and two call sites. All 28 pinned live files and byte snapshots matched; the new test did not exist.
- Copied `r6_common.py` to `preimages/r6_common.py`; both SHA256 `17bf5799c445a6f7133c61d53b9d5c41083307add1d7b6a50acdf83c294c15e3`.
- Fresh baseline `root_probe_c02b1_staging.py --source <preimage live source> --out c02b1-worker/baseline-probe`: exit 1, 2/7. Raw `baseline-probe/RESULT.json` and `baseline-probe-stdout.json` retained.
- New isolated regression `test_same_path_same_size_source_mutation_reextracts`: exit 1 against old helper, with stale `FRAME-SOURCE-A-0` after `SOURCE-B`. Raw `test_red_01.log` retained.
- Bounded common helper patch; post-patch SHA256 `9c4ba658d0f1455d96c8038f8a1703f9b091d78a3d1506d02e05cc7120c481dc`, 10,578 bytes, 241 lines. First focused test exit 0, 1/1 in `test_green_01.log`.
- Incremental S1–S3 module: exit 0, 5/5 in `test_matrix_s1_s3.log`. Incremental S4–S5 module: exit 0, 9/9 in `test_matrix_s1_s5.log`.
- Full new module with real FFmpeg fixture: exit 0, 10/10 in `test_matrix_s1_s6.log`. Fixture command, raw return codes, actual source MP4s and staged PNGs, and decoded center pixels retained under `real-ffmpeg-rx7q9lr_/RESULT.json`.
- Fresh post-patch seven-case root probe: exit 0, 7/7 in `post-probe/RESULT.json` and `post-probe-stdout.json`.
- Full approved C01 module: exit 0, 17/17 in `test_c01_full.log`. Full approved C02A module: exit 0, 13/13 in `test_c02a_full.log`.
- Read-only scope audit: exit 0, `AUDIT.json` reports 27 protected hashes and all 28 preflight snapshots unchanged, no unexpected Python files or duplicate definitions; `common.diff` contains only stage-frame helpers/imports and the stage-frame replacement.

Checkpoint sequence: `CHECKPOINT_01.json` through `CHECKPOINT_07.json`. No GPU, Hermes, production media extraction, Git operation, model/runtime/DB mutation, or source/test write outside the two allowed paths. No live child job remains.
