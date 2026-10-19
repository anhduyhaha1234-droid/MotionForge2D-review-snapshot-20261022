# S10-T04A Continuation — J1→J5 Verified (27/08 23:38 → 28/08 02:00 +07)

Manager `20260827_220742_de1883` meta/max/TTFB900/fallback OFF on `codex/s08-integration` HEAD `d3f6f79`.
DAG: `PREP → (T01A ‖ T01B) → J1 → T01C → J2 → T02 → J3 → T03 → J4 → T04A → J5 → T04B → J6 → T04C → EXIT`.

## Verified waves
| Phase | Task | Allowlist (exclusive) | Tests ×2 | Manager re-verify | Gate |
|---|---|---|---|---|---|
| W1‖ | **T01A** durable domain | models.py + s10_full_apply.py + schemas + 1 migration `a10b11c12d3e` (down `b3c4d5e6f7a9`, single head) + 2 domain/migration tests | 21 (15+6) | `cd worktree && MOTIONFORGE_DATABASE_URL= pytest … -p no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>` 21.09s ×2, `alembic heads` from worktree cwd = `a10b11c12d3e`, `git diff --check 0` | J1 part |
| W1‖ | **T01B** planner pure | s10_chunk_plan.py + test 26 | 26×2 1.63s pure (no DB/IO/time/process/path, canonical JSON sort_keys, chunk_id ck_<sha16>) | isolated basetemp, ruff isolated pass vs pyproject E501 P2 documented | J1 part |
| J1 | — | — | **47×2** combined 21.09s/20.87s, 38 warnings SAWarning only | alembic/mypy/ruff/diff full green | **MANAGER_VERIFIED 00:30** |
| W2 | **T01C** orchestration | s10_full_apply.py + s10_full_apply_jobs.py + routes/s10_full_apply.py (+bounded app.py/deps.py) | 11 (7 api +4 workflow) 54s | checkpoint durable before stop + fresh resume skips verified only, cancel zero false pub, dedupe vs distinct lineage, atomic write | J2 58×2 → **VERIFIED 01:00** |
| W3 | **T02** multi-role | s10_multi_role_apply.py + bounded shims | 30×2 1.67s | group 2chars+prop+fg not flattened, per-role pinned route/pack/attempt, isolation on failure, contact/z-order survive overlap, schedule invariance | J3 88×2 → **VERIFIED 01:17** |
| W4 | **T03** recompute | s10_recompute.py + bounded S10 files | 9×2 15.8s | mask/z-order/contact/route/asset closure + overlap dependents, unaffected preserved exact IDs/SHA, affected attempt+1 provenance, replay dedupe, stale/cross fail-closed, restart resume | J4 97×2 → **VERIFIED 01:40** |
| W5 | **T04A** structural | s10_structural_compare.py + bounded S10 | 27×2 1.61s | frame/timebase/shot/cut exact, trajectory median 0.5% P95 1.0% scale 3% rotation 3° contact 1.0% diagonal, zero z-order/visibility, clipping silhouette guard, NaN/missing/policy guards, REVIEW_REQUIRED only when all pass | J5 124×2 → **VERIFIED 02:00** |

## Traps captured at J1 (see s10-j1-gate-verification.md for full recipe)
1. **Alembic CWD trap** — `alembic.ini` `script_location = migrations` relative; running from MAIN (4 migrations) hides 13 worktree revisions. Every gate must `cd worktree` before `alembic heads/history/current/upgrade`. Verify via `ScriptDirectory.from_config` if unsure.
2. **Pytest invocation trap** — `pyproject.toml` addopts break `pytest --cache-clear`; correct is `pytest … -v -p no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>`.
3. **Prompt heredoc EOF trap** — Vietnamese diacritics inside `cat <<'EOF'` broke bash heredoc matching (`unexpected EOF while looking for matching '''`). Fixed by writing prompts via `execute_code` Path.write_text (ASCII fallback without diacritics) instead of shell heredoc.
4. **Shell & trap** — foreground terminal rejects `&`; use `terminal(background=true, notify_on_complete=true)` per lane.
5. **Gateway 524** — T01A first dispatch 23:40 hit `524 Gateway request failed` retryable → RUNNING_RETRY_WAIT per Rules §7: wait 5' then `hermes --resume <same-session> -z "$(cat prompt)" -m meta --yolo` (same model/TTFB, not new session). Retry succeeded 23:58 with `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900`. Never create fresh session for retryable provider error.

## Manager discipline that held
- Prompt dispatch via file `output/s10/<lane>/prompt.txt` + `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes -z "$(cat …)" -m meta --yolo`; resume same owner with `--resume`.
- Liveness = `↻ Resumed session` + log delta + PID/CPU probe; compression silence vs real stall vs router-wide TTFB distinguished per skill.
- Heartbeat ≤30' + instant on lane exit/blocker; every `chạy đi` + ETA co-occurrence answered in same reply with `date`-anchored wall table + DAG progress.
- Each join: Manager re-runs decisive `pytest ×2` with fresh basetemp + `alembic heads` from worktree cwd + `ruff/mypy/git diff --check` + allowlist/forbidden audit before MANAGER_VERIFIED.
- Pre-existing dirty `models.py + app.py` (290+7) carried from T01A; later lanes did not extend tracked diff — verified via `git diff --stat` (only tracked files) vs `git status --short` (includes untracked new allowlist).

## Carry-forward P2
E501 line-length on long SQL/doc/test lines across T01B/T01C/T02/T03/T04A — isolated ruff pass, pyproject line-length 100 flags it; documented P2 not blocking. Fix with import-sort / line-wrap at final hardening if desired.
