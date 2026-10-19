# C02A checkpoint 01 — validation core

- Goal: strict v3 recorded dependency validation and actual key/assembly wiring, CPU only.
- Owner/model: `/root/motionforge_c02a_coder`, `gpt-6-sol` / `max`, no fallback; root reviews independently.
- Allowlist: `R6/scripts/r6_cache.py`, necessary `R6/scripts/r6_gate.py`, new C02A test, fixture-only C01 test, `OUT/c02a-worker/**`.
- Preflight: root `C02A_PREFLIGHT.json` `ok=true`; 27/27 current source/test paths and root snapshots matched SHA/bytes/lines. Own 27 byte-matching snapshots in `PREIMAGES.json`. MAIN Git tree dirty preexisting; untouched.
- Baseline: `BASELINE_EMPTY.txt` showed `(True, 'ok')` for empty deps. `RED_02.txt`: empty record and missing gate deps failed as expected; builder positive exposed old signature.
- Landed: new C02A test `10dde7683ba2b5da9a8e6754b5d6c06fd274c3cf9ebbaa907c317d6234169f50`, 4386 bytes, 102 lines; cache `4a6a78c890e8c45bdd689ddc852efc5d9bed5638b4d63a524005b40de076b5b0`, 9970 bytes, 207 lines. Root preimage cache `29a9e7b0f60304a56692d21fd229ef884dd93064fd4376eec7ab030daaf304c6`.
- Decision: public `verify_deps(dep, sid=None, fid=None)` retained; requested identity and `K.PLAN` checked before path reads. Strict `load_deps` rejects duplicate fields/non-JSON constants. Generated keys require graph; explicit no-visible-actor passthrough may omit graph and asset lists.
- Micro test: `python -B -m unittest discover -s tests -p test_codex_c02a_dependency_verification.py -v` exit 1; `MICRO_01.txt` shows builder positive + empty negative pass; missing-deps gate still fails until consumer wiring.
- Next: bounded gate patch for strict load/verify before review; then add finite negative matrix and C01 fixture setup. No live jobs or GPU work.
