# Correction-round immutable evidence & RED-first repros (S10-C6C→C6D, 2026-09-01)

Detail bank for Manager-side reproduction/evidence hygiene in bounded
correction rounds. Trigger: a Codex review returned CHANGES_REQUESTED and the
next packet authorizes "fix only these findings, then exit-gate".

## Why: the P2 evidence-integrity finding

Codex's C6C review (S10_C6C_PM_REVIEW_2026-09-01.md §4) flagged that Manager
files under `output/s10/c6c/manager/prep/repro_f1_result.json` etc. were
OVERWRITTEN at 17:08, after EXIT_VERDICT.md (16:56) — re-running the repro
scripts onto the same paths mixed post-fix output into a `prep` (pre-fix)
location, and one file still claimed the (now fixed) CAS was absent. Review
boundary: evidence must show what the tree looked like BEFORE the worker's fix,
and it must stay that way forever.

## Rules that follow

1. **Never reuse a prior round's evidence paths.** Round evidence lives under
   `output/s10/c6X/...` (one dir per packet round). Within a round:
   - `before/<finding-name>/**` — reproduction run on the PRE-FIX tree,
     written once, frozen the moment the worker is dispatched.
   - `after/<finding-name>/**` — same reproduction re-run post-fix into NEW
     paths (no shared filenames, no overwrites).
   - Manager's own re-verifications after EXIT go into a NEW subdir or get
     appended as lines in EXIT_VERDICT/registry — never onto a `prep` path.
2. **Do not re-run `before/` while the worker owns the tree.** Single-writer
   rule + the worker is editing `tests/` helpers the repro imports via
   importlib — a re-run mid-flight can read half-written helpers and produce
   non-representative results. If a verification hook flags staleness, re-run
   the `after/` equivalents or the focused suites, not `before/`.
3. **Treat any Codex P1/P2 on evidence as a first-class finding.** It lands in
   the next packet's requirements (C6D §4: "Không overwrite before/** sau khi
   worker sửa. Post-fix phải ghi mới vào after/**").

## RED-first contract repro pattern (proves defect AND fix objectively)

Write each reproduction as a pytest that asserts the CONTRACT (what correctness
looks like), not the defect:

- Failing NOW (pre-fix) = defect recorded; passing after the worker's fix =
  flip evidence. Same file, same assertions, two runs, two stated outcomes.
- **Write the evidence JSON sidecar BEFORE the asserts** — if the assert fails,
  the observed rows/bodies are already persisted to disk (pytest failure alone
  loses the payload).
- Sidecar content: HTTP status/body per step, run rows, durable-job rows
  (id, job_type, owner_type/owner_id, state, attempt, idempotency_key,
  input_manifest_json), expected-vs-actual manifest, and the boolean checks
  dict (C1/C2/C3...) so Codex can diff check-values across before/after.
- Use real route + real JobService + one fresh isolated SQLite per sequence
  (monkeypatch a `_Boom(JobService)` subclass raising in `create_job` for
  forced enqueue failure — the route resolves the service via
  `deps._job_service`, so `monkeypatch.setattr(deps, "_job_service", boom)`).
- Reuse test helpers without making `tests/` a package: `importlib.util.
  spec_from_file_location` + `sys.modules[name] = mod` (C6C/C6D proven).

## Repo-root discovery: path-depth-tolerant, not parents[N]

`Path(__file__).resolve().parents[5]` is brittle — the correct index depends on
how deep the evidence dir nests (C6C prep was parents[5]; C6D
`before/<finding>/` became parents[7]) and silently produced
`FileNotFoundError` against `output/s10/tests/...`. Use:

```python
_ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "tests" / "test_s10_full_apply_api.py").exists()
)
```

## Bounded-round model probe (exact selector, before dispatch)

- Probe via the exact owner resume: `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900
  hermes --resume <owner> --provider custom -m "<exact-model>" --yolo -z
  "Preflight model probe — reply exactly MODEL_PROBE_OK"`; success =
  `MODEL_PROBE_OK` in log + exit 0. Ledger under
  `output/s10/c6X/manager/prep/model/**`.
- The packet's model override is per-round (C6C: GLM → rejected by review for
  cost/speed; C6D: user re-selected `BAI/deepseek-v4-flash-vision-exp`).
  Record which round used which selector; never carry a prior round's model
  forward.

## Heartbeat cron: script location constraint

`cronjob script` must be a bare filename under `~/AppData/Local/hermes/scripts/`
(copy the collector script there; absolute or worktree paths are rejected with
"Script path must be relative to ~/.hermes/scripts/"). `mkdir -p` first, then
`bash -n` to syntax-check, then register; set heartbeat model per standing user
instruction via `hermes cron edit <id> --model comboBAI --provider custom`
(after creation, since create doesn't take model).
