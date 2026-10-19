# S10-C4 T03-C4 — correction authority semantics + continuation signatures (verified 29/08)

Continuation of S10-C4 serial DAG: `T01C-C6 → J1 (179×2) → T03-C4`.

## T03-C4 scope (from Codex C4 prompt §6)
- Resume exact owner `20260828_011920_b79bd6`, model `ocg/deepseek-v4-flash`, reasoning max, fallback OFF, TTFB 900.
- Allowed: `app/services/s10_recompute.py`, bounded recompute schema/API/wiring, `tests/test_s10_partial_recompute.py`, task docs append, `output/s10/c4/t03-c4/**`.
- Binary: no fallback authority synthesis (`ckpt-fallback`, zero-hash, `gen-1`, 100-frame/two-shot/generic mapping, guessed `_source.mp4` scans); `correction_id` must resolve durable applied same-workspace/project/video correction authority; build T02 RoleMapping from post-correction persisted facts; CẤM correction-ID hash perturb / byte-difference trick; renderer-returned route/adapter authoritative; affected attempt +1, unaffected byte-exact + zero calls; >260 nested-root test; mypy carry-forward T03 (754 unused-ignore + 890 dict / 918 set / 919 list type-arg) closed in this round.

## Signature: `Codex response remained incomplete after 3 continuation attempts` (1-line log)
- Dispatch R1 (21:20): `wc -l dispatch.log` = 1, content exactly that line. NOT the 7B `EXIT=1` write-hang, NOT the 90B `Network connection lost`.
- Decisive evidence: `ls -la --time-style=full-iso` on lane files — `app/services/s10_recompute.py` mtime moved 21:19→21:40 → worker LANDED real edits before dying.
- Action: `python -m py_compile app/services/s10_recompute.py` (PASS), wait full 5 min (Rules §7 transient), resume SAME owner/session/prompt/model → `dispatch-r2.log`.

## R2 report — 17/18 + honest RUNNING
- Worker diagnosed live: 13 legacy tests called `apply_correction` with random correction_id but never seeded `s09_correction` → new fail-closed `S10RecomputeNotFoundError` correctly killed them; seed job idempotency_key mismatch (`s10_t03_seed_...` vs production `s10_full_apply_job:{run_id}`) broke manifest authority resolution.
- Production hardening inside scope: contact facts validate (kind/source/target, frame int-cast); z_order None-check replaces `int(... or idx)` fallback.
- Path-budget probe: `\\?\` prefix OK for VideoWriter/VideoCapture/imread/imwrite/open/atomic_write/decode on >260 paths (LongPathsEnabled=0); ManagedRoot.resolve() keeps prefix.
- mypy: `--follow-imports=skip` → Success (2 call-overload ignores legit); remaining unused-ignores belong to T04B/T01C files outside allowlist.
- 5 new C4 tests: fail-closed random/pending/cancelled/cross-project/cross-video IDs; manifest-missing → zero attempt bump; mask region → RoleMapping.affected_region; z/contact/route fact → RoleMapping + renderer evidence; nested >260 atomic zero orphan.
- Full run: 17 passed, 1 failed.

## The reseed trap (banned byte-trick ⇒ update the test, not the code)
- Failure: `test_c3_affected_adapter_invocation_and_evidence`. (a) `workspace_root` now `\\?\`-normalized → assertion must use `resolve()`; (b) affected bytes do NOT change because persisted mask region `[0.10,0.10,0.40,0.40]` EQUALS the base mapping region → real SpriteAffineAdapter renders identical media. C3 got changed bytes via hash-perturb, which C4 outlawed.
- Worker's stated fix direction: seed C4 authority with a region DIFFERENT from base mapping (e.g. `[0.10,0.10,0.60,0.60]`) so recompute genuinely changes a visual fact; or assert "fact changed + identity matches" instead of merely unequal SHA.
- General rule captured in SKILL.md: when a correction round forbids a deterministic-perturb trick, reseed the asserting tests with genuinely different persisted authority and assert corrected fact + request identity — never silently reintroduce the trick to make bytes differ.

## R3 continuation (no 5-min wait)
- R2 exit was an honest worker-requested continuation (`STATUS: C4 chưa hoàn tất... cần tiếp tục lượt mới`), NOT a transient → resume immediately, same prompt (`dispatch-r3.log`).

## J1 (C4) gate — Manager independent re-verify pattern used
- Targeted API+workflow ×2 fresh basetemps: 32+32 passed.
- Full `tests/test_s10*.py`: 179 passed / EXIT 0 (208.99s, DB UNSET) — matches worker's own `full-s10-regression2.log` 179.
- Ruff F* touched: All checks passed; mypy 9-file: T01C 0, 12 carry-forward (8 structural_compare unused-ignore T04A + 1 recompute unused-ignore/3 type-arg T03) — routed to owners, not hidden.
- J1-v4 13/13 + EOL (packaged `scripts/j1v4_rehash.py`); alembic single head `a10b11c12d3e`; git diff --check 0; porcelain 45 = allowlist + pre-existing.
- Reconcile fairness rule: manager NEVER relabels a red binary gate as "fair" — the C3 registry's `"ALL 9 GATES GREEN"` + mypy-15-as-"fair" claim is the anti-pattern being superseded in C4 (`BLOCKED_WITH_FINDINGS` until every binary gate is genuinely green).