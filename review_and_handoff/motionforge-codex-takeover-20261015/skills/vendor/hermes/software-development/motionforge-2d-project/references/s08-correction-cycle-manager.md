# S08 correction-cycle manager orchestration (C1 → C2 → …)

Use when Codex returns **CHANGES_REQUESTED** on a MotionForge2D S08 packet and the manager must
stand up the next correction cycle (R1-C1 → R1-C2, etc.). Extends
`s08-manager-handoff-experimental-writer.md`; this file captures the later-cycle mechanics.

## Trigger

Codex verdict on the last packet is CHANGES_REQUESTED with a named next task (e.g.
`S08-A02-T01-C2 — Re-analysis Role Binding, …`). A02-T01 overall stays **NOT APPROVED** even when
all local tests pass — never flip it yourself.

## Required manager sequence (verbatim from the C2 run)

1. **Preflight** — pwd/toplevel, branch `codex/s08-integration`, HEAD `a43b20da…`, `git status`
   count (~200), MAIN HEAD match, `MOTIONFORGE_DATABASE_URL` UNSET, one alembic head
   (`a0b1c2d3e4f5`, down_revision `f7a8b9c0d1e2`), QA ports free, no prior writer alive.
2. **Read the current code against EACH finding** — before writing TASK.md, grep/CURRENT audits so
   the packet's "current bug" lines cite real file:line (e.g. supersede uses `prior.role_id`;
   `update_segment` lacks a child-range re-check; lineage uniqueness is only
   `UNIQUE(workspace_id, logical_id, lineage_version)` + partial active index, no DB-enforced
   successor uniqueness; historical list returns all lineage versions incl. current; route bodies
   are `dict[str,Any]`+`_validate_body` so OpenAPI has no requestBody $ref).
3. **Bookkeeping first** — append `CODEX VERDICT APPEND` (CHANGES_REQUESTED + mandated next task)
   to the PRIOR C1/R2 REPORT.md (append-only, never rewrite). Then append the shared ERRATA/timestamp
   corrections.
4. **Create the C2 packet** `docs/pm/sessions/S08-A02-T01-C2-<name>/` — TASK.md (findings F1..F6
   normative, exact allowlist, forbidden list, 18-step validation order), START_PROMPT.md, LOG.md,
   REPORT.md. Allowlist typically: A02 block of models.py, structural_evidence.py, the SAME migration
   revision (no second head), schemas, route, app.py only for registration, 5 A02 test files + a NEW
   `tests/test_s08_a02_c2_integrity.py`, packet/evidence. FORBIDDEN: object_intelligence production
   code, frontend, A02-T02/S07/S09, other migrations, the 8 head-bump test files, MAIN.
5. **Model/provenance**: launch ONE writer via
   `hermes chat -q "$(cat …START_PROMPT.md)" --provider custom --model ocg/deepseek-v4-flash
   --max-turns 500 --pass-session-id --accept-hooks --yolo --source tool` with
   `MOTIONFORGE_DATABASE_URL` unset, background + notify_on_complete. Verify the real session id +
   model from `state.db` (sessions table, most recent `source='tool'` row). Reasoning max comes from
   `agent.reasoning_overrides['ocg/deepseek-v4-flash']='max'` + `agent.reasoning_effort`.
6. **Up to 2 read-only reviewer lanes** via delegate_task in parallel (do NOT use the `tasks` batch
   when you want to keep working — here batching is fine because the code writer is a separate
   background process, not a delegate). RO-1 audits lineage/re-analysis/SQLite constraints;
   RO-2 audits API strictness/OpenAPI/history/test gaps. Both READ-ONLY: no filesystem, no
   migration, no server, no MANAGER_STATE. Save their full summaries under the packet's
   `output/s08-a02-t01-c2/…` evidence so the manager can use them as a post-SUBMITTED verification
   checklist. Findings are relayed to the writer only when concrete and actionable.
7. **Heartbeat ≤5 min**; no-silence ≤10 min. On 502/disconnect verify the session is alive then
   resume the SAME session; never spawn a second writer. If writer BLOCKED: surface immediately.
8. **Manager independent verification after SUBMITTED** — do NOT trust REPORT pass counts. Re-run:
   import smoke (all 4 modules incl. schemas+routes), each A02 suite, combined focused, full S08
   regression + persistence bootstrap + durable_job, ruff, mypy, `git diff --check`, OpenAPI
   inspection (real requestBody $ref per POST/PATCH, no DELETE), a FRESH `quality-baseline.ps1`
   7/7 Run ID, alembic single-head/integrity/FK/downgrade-refusal, protected MAIN hashes,
   NO_LISTENERS. Spot-check each finding's code+test directly.
9. **C2-specific manager spot-checks** (the "don't fake green" list):
   - F1: `grep` tests for `role.source_generation = ` (assignment to an existing role) — must be
     GONE; the new role must be created via `ObjectIntelligenceRepository.create_role` or the
     production-equivalent API path in tests.
   - F4: raw-SQL corruption test proves two predecessors→same successor is REFUSED by the DB
     (UNIQUE/IntegrityError), not silently stored; duplicate active lineage refused; concurrent
     supersede single winner; rollback leaves no orphan/pending row; `integrity_check` ok,
     `foreign_key_check` empty; migration/ORM parity incl. the new lineage constraint.
   - F5: `?logical_id=…&historical` excludes the ACTIVE successor; pagination/total after the
     historical filter; current-generation query sees predecessor historical but NOT the current
     successor.
   - F6: OpenAPI requestBody has a concrete schema/$ref per POST/PATCH (no `dict[str,Any]` public
     body); `{"revision":"1"}` (string) → 422; NaN/Inf → 422 never 500; unknown field → 422.
10. **State + stop**: update `output/MANAGER_STATE.md` (session ids, model/provider/reasoning, real
    timestamps, test counts, blocker). Final = `MANAGER_VERIFIED_PENDING_CODEX_REVIEW`. STOP — no
    A02-T02/S07/S09. A02-T01 stays NOT APPROVED.

## Timestamp discipline (user-enforced via ERRATA — do not repeat the mistake)

- The user mandates Asia/Bangkok local +07:00 **and** UTC = local − 7h (same-day minus one hour),
  recorded AT WRITE TIME of each file. Never estimate, never write a future-ish timestamp, never
  reuse a "conversation started" date as a proxy.
- Background tool sessions have `end_reason=None` in state.db even after exit — do NOT trust
  state.db end times for wall-clock; use the writer's REPORT/LOG stated finish or the process
  completion notification.
- If a prior artifact has wrong timestamps, **append an ERRATA section** (never rewrite the old
  evidence). Example: `output/OVERNIGHT_HANDOFF.md` declared 06:30 but the file was actually
  written 06:10:04+07; C1 wall-clock was 02:46→~04:16 (not 04:33→06:04, which was the R2 wrapper).
- When verifying MAIN: `git -C C:/Users/Admin/MotionForge2D rev-parse HEAD` fails under MSYS;
  run `cd C:/Users/Admin/MotionForge2D && git rev-parse HEAD` instead.

## Model routing — verify before launch (multi-provider)

- Check `C:/Users/Admin/AppData/Local/hermes/config.yaml` → `providers:` lists both:
  `custom` (9Router `http://127.0.0.1:20128/v1`, model `ocg/deepseek-v4-flash`) and
  `muse` (9Router same base_url, model `meta/muse-spark-1.2-contributor`, `api_mode: codex_responses`).
- **Probe before dispatch** — `hermes chat --provider muse --model "meta/muse-spark-1.2-contributor" -q "Hello"` must return a session in ~7s; `meta/muse-spark-1.2.-contributor` (with extra ".-") 404s with `model_not_found` — the user-supplied `muse:meta/muse-spark-1.2.-contributor` has a typo dot, correct is without dot (CODEX_INDEPENDENT_REVIEW 2026-08-20T13:38 and config.yaml both confirm). If probe 404s, STOP as BLOCKED_MODEL_ROUTE, never fallback.
- The task packet's `Model:` line may still say `ocg/deepseek-v4-flash` from an earlier cycle — the **user instruction is the override** (record as "TASK.md nominal superseded by user instruction" in LOG.md). Launch flags are source of truth, not stale packet text.
- Reasoning max via `agent.reasoning_effort=max` + `agent.reasoning_overrides`; fallback must be `No fallback providers configured` (hermes fallback list). Verify from `state.db` session table (`sessions.model`), not just packet text.
- **Delegation inherits parent model** — `delegate_task` sub-agents inherit the manager chat's provider/model (e.g. `custom:meta-ai` pay-as-you-go), NOT the mandated `muse` via 9Router. In C2 both RO lanes (deleg_50719b87) failed `HTTP 403: hết credit (ví Pay-as-you-go, số dư: 2425)` because they inherited `meta-ai` instead of the local 9Router Muse model. Fix: do NOT use `delegate_task` for reviewers unless you pin the provider to the local 9Router (`--provider muse --model meta/muse-spark-1.2-contributor`) or skip delegation and let the manager do the read-only audit inline (record outcome in `output/s08-a02-t01-c2/reviewer-lanes-failed.md` pattern).

## Pitfalls seen

- `tee output/…/log` fails silently if the output directory does not exist yet — `mkdir -p`
  the evidence dir BEFORE launching the writer.
- `_validate_body(dict)` router pattern (R2/C2 era) hides request schemas from OpenAPI; the C2-F6
  fix exposes typed models while keeping NaN→422 via a router-local APIRoute/validation wrapper —
  an app-wide exception handler is NOT required and would widen scope.
- Migration may be RE-REWRITTEN within the same revision id (`a0b1c2d3e4f5`) because it is
  unreleased; verify no DB anywhere sits at that revision (check MAIN `.db` alembic_version and old
  `output/*/migration.db`) before rewriting, and only test on temp DBs.
