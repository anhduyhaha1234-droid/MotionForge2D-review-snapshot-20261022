# S12-C1 INT01 merged gate + route-quota switch (2026-09-09)

Real transcript: W4 T03C `9a91e18`, W5 T05 `76bd79f`, W6 T06A `00d1084` all
TASK_SUBMITTED on task branches; W7 T06B re-measured green on the SAME SHA
`48bf514` (zero-diff verifier). INT01 merged all four onto canonical
`0d2e063` → `5a38e73`, then the merged gate found exactly one real finding.
Full Manager-only (zero model calls for every gate step).

## 1. Duplicate test basename breaks full-tree collection on the merged gate

Every C1 lane adds its own `tests/s12/s12-t0X/test_c1_closure.py`. On the
merged canonical a single `python -m pytest tests/s12/` dies at COLLECTION:

```
import file mismatch:
imported module 'test_c1_closure' has this __file__ attribute:
  .../s12-t01/test_c1_closure.py
which is not the same as the test file we want to collect:
  .../s12-t02/test_c1_closure.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename
```

Root cause: several lane dirs (`s12-t01`, `s12-t02`, `s12-t04a`) lack
`__init__.py`, so pytest's prepend import-mode treats the shared basename as
one module. This is NOT a code defect and NOT a merge conflict — do not
open a correction for it.

Workaround ladder (verified):
- `--import-mode=importlib` alone does NOT fix it — it then breaks the
  lanes that use `from conftest import X` (`ModuleNotFoundError: No module
  named 'conftest'`, t04a/t06b). Skip it.
- Robust fix: run the gate PER PACKAGE DIR with a SHORT per-dir basetemp and
  sum the counts:
  ```bash
  for d in s12-t01 s12-t02 s12-t03a s12-t03b s12-t03c s12-t04a s12-t06b; do
    python -m pytest "tests/s12/$d" -q \
      --basetemp="C:/Users/Admin/AppData/Local/Temp/s12_$d" -p no:cacheprovider | tail -n1
  done
  ```
- Each dir individually is green (T01 31, T02 36, T03A 44, T03B 32, T03C 19,
  T04A 48, T06B 11+1skip). Full-tree single invocation is simply the wrong
  shape for this suite; record the per-dir matrix in the INT01 evidence.

## 2. A test that documented a pre-fix bug fails on the merged tree — route
   the TEST update, never re-open production

T06B `test_f3_provenance_decides_not_filesize` asserted the OLD behavior
(`classify_source_kind(bare 3840x2160, no provenance) == "native_4k"`) as a
"documented known bug" (F-OBS-01, dims-only fallback). T01-C1 `0d5bc77`
closed F-OBS-01 in production (bare dims now classify `upscale_4k`). On the
merged canonical the T06B test FAILS with `AssertionError: 'upscale_4k' !=
'native_4k'` — while the same test PASSED on T06B's own branch (pre-fix
prod, zero-diff verifier).

Lesson: when an INT01 merged gate fails on a lane that documented a known-bug
behavior, the fix is to route the TEST update to that exact owner — update
the assertion to the new behavior + add a note `F-OBS-01 closed by <owner-Cx
commit>` — NOT to re-open the production owner or patch production back.
The verifier worker reports the updated test FAILING locally on its own
branch BY DESIGN (its tree still has pre-fix prod) and PASSING on canonical
merged with the fix — that is correct and expected; do not require the lane
branch to turn green before merging. Merge the test update, re-run the
per-dir gate on canonical → green.

## 3. Route quota 429 with reset timestamp — log blocker, switch to the last
   user-authorized alternate route

Mid-INT01 the `cmc/meta/muse-spark-1.3-contributor` worker dispatch returned:

```
API call failed after 3 retries: HTTP 503: [commandcode/...-contributor] [429]:
You've reached your weekly usage limit for your plan. Your limit resets at
2026-09-11T17:23:2x
```

This is a DETERMINATE quota/auth blocker (reset timestamp given), NOT a
transient connection error — Rules §7's 5-min-retry loop does NOT apply; do
not retry the dead route in a loop. Procedure:
1. Record the raw error + reset time in a `BLOCKER_LOG.md` at the evidence
   root immediately (do not just retry).
2. Switch the pending worker resume to the LAST route the user explicitly
   authorized this session (here `ocgfree/muse-spark-1.3-contributor-free` @
   provider custom, previously user-chosen 2026-09-08 ~19:4x) and continue
   the SAME exact owner session with the new `-m/--provider` pin.
3. Note the switch in the blocker log + registry; the correction lands and
   the gate continues. Report the blocker to the user lead-with-status in
   the same turn (reset time included).

## 4. Escalation confirmed: ack-only lifecycle lanes get the harness run by
   the Manager, then a commit-only order

T06A (W6) acked 5 times across ~2h with tip frozen at `ddc5d05`, no gate
output. Manager executed the FULL harness itself with zero model calls:
`preflight` READY → `build_manifest` (build_id `SMMKnaiyQ5jEj09fkhU72`) →
`setup` → `serve` (backend pid :8423 HTTP 200, frontend pid :3123 HTTP 200)
→ `diagnose` (pids alive, free 520473 MiB) → `stop` (ports `000` = down) →
`uninstall` (data PRESERVED) → `ruff check --select F scripts/s12/` → `git
diff --check`. Then a commit-only resume landed `00d1084`. Note: `diagnose`
and `stop`/`uninstall` take ONLY `--install-root` (no port args — the ports
are read from RUNTIME.json), so a `--backend-port` on diagnose fails with
`unrecognized arguments`; drop them and pass just the root.
