# S11 W1–W3 annotated playbook (run 2026-09-03)

Real transcript of a successful 19-ID/14-wave full-sprint Manager run start.
Reuse these exact shapes; replace task tokens/wave bases per sprint.

## Preflight (activation) — all 8 checks in ~15 min

```bash
# authority hashes (verify vs prompt Expected):
sha256sum "MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md" \
  "…/s08-integration/output/s11-post-t01-readiness/r1/synthesis/S11_T02_T06_PRODUCTION_PLAN.md" \
  "…/s11-integration/docs/pm/sprints/S11-SPRINT_CONTRACT.md"
# git activation:
git rev-parse --abbrev-ref HEAD && git rev-parse HEAD        # == activation HEAD
git status --porcelain | wc -l                                # 0
git ls-remote origin codex/s11-integration                    # == local HEAD
git fsck --no-reflogs                                         # broken turn-diff capture refs: RECORD, don't delete
# env + processes:
env | grep -i -E "MOTIONFORGE|DATABASE" || echo NO_DB_ENV     # must be unset
tasklist //FI "IMAGENAME eq python.exe"                        # zero workers
# alembic + openapi + s10/t01:
python -m alembic heads                                        # exactly 1 head
python -c "from app.api.app import app; …opIds dup check…"    # zero duplicate operationIds
python -m pytest tests/test_s10_full_apply_api.py -p no:cacheprovider --basetemp=%TEMP%/mfc_… -q   # 71/71 fresh
python -m pytest tests/test_s11_original_audio_*.py tests/test_s11_attach_original_audio_job.py --collect-only -q  # 64 tests
# plan structural parse: 19 unique IDs, W1..W14 order, parallel-only W6/W9/W12 (python regex on ^### (W\d+) · (T\d{2}[A-Z0-9]+) )
```

Observed values (09-03): head `77515982`, alembic `a10b11c12d3e`, OpenAPI
263 paths/329 ops, S10 route `5A6C7E86…`, API test `E26A96DC…`, exec prompt
`57E9434A…` (MAIN docs/pm/prompts/ — verify BEFORE dispatch).

## Evidence root

```
C:\Users\Admin\MotionForge2D-evidence\s11-production\
  manager\{ledger\REGISTRY.md, gates, int01\{charter,waveN_merge.md,waveN_push.md,*.log}}
  <TASK-ID>\<token>\{prompt.md, baseline_manifest.json|txt, dispatch.log}
```

Registry table columns (proven shape):
task | worktree | branch | WAVE_BASE | session | writer state | commit range
| Manager verdict | integrated remote SHA.

## INT01 charter (create once, resume every wave)

Prompt: single Git-only owner; authorized scope = canonical index/refs via
`git merge --ff-only` (serial) / `--no-ff --no-edit` siblings (parallel);
pre-merge pre-image checks (porcelain 0 + ls-remote == base); conflict ⇒
abort + `BLOCKED_INTEGRATION_CONFLICT`; push `HEAD:refs/heads/codex/s11-integration`
non-force only after Manager's green wave gate; verify ls-remote == local.
Init: `hermes chat -q "$(cat charter.md)" -m ocg/deepseek-v4-flash --provider custom -Q`
→ session `20260903_112116_35051c`. Every wave resume: add `--resume <id>`.

Wave merge prompt (INT01): state exact verified range
`<BASE>..<HEAD>` (2 commits), serial ⇒ ff-only, evidence
`output/s11/int01/waveNN-merge.md`, NO push yet.
Wave push prompt (INT01): after Manager gate green, pre-push proof, push,
ls-remote verify, evidence `waveNN-push.md`.

## Task packet shape

- §1 worktree/branch/WAVE_BASE (absolute paths, porcelain=0 proof)
- §2 model route (exact, no-fallback)
- §3 BINDING TASK BLOCK **verbatim** from the binding plan (all 8 fields:
  Outcome / Depends-on / Write-set / Forbidden / Tests / Session rule /
  Acceptance / Trace) — say "SHA … — authority; line anchors chỉ là hint"
- §4 byte-safe protocol (existing = bounded patch; NEW paths only whole-file;
  shrink ⇒ BLOCKED_UNSAFE_WRITE; isolation flags: `-p no:cacheprovider`,
  short Windows-native basetemp `C:/Users/Admin/AppData/Local/Temp/mfc_<task>_<seq>`,
  `env -u MOTIONFORGE_DATABASE_URL`)
- §5 required sequence: porcelain 0 → alembic heads → RED → implement →
  GREEN → ruff `--select F` → self-review diff vs WAVE_BASE → stage
  allowlist + docs/pm/sessions/<task>/** → commit local → TASK_SUBMITTED → exit
- §6 evidence files

Baseline manifest before dispatch: sha256/bytes/lines of every existing
allowlisted/protected file (python hashlib reading RAW bytes; note CRLF).

## Wave loop (proven cadence)

dispatch → worker ~35–45 min → EXIT `TASK_SUBMITTED` with session_id →
Manager audit (porcelain, `git log --oneline -3`, `git diff --numstat BASE`
zero deletions, forbidden paths absent, router grep for mutation methods,
race pattern `on_conflict_do_nothing`, OpenAPI before/after diff) →
fresh-basetemp pytest re-run + alembic heads + ruff F →
`MANAGER_VERIFIED_PENDING_SPRINT_REVIEW` → INT01 merge (ff-only) → wave gate
in disposable `s11-verify-wN` detached worktree at integrated HEAD (all
wave task suites + regression collect + OpenAPI + alembic) → INT01 push →
ls-remote verify → next wave base = pushed SHA → next task (full-sprint
exception: open next dependency without waiting Codex).

## CRLF attribution case (do this before declaring drift)

```python
b = open(p,'rb').read()
lf = hashlib.sha256(b.replace(b'\r\n', b'\n')).hexdigest()  # compare vs pinned/committed blob
```
Case: T01 engine pinned `19e5fc01…`; disk sha256 `bf140c62…`, porcelain 0 →
LF-normalize == `19e5fc01…` == blob at activation HEAD. Stale pin case:
T01 acceptance `28244b02…` (handoff 08-23) vs committed `8a8b912b9b…` —
verified identical at d3f6f79, 4cec376, ee10e55, 77515982 → attributed
stale pin, recorded for Codex, not a blocker.

## ETA answer shape (user: "estimate bao giờ xong hết")

`date` first → status line (waves done / current wave) → per-wave ETA table
with time anchors → cam kết band + buffer disclosure + "báo NGAY nếu lệch".