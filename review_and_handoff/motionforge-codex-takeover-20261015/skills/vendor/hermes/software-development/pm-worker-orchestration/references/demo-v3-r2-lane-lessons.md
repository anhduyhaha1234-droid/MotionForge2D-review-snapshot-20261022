# DV3-R2 lane lessons (2026-09-08/09) — manager 20260908_165201_c0780f

Session-specific detail for `pm-worker-orchestration`. T00→T04 demo lane,
model switch mid-lane + repeated worker deaths. All items verified live.

## 1. Mid-lane model switch (user order, latest-wins)
- User switched lane route `ocgfree/muse-spark-1.3-contributor-free` →
  exact `cmc/meta/muse-spark-1.3-contributor` (provider custom, max, OFF).
- Protocol that worked: probe `hermes -z "ping" -m <exact-id> --yolo`
  (pong EXIT 0) → log `commands.jsonl` SWITCH event → write prompt file
  with new `-m` → resume/dispatch with new `-m` → record override at top
  of REGISTRY.md. Never apply retroactively to finished tasks; never touch
  S12/Lunar/global routing.

## 2. write_set_guard: allow-change your own targets
- T04 manifest listed 8 frozen entries INCLUDING the 3 pilot files the task
  allowlist permits as bounded patches. Plain `verify` then reported
  `protected_file_changed` x3 — a self-inflicted false FAILED.
- Rule: when the prewrite manifest contains intentional write targets,
  verify with `--allow-change <each-target-path>` (plus shrink limit), or
  keep two manifests (frozen-only vs task-owned). Untracked (`??`) files
  that change hash are reported as changed too — check `git status`
  attribution before crying drift.

## 3. `hermes --resume` often mints a NEW session
- Observed 4+ times: `--resume <id>` created `20260909_*.new` instead of
  continuing the owner, same model, prompt embedded and live.
- Handling: never assume resume worked — query state.db
  (`SELECT id,model,ended_at,message_count FROM sessions ORDER BY rowid
  DESC LIMIT 1` + first user-msg substring) to confirm which session is
  live, then record lineage `R1 → R2 → R3` in REGISTRY.md. Single active
  writer holds because priors are `agent_close` terminal; say so explicitly.

## 4. Stale watchdogs: close the ledger
- Bounded poll watchers (e.g. `grep STATUS REPORT.md`, 60s x 180) fire on
  OLD markers after the task already advanced (W3/W4/W8-W12 here).
- Always append `commands.jsonl` END rows with `STALE/superseded` notes so
  the next turn does not mistake a late fire for a new result.

## 5. Reading-phase death → lean split prompt
- T03 died 7x at 40-70 msgs during required-reading (5KB prompt + 6 docs),
  zero code artifacts each time. Same full prompt retried = same death.
- Pivot that worked: split into stepA (module only, ~2.2KB prompt, facts
  inlined, no heavy reading list) + stepB (tests/stills/REPORT). StepA
  landed 550 lines, ruff+compile clean, 29-test regression green first try.

## 6. vision_analyze blind on local files → pixel truth
- `vision_analyze` on local PNGs repeatedly returned "[image omitted]".
- Fallback that held gates: decode panels with PIL/numpy, split composite
  sheets into cells, measure channel deltas (note BGR→RGB flips BEFORE
  color overlays — red tint in BGR reads as BLUE in RGB), mask bbox +
  overlap % + inside/outside means. Numbers named the owner every time.

## 7. T04 correction triage shape (reuse)
- Real fails: exact-dict equality on a verdict dict with extra keys →
  assert the key; `pytest.raises(match=)` vs actual raised code → read the
  raise first; 422-pack-gate masked by frame-range guard firing first →
  reorder request or split assertions; 503 asset-under-isolated-roots →
  point at pinned read-only asset, never MAIN.
