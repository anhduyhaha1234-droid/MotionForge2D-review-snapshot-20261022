# MF2D route-parity fixtures: never hand-key a manifest the route builds

Measured 2026-09-29 (DELTA-F4, MotionForge2D). A worker seam can be green in
tests and dead live when the FIXTURE — not the code — invented the key space.

## The failure shape

- Submit route builds `replacement_assets` keyed by OBJECT ROLE id
  (`assets[role_id] = ...`, app/api/routes/s10_full_apply.py).
- Group chunk members are occurrence LAYER ids (segment uuids) — a different
  id space by construction.
- Worker group path looked the layer id up directly -> every run died chunk 0:
  `replacement_assets missing entry for layer '0cbfa39b-…'`, 0 GPU work.
- The DELTA-F1 test fixture had hand-built `assets[lid] = ...` (layer-keyed),
  so 6/6 tests stayed green while the live run failed. A fixture that mirrors
  the BUG keeps the seam invisible.

## The fix pattern (two layers)

1. **Production**: one shared adapter, used by every consumer, extracted from
   the path that already had it right. Here:
   `_replacement_asset_key(mapping_entry, layer_id) = str(mapping_entry.get("role_id") or layer_id)`
   — `_stage_layer_asset` (legacy, correct) and the group cast (broken) now
   call the same function. Grep the whole app for the manifest key name and
   fix EVERY consumer site, not just the reported one.
2. **Fixture (route parity)**: build the fixture's manifest by CALLING the
   real route helper over the real persisted authority, and take the render
   authority from the real service output:
   - `manifest = {"managed_root": ...} + routes._resolve_canonical_render_pins(
       session, ..., authority=S09ApprovalRepository(session).full_apply_authority(ckpt, ws),
       managed_root=<the SAME root the DB artifact rows point into>)`
   - `authority = plan["render_authority"]` (service output)
   Then a future key-space drift cannot hide: the fixture follows the route
   automatically, and a bug in the worker goes red.

## Upgrade the fixture to the real cardinality

One member / one role hides whole classes of regression. Feasible upgrade
(measured): add a SECOND `object_role` + pack version (version=2, same
character is fine) + `character_asset` + `reskin_config`, and a SECOND
`occurrence_segment` (same scene; segment identity is UNIQUE per
role/scene/frame-range/source-generation, so give it a distinct range, e.g.
50–99). Result: a 2-member group chunk with DISTINCT roles per member — catches
both "no translation" and "first-member-wins" regressions. Assert per member:
`cast[i].character_id == mapping[i].role_id` AND the cast reference sha equals
that role's manifest pin.

## Required row set (never ship a fix without all three)

1. positive: render succeeds, exactly ONE engine call, per-member role/asset;
   also assert the manifest contract itself (`set(manifest.keys) == set(roles)`
   and `set(members) & set(manifest.keys) == ∅`).
2. negative ×N: delete the role entry of member 1 AND member 2 separately ->
   typed refusal + ZERO engine calls (fail-closed kept, per member).
3. parity/micro: the legacy path resolves the SAME manifest, plus the adapter
   fallback micro (`{"role_id": "r"}` -> "r"; `{}` -> layer; `{"role_id": ""}`
   -> layer).

## Proof procedure (red-on-base needs a scratch worktree)

- `git worktree add <WT>-base-red <base>` (from the task worktree is fine) +
  copy the FINAL test files in; run the same pytest command -> expect RED with
  the LIVE error text. Save the log; remove the worktree before the commit.
- Run the broad suite on BOTH trees; compare failure sets. Non-vacuity =
  base reds ⊇ new/changed tests; fix reds ⊆ base reds.
- A fix-only red that is a generated-artifact determinism test
  (`test_mf_end_28::test_28_2`, `app_tree_sha256`) is MECHANICAL: reproduce the
  attribution by hash — committed digest == fresh build on the pristine base
  tree; fresh build on the fix tree differs only by the writer's diff. Remedy
  (builder regen) belongs to the integration owner, never the task write-set.
