# S09-C4 Muse Full Completion — 26/08/2026 Manager Notes

Authority: `docs/pm/prompts/S09_C4_FULL_COMPLETION_MUSE_MANAGER_2026-08-26.md` (SHA `770719FF67E09F96…`) — unified live prompt superseding `S09_C4_CORRECTION_MANAGER`; `HERMES_AUTOPILOT_RULES.md` 180 lines SHA `987386c59f…`. Worktree `C:/Users/Admin/MotionForge2D-worktrees/s08-integration` @ `ee10e55a` (`codex/s08-integration`, dirty 117), MAIN `a43b20d` read-only. Freeze J1-v4 `ae92247b8bfd7bf2a43dcfcd83f71ac91603c86fa9f59b9c34d4c254df18d0d5` 13/13 MATCH, I03 `12de1345…`/`dab37e41…`, I05 `d289929d…` retained.

## J0-MUSE reconcile

Old T04 R4 exited 21:00:52 via `output/s09/.../t04-c4/dispatch3.log` 561B: `HTTP 401: [openrouter/stealth/ox-alpha]` then wrapper `EXIT-T04-C4-R4=0` ≠ task success. Recovery fact appended to `S09-C4-SESSION-REGISTRY.md`. Process audit: 0 owner workers, `ps aux` clean. DB guard `MOTIONFORGE_DATABASE_URL=UNSET`. No watchdog to kill.

## Muse probe (MUST use Hermes, not curl)

`hermes -z "ping" --provider muse -m ocg/muse-spark-1.2-contributor` → `pong — Hermes Agent online` + `RULES_LOADED terminal-engineering-discipline` in <1s, HTTP 200 via `codex_responses` at `http://127.0.0.1:20128/v1`. Raw `curl -H "Authorization: Bearer $key" http://127.0.0.1:20128/v1/responses` or `/v1/chat/completions` with `model: ocg/muse-spark-1.2-contributor` always `Missing API key` — config.yaml shows `sk-cff...c38f` but hermes redacts and injects via `credential_pool` (`custom:meta-muse-via-9router`, `custom:9router`, fingerprint `sha256:3848af8f…`). `/v1/models` lists 62 models but `ocg/muse-spark-1.2-contributor` only resolves through Hermes egress, not direct curl. Never use `openrouter/stealth/ox-alpha`, `custom/alpha`, or `alpha`.

## TTFB and dispatch

Large prompt (≈150k tokens, 4000-msg session context) needs `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900` — default 120s TTFB cutoff kills prefill before first byte (C4 measured 47s for 16-token probe, 22 min silence before first burst on resumed session). Dispatch exact owner:

```
HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume 20260824_052859_c6e197 \
  -z "$(cat output/s09/20260823_sprint_full/t04-c4/prompt-muse-final.txt)" \
  --provider muse -m ocg/muse-spark-1.2-contributor --yolo
```

**Never truncate:** `hermes --resume … --yolo 2>&1 | head -n 200` kills the worker — head closes after 200 lines, hermes gets SIGPIPE and dies mid-prefill. S09-C4 first Muse dispatch (26/08 21:36, PID 29096) showed exactly this: 5-line dispatch.log / 2.0K frozen for 50+ min, `msg count` 4001, ESTABLISHED socket but zero tool output until killed at 22:34 and relaunched correctly as `>> dispatch.log 2>&1`. Always redirect to a file, never pipe through head/tail.

Worktree cwd, reasoning max, fallback disabled. Owner suffix `052859_c6e197` IS the hermes session id (sqlite `sessions.id`); `hermes sessions list` truncates titles but sqlite `state.db` confirms. PID 29096 observed, `netstat` ESTABLISHED `127.0.0.1:57240 → 20128`, `wmic` WorkingSet ~3.7MB, log frozen initially = expected prefill, not stall.

## T04 fix (route A)

`wire_extraction_segment` in prompt = `app/persistence/structural_evidence.py:create_extraction_segment` (1334, requires `logical_id` + `segment_id`). `create_segment` (1185) rejects caller `logical_id` (C1-F2, `logical_id=_new_id()` uuid4). Extraction helper reuses all invariants but allows deterministic `logical_id == fixture layer_id` (e.g. `d1_sign_graphic`). Guard: `confidence_source in REQUIRED_JOB_CONFIDENCE_SOURCES` requires `source_job_id`; use `user`/`manual` + `None` to bypass, else return `BLOCKED_WITH_FINDINGS` with file:line. In `tests/test_s09_t04_demo_compare.py:_seed_applied_zorder_correction` replace `create_segment` call with `create_extraction_segment(logical_id=fixture_id, segment_id=deterministic, confidence_source="user", source_job_id=None, mask_artifact_id=..., z_order=...)` and assert `seg_rec.logical_id == fixture_id`.

## Liveness vs prefill (8-min audit)

Audit at 7.5 min: ESTABLISHED socket + low CPU (0 user time) + unchanged `dispatch.log` (2.0K) + frozen `messages` count = still prefill, not `BLOCKED_LIVENESS`. Distinguisher: prefill silence starts IMMEDIATELY after resume of large session; true stall starts AFTER visible progress then freeze. Wait full TTFB window before killing.

## DAG

`J0-MUSE → T04 final (052859) → J1-C4 → T05B final (093602) → J2-C4 → T06B production x2 (131423) → final gate` — single active slot, no cross-sprint freelancing, writers quiescent at gates.

## Evidence

- Freeze re-hash script: iterate manifest `files` dict, `hashlib.sha256(path.read_bytes()).hexdigest()` per file, assert MATCH.
- `MOTIONFORGE_DATABASE_URL` check: `env -u` for every pytest/basement, `hermes` inherits.
- Registry append via `cat >> S09-C4-SESSION-REGISTRY.md <<'EOF'` with timestamp +07.
