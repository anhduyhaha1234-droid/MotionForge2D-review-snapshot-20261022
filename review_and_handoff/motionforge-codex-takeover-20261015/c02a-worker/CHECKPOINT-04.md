# C02A checkpoint 04 — edge-case repairs

- Same goal, owner `/root/motionforge_c02a_coder`, `gpt-6-sol` / `max`, no fallback, and C02A allowlist as checkpoints 02–03. No live jobs/GPU.
- Root's isolated 55-case probe ran as self-review: `root-probe-self-01/RESULT.json`, 55/55 exit 0 on the previous cache hash; copied source and tiny fixtures only.
- Found two additional malformed-record paths. `RED_03.txt` showed a resealed `settings.mode=null` accepted; a one-line cache patch now rejects it. `RED_04.txt` showed deeply nested JSON escaping as `RecursionError`; `load_deps` now returns a controlled failure. `MICRO_06.txt` and `MICRO_07.txt` each show all 11 C02A tests pass after the respective repair.
- Current exact bytes: cache `946935906625d79b95153a92d4cf86310551cfbc4533a3661f2011854aeae7a7` (10018/209), gate `8c2e3f9eedd4d8e11832809c2b72293db17df1fb5a4012bd39fa396f93143f94` (17804/367), C01 test `351c39e764e53d67466688d9ec032cf9e352167e105ee0be580129f1db38fdf7` (14693/330), C02A test `403e45568fddeda038b3f10a62cf3b311764d1e91e7a5f9ef9ca3fbf78877899` (18036/374). Patch receipts 08–11 record each hash/bytes/lines; no shrink.
- Matrix is now 43 shape/type, 8 identity, 12 byte/path, 8 JSON negatives, 5 restored controls, plus real gate/assembly positive and omission negatives. C01 17-test module passed before the two new cache guards; rerun with final source hash.
- Remaining: final 28-test affected module run, fresh independent probe on final bytes, static/self-review and protected-scope guard, final immutable diff/manifest/report/raw receipts/checkpoint. C02B limitations unchanged.
- Next command: run both affected unittest modules together with isolated fixture environment, then fresh root probe using a new output directory.
