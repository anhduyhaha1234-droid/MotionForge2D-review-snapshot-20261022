# S01-T01 - Persistence domain contract and migration policy

**Status:** APPROVED  
**Epic:** E01 - Durable Domain, Persistence and Jobs  
**Sprint:** S01 - Persistence foundation  
**Gate:** G1 - Foundation green  
**Depends on:** S00 exit (APPROVED)

## User outcome

The project has one reviewable persistence contract before database implementation begins.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/MASTER_PLAN_V1.md`
3. `docs/PRODUCT_REQUIREMENTS_V2.md`
4. `app/schemas/__init__.py`
5. `app/services/project_service.py`
6. `app/workflow/channel_service.py`
7. `app/workflow/job_service.py`

## Allowed write scope

- `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
- `docs/pm/sessions/S01-T01-domain-contract/`

## Forbidden scope

- Runtime source, dependencies, database files and existing user data.
- PRD, Master Plan, roadmap and S00 evidence.
- SQLAlchemy engine/models, Alembic setup or import implementation.

## Acceptance criteria

- [x] AC1 Entity ownership, IDs, relations, lifecycle and constraints are explicit.
- [x] AC2 Artifact/database authority and transaction boundaries are explicit.
- [x] AC3 Migration, backup, rollback, idempotency and cutover policy are explicit.
- [x] AC4 Deferred S01/S02 decisions are identified without premature implementation.
- [x] AC5 Every S01 task retains the seven-gate baseline as a mandatory exit condition.

## Required validation

```powershell
rg -n "^## |S01-T0|S02|7/7|seven-gate|rollback|cutover|idempot" docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md
git diff --check -- docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md docs/pm/sessions/S01-T01-domain-contract
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
