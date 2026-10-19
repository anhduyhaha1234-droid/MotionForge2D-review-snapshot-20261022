# S10-C1 — Iteration Limit + Network Retry + Route Coverage (2026-08-28)

## Iteration limit continuation (hit twice on T01C-C3)

- Initial `T01C-C3` prompt 38 lines: fixed route column + NVENC 256, got `11 passed ×2`. But worker hit `--max-turns 200` before server-side binding tighten + J2 probe tests. Reported `11 passed x2` green yet listed 6 remaining J2 bullets unstarted.
- Manager rule: `hit iteration limit` ≠ `TASK_SUBMITTED`. When worker exit says `hit iteration limit` + bullet list remaining, do NOT open J2. Resume **same owner** with a `-cont` packet (same `meta/max/TTFB900`) that lists only the remaining bullets. T01C needed **two continuations**: `t01c-c3-cont` (binding + 6 new tests) then `t01c-c3-cont2` (stitch 200→100 + tampered quarantine).
- Pattern: `output/s10/c1/<lane>/prompt.txt` → `output/s10/c1/<lane>-cont/prompt.txt` → `output/s10/c1/<lane>-cont2/prompt.txt` — same `owner_id`, each `prompt.txt` scopes only remaining work. Registry: `T01C-C3 CONTINUATION DISPATCHED (hit iteration limit)` with bullet delta.

## Network retry loop (3× on T01C-C3)

- `Network connection lost` at `14:00`, `14:26`, `15:15` — each classified `RUNNING_RETRY_WAIT` per Rules §7, wait 5 min then `hermes --resume <owner> -z "$(cat prompt)" -m meta --yolo`. Unbounded until success/session death, no fallback, no new session.
- After 2 fails, success at `14:46` produced `11 passed ×2` (route + NVENC fixes verified). Next `cont` hit network again then succeeded after 3rd retry. Distinguish from `Gateway 524`/`TTFB 120s > 120s`: both are `RUNNING_RETRY_WAIT`, not stall-kill.
- Registry must log `RETRY 2 DISPATCHED` / `RETRY 3 DISPATCHED` with elapsed check (`5 min satisfied` + `prior: 3× Network lost`).

## Renderer route coverage (T02-C1 2/38)

- `GROUP_FIXTURE_SPEC` role `layer_fg_table` used `controlled_redraw` but `_build_render_request_for_chunk` (L677) + `_execute_via_adapter` (L750) only wired `sprite_affine`/`pose_swap` → `Unsupported route` → 2/38 failed, `role_fg_table failed=True 0 artifacts`.
- Fix same owner `20260828_010435_b24638`: add `elif route == "controlled_redraw":` to **both** helpers, mapped to `SpriteAffineAdapter` with evidence preserved as `controlled_redraw` (6 hits verified, `38 passed ×2` after).
- Class lesson: every `RENDERER_ROUTES` value appearing in any `GROUP_FIXTURE_SPEC`/`spec` must have a wired executor branch. Pre-accept audit: `grep -n controlled_redraw app/services/s10_multi_role_apply.py` must show ≥6 hits (ROUTES + fixture + 2 branches + 2 evidence). Scope sweep before green gate.

## Stitch dedup + tampered quarantine (T01C-C3 cont2)

- `test_publication_exact_hash_size 200==100`: stitch double-counted verified core chunks → publication `frame_count 200` expected `100`. Fix: dedup verified core coverage sorted by shot/layer/core_range before stitch.
- `test_tampered verified 0==1`: `_quarantine_chunk` → re-render path did not set `verified=1` on second resume. Fix: quarantine → `Path.unlink` + re-render via real T02 executor → `verified=1` + new `artifact SHA/size`.
- Both surfaced only after `15 passed` initial; need `17 passed ×2` for J2. Never claim J2 on `11 passed` legacy count.
