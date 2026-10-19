# S10 J1 Gate — 47×2 Join Verification & Three Pitfalls (verified 2026-08-28 00:30)

J1 closed `PREP -> (T01A || T01B)` at `MANAGER_VERIFIED` after both workers `TASK_SUBMITTED` and Manager re-ran every decisive command from disk. Three pitfalls would each have given a false gate verdict.

## Gate result

- Worktree: `codex/s08-integration` HEAD `d3f6f79` + T01A/T01B untracked allowlist files.
- T01A: `app/persistence/models.py` (+290), `app/persistence/s10_full_apply.py`, `app/schemas/s10_full_apply.py`, migration `a10b11c12d3e` (down `b3c4d5e6f7a9`, one head), tests `15 domain + 6 migration = 21`.
- T01B: `app/services/s10_chunk_plan.py` (pure, no DB/IO/time/process/path), tests 26 (6-bullet determinism).
- Combined isolated re-verify `cd <worktree> && MOTIONFORGE_DATABASE_URL= pytest tests/test_s10_full_apply_domain.py tests/test_s10_full_apply_migration.py tests/test_s10_chunk_plan.py -v -p no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>`: **47 passed ×2** (38 warnings `SAWarning: skipped unsupported reflection of expression-based index` only), 21.09s / 20.87s.
- Alembic: `cd <worktree> && alembic heads` → `a10b11c12d3e (head)`, `alembic history` shows the 17-step chain `<base> -> a1b2c3d4e5f6 -> … -> b3c4d5e6f7a9 -> a10b11c12d3e`.
- Ruff: `app/persistence/s10_full_apply.py` + `app/schemas/s10_full_apply.py` + `models.py` → `All checks passed`. `s10_chunk_plan.py` alone under `pyproject.toml line-length 100` reports 3× E501 (lines 56/62/64, 107–130 cols) but worker's `ruff --isolated` was `All checks` — P2 carry-forward, gated T01B owner only, not blocking J1.
- `mypy --strict` on 3 files → Success.
- `git diff --check` → 0; `git status --short` → only allowlist (`M models.py` + `??` new allowlist) plus pre-existing manager probes (`560`, `probe_*.js`, `.codex-review`).

## Pitfall 1 — Alembic CWD trap (would report stale head)

`alembic.ini` has `script_location = migrations` (relative). Manager's shell `cwd` at that phase was `C:/Users/Admin/MotionForge2D` (MAIN, 4 migrations). Running bare `alembic heads` from there returned `d5e6f7a8b9c0 (head)` — hiding all 13 worktree revisions and making J1 look like the T01A migration never landed.

Recovery: `cd C:/Users/Admin/MotionForge2D-worktrees/s08-integration && alembic heads/history`. Rule: **every alembic invocation in an S10 Manager gate must `cd <worktree>` first** — the integration worktree is the authority, not MAIN. Verifying via `ScriptDirectory.from_config` after `chdir` also works; grepping file-level `revision`/`down_revision` strings does not prove reachable heads.

Evidence of the trap is still in the session transcript:

```
alembic -c "C:/Users/.../s08-integration/alembic.ini" heads  → d5e6f7a8b9c0 (head)
cd ".../s08-integration" && alembic heads                    → a10b11c12d3e (head)
```

## Pitfall 2 — `pytest --cache-clear` breaks on this pyproject

Worker's gate recipe `pytest --cache-clear --basetemp=$(mktemp -d)` fails on this repo:

```
pytest: error: unrecognized arguments: --cache-clear
inifile: .../s08-integration/pyproject.toml
```

The repo pins `addopts` that conflict with bare `--cache-clear`. Correct isolated form (verified for both J1 runs above):

```
pytest <tests> -v -p no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>
```

`--cache-clear` without `-p no:cacheprovider` fails; bare `--basetemp` without the override inherits `addopts` and can break different tests. Record the basetemp path in the registry per run.

## Pitfall 3 — Prompt file write via heredoc on Vietnamese content

Attempting `cat > output/s10/t01a/prompt.txt <<'PROMPT_T01A_EOF'` with multi-line Vietnamese containing interior `'` quotes died:

```
/usr/bin/bash: -c: line 59: unexpected EOF while looking for matching `''`
```

Any stray `'` on a line collides with the quoted heredoc delimiter. Fix in the same Manager session: `Path(...).write_text(p1, encoding="utf-8")` via `execute_code` (Python `r"""..."""` keeps interior `'`/`"` inert), verified with `wc -l` + `sha256sum` — T01A 45 lines `efa65bfc...`, T01B 37 lines `0cf09d05...`. Follow-up dispatch must use `terminal(background=true, notify_on_complete=true, command="HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes -z \"$(cat .../prompt.txt)\" -m meta --yolo")` — no trailing `&`.

## Dispatch retry note (same J1 window)

T01A's first attempt died pre-prefill with `statusCode 524 Gateway request failed isRetryable=true` at 23:46; per Rules §7 classified `RUNNING_RETRY_WAIT`, waited 12m then `hermes --resume 20260827_234001_9d7f39 -z "$(cat prompt.txt)" -m meta --yolo` as `proc_fde510fe01a5` pid 28140. Resume resumed same session context; second launch completed gates that `head | 50` had truncated — full worker result recovered via the resume, not the truncated head.

## What J1 depends on next

T01C was dispatched at 00:31 as `proc_94190cff1509` pid 22868 on the verified J1. Its preflight must re-check `alembic heads` from worktree cwd, `MOTIONFORGE_DATABASE_URL=UNSET`, and the two T01A/T01B file sets before touching `app/api/app.py` wiring.
