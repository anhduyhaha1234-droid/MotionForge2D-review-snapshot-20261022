# S10-C1 — Real FullApply Correction (F1–F7) — 2026-08-28

Verified Codex independent review `S10_C0_PM_REVIEW_2026-08-28.md`: `122 passed, 2 failed, 79 warnings`.
Both failures in `tests/test_s10_partial_recompute.py`. Direct DB truth: 1 completed run, 12 verified chunks,
**zero `s10_full_apply_publication` rows**, 12 artifact rows with **null `size_bytes`/`sha256`**, 8192-byte `.bin`
files of repeated hex — not rendered video. Ruff 162 errors incl. unused-value, sprint report falsely
claimed line-length only.

## F1 P0 — Fabricated bytes instead of rendered video

- Owner: `S10-T01C 20260828_003035_859fe5` + `S10-T02 20260828_010435_b24638`
- File: `app/workflow/s10_full_apply_jobs.py:171-186` hashes string → repeats digest → `chunk_*.bin:213-219`
  marks completed without stitching or publication.
- Fix: typed executor contract in `s10_multi_role_apply.py` that builds frozen `RenderRequest`
  from pinned source artifact + exact core+overlap range + role/layer mapping + pack/replacement
  asset + anchor/motion/contact/z-order + pinned route; invokes **real licensed adapter**
  via `renderer_router`/`composite`; returns decodable media + route/attempt/frame/hash evidence.
  Worker deletes fabricated `.bin` path, writes **managed atomic decodable chunk media** with
  real `SHA-256/size` + decoded-frame/route/dependency evidence, then deterministically stitches
  **one completed `s10_full_apply_publication`** bound to checkpoint. `completed` only after
  publication `completed`.

## F2 P0 — Structural gate caller-forgeable

- Owner: `S10-T04A 20260828_014304_25d94a` → `S10-T04B`
- File: `app/api/routes/s10_full_apply.py:465-547` accepts source/rendered manifests,
  every metric, policy version, annotations from HTTP body.
  UI `frontend/src/app/(app)/apply/page.tsx:151-207` hard-codes good metrics.
- Fix: server derives **all metrics** from pinned `StructuralLockManifest`/checkpoint,
  completed publication, decoded rendered media, stored per-role/route/contact/z-order/visibility
  evidence; records content hashes linking result to exact input/output/policy. Client metrics
  ignored. Negative API tests: forged metrics, tampered output, removed publication, wrong
  policy → all `BLOCKED`. Only server-derived green → `REVIEW_REQUIRED`.

## F3 P1 — Restart never proves mid-run

- Owner: `S10-T04C 20260828_023122_76b87e`
- File: `frontend/e2e/s10-full-apply.spec.ts:564-601` accepts terminal completed as checkpoint;
  `:631-640` accepts 409 from resume. All 12 chunks verified before stop.
- Fix: prove **strict** before stop: `0 < next_chunk_index < total`, `0 < verified < total`,
  run **nonterminal**; record initial PID/port; stop exact owner; prove exit/port release;
  start **different PID** owning port; resume must `2xx {resumed:true}`; pre-stop verified
  artifact IDs/SHA/attempts exact; unfinished chunks complete after. **Completed-run fallback
  and 409 fallback forbidden.**

## F4 P1 — Recompute not a vertical slice

- Owner: `S10-T03 20260828_011920_b79bd6` → `S10-T04C`
- No recompute endpoint; E2E tolerates 404/422/409, unchanged run as proof.
  Nested artifact parent not created before `ManagedRoot.atomic_write_bytes` (`s10_recompute.py:622-628`).
- Fix: strict project-scoped idempotent `POST /recompute` API: validates run/checkpoint revision
  + correction provenance, computes deterministic affected closure, enqueues durable work,
  uses same real T02 executor. `fix: ensure parent dirs via Path.mkdir(parents=True)`.
  Affected `attempt +1` + new verified media/provenance; unaffected IDs/SHA/size/frame exact,
  zero new attempt. Replay dedupes. Restart resumes partial. **Missing route / non-2xx = fail.**

## F5 P1 — Resume hash fail-open

- Owner: `S10-T01C`
- File: `s10_full_apply_jobs.py:253-285` computes `file_sha` but discards → true for any
  existing ready non-partial artifact.
- Fix: compare **actual file SHA-256, size, decoded frame count/timebase, chunk identity,
  pinned dependency hashes** before reuse; mismatch → quarantine/recompute, never advance
  checkpoint.

## F6 P1 — UI manufactures plan inputs

- Owner: `S10-T04B 20260828_020206_b1f8af` + `S10-T01C` server validation
- File: `frontend/src/features/apply/ApplyCard.tsx:62-99` fabricates `source_generation`,
  frame 100, 2 shots, 2 mappings when authoritative absent.
- Fix: backend resolves exact current checkpoint snapshot for selected project/video;
  missing `StructuralLockManifest`/pack/policy/routes/corrections → **Apply disabled**
  with explicit Vietnamese reason. No synthetic fallback enters submit. Server binding
  prevents override; missing/stale/cross-project/incomplete pin → fail before enqueue.

## Correction DAG (serialized — one writer)

```
PREP → T02-C1 → J1 → T01C-C3 → J2 → T03-C1 → J3 → T04A-C1 → J4 → T04B-C1 → J5 → T04C-C1 → EXIT
```

- No parallel production writer (T02/T01C/T03 share workflow; T03/T04A share API;
  T04B depends server contract; T04C depends all).
- Frozen T01A/T01B not resumed unless blocker proven + Codex authorizes.
- Each correction: `HERMES_CODEX_TTFB_TIMEOUT_SECONDS=900 hermes --resume <owner_id> -z "$(cat output/s10/c1/<lane>/prompt.txt)" -m meta --yolo`

## Verification Traps Captured This Round

- **Job handler registration**: `app/workflow/job_service.py` must `register_s10_full_apply_handler(self._worker)`
  after `register_attach_original_audio_handler` — bounded `+3 lines`. Missing → worker never dispatches.
- **SQLite busy**: `submit` did `create_job` inside uncommitted `session` tx → whole-DB lock.
  Fix: `session.commit()` run/chunks **before** `create_job` (separate connection), narrow inner
  `except Exception: pass` to duplicate-idempotency only (`IntegrityError`/`S10ApplyConflictError`).
- **Alembic CWD**: `script_location = migrations` relative — `alembic heads` from MAIN (4 revs → `d5e6f7a8b9c0`)
  hides worktree chain (17 revs → `a10b11c12d3e`). Always `cd <worktree> && alembic heads/history`.
- **Pytest addopts**: `pyproject.toml addopts` breaks `pytest --cache-clear`. Use
  `pytest -v -p no:cacheprovider --override-ini="addopts=" --basetemp=<fresh>`.
- **Harness shape**: response is `{projects:[]}` not `{items:[]}`; `{videos:[]}` similarly — parse both.
- **Renderer route coverage (T02-C1 28/08 13:38)**: `GROUP_FIXTURE_SPEC` used `controlled_redraw` for `layer_fg_table` but executor only wired `sprite_affine`/`pose_swap` → `Unsupported route` → 2/38 failed (`role_fg_table` 0 artifacts). Fix same owner `20260828_010435_b24638`: add `elif route == "controlled_redraw":` to both `_build_render_request_for_chunk` and `_execute_via_adapter` mapped to `SpriteAffineAdapter` with evidence preserved as `controlled_redraw` (6 hits verified, `38 passed ×2` after 25.8s). Lesson: every `RENDERER_ROUTES` value appearing in any fixture must have a wired executor branch — audit `grep -n controlled_redraw` before accepting.

## Exit Gates for C1

1. J1-v4 13/13 + EOL unchanged (manifest v4 `ee10e55a`, `.gitattributes` `text eol=lf/crlf`)
2. All `tests/test_s10*.py` **pass ×2** on fresh roots (prior 2 T03 failures now pass, no nested parent error)
3. Retained S09 renderer/T06 suites pass; real adapter invocation count >0; source-only re-encode negative fails
4. Ruff `F*` functional zero (E501 formatting P2 documented separately); mypy relevant green
5. One Alembic head + round-trip; OpenAPI additive + unique ops + real recompute route present
6. Frontend TSC + scoped ESLint + prod build green; active build manifest reused by both runs
7. DB truth per run: partial `0<next<total` before kill, exact reuse after resume, affected-only `+1`,
   non-null `SHA/size`, decodable, exactly one completed publication per lineage, no `.partial`
8. `git diff --check` 0; attribution complete; 3014 preserved; task ports free after runs
