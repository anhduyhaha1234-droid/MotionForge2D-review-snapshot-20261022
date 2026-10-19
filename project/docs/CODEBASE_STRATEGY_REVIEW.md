# MotionForge 2D - Codebase Strategy Review

**Date:** 2026-08-03  
**Decision:** Hybrid rebuild using a strangler migration  
**Scope:** Read-only architecture/code review; no production code changed

## 1. Executive decision

Do not rebuild from an empty repository, and do not continue polishing the current Screen A-E flow as the target product.

Keep the current Python/FastAPI + Next.js foundation and the media/AI services that already provide useful behavior. Build a new product spine alongside them: durable domain storage, resumable jobs, modular APIs, Project/Channel/Video management, Character Library, a new Project Shell and the object-first reskin flow. Retire old screens and JSON state only after each replacement vertical slice passes its migration and UX gates.

This gives the best balance of delivery speed, regression risk and product fit.

## 2. Evidence from the current repository

### Verification snapshot

- Python test suite: `144 passed, 6 skipped`.
- TypeScript type check: passed.
- ESLint: failed with `28 errors, 21 warnings`.
- Test warnings include deprecated frame access in scene detection and Pydantic enum serialization warnings.
- Existing media pipeline and tests are substantial enough that an empty-repo rewrite would discard validated behavior.

### Structural findings

| Area | Finding | Product impact |
|---|---|---|
| Channel storage | `channels.json` is shared mutable root data and is polluted by repeated test records | Unsafe production/test isolation; cannot support a reliable workspace |
| Project model | One `source_video` is the authority for a project | Cannot model a project containing many videos or per-video lifecycle |
| Persistence | Direct JSON writes and mixed filesystem state | Weak atomicity, migrations, relational queries and recovery |
| Jobs | Important job state lives in process memory/threads | Closing the app can lose or misreport work |
| Backend routes | Project route module is approximately 2,000 lines | High coupling and costly feature changes |
| Frontend state | Durable project truth is duplicated in Zustand/localStorage and restore hooks | Stale state and unclear authority |
| Current UI | Large Screen A-E components encode an old editor-centric flow | Poor fit for project/library/object-first UX |
| Presets | Existing presets hardwire a six-pose convention | Useful migration seed, but not a reusable/versioned Character Library |
| Media services | FFmpeg, scene detection, segmentation/tracking/compositing capabilities already exist | Valuable engines to preserve behind stable adapters |
| Dependencies | Some runtime imports/fallback paths are not cleanly declared/configured | Clean installation and hardware portability are not yet trustworthy |

## 3. Keep, refactor, rebuild or defer

| Component | Decision | Required treatment |
|---|---|---|
| Python/FastAPI runtime | Keep | Upgrade contracts, dependency declarations and module boundaries |
| Next.js/React/TypeScript | Keep | Build a new design system and application shell |
| FFmpeg probe/render/audio utilities | Keep + harden | Centralize capability detection, timebase and artifact contracts |
| Scene detection | Keep + refactor | Replace deprecated access, add fixtures and stable IDs |
| SAM2/contour/tracking adapters | Keep behind interface | Benchmark and add fallback/correction contracts |
| Motion/compositing math | Keep selectively | Extract from UI, unit-test and expose through new reskin workflow |
| CompositeCanvas interactions | Reuse selectively | Preserve proven transform/anchor math; rebuild presentation and state ownership |
| JSON project/channel persistence | Replace | SQLite metadata + versioned migrations + managed artifact store |
| In-memory jobs | Replace | Durable queue/state machine with checkpoint and reconciliation |
| Monolithic project routes | Rebuild modularly | Separate channels, projects, videos, characters, analysis, reskin, review and render APIs |
| Screen A-E navigation | Replace | New Home, Project Detail and six-step Project Shell |
| Channel Dashboard | Rebuild | Source/production channel roles, project links, counts and status |
| Preset Manager | Migrate data, replace domain/UI | Import usable assets into Character/Pack Version entities |
| Dubbing/localization UI/services | Defer | Isolate for Phase 2; Phase 1 preserves original audio |

## 4. Target migration topology

```text
Legacy JSON + Screen A-E
          |
          | read-only importer / compatibility adapters
          v
SQLite Domain + Artifact Store + Durable Jobs
          |
          +-> Channels -> Projects -> Video Items
          +-> Character Library -> Pack Versions -> Assets
          +-> Analysis -> Object Roles -> Cast Mapping
          +-> Demo -> Apply -> Review -> 4K Render
          |
          v
New Home + Project Detail + Guided Project Shell
```

There must be one backend authority for durable business state. Frontend stores may cache view state and optimistic UI only.

## 5. Safe execution order

1. Freeze fixtures for current projects, presets and representative videos; record baseline outputs.
2. Make lint/type/test/install gates trustworthy and remove test writes to production-root data.
3. Introduce SQLite migrations, managed artifact paths and durable job contracts.
4. Add Channel/Project/Video Item APIs and the new Home/Project Detail shell.
5. Add a one-way importer for legacy JSON projects/channels/presets; never mutate the source during import.
6. Deliver manual Character Library and immutable Pack Version pinning before the generator.
7. Deliver one end-to-end vertical slice: import one Video Item, analyze, select one Object Role, map one library character, approve Demo, apply and review with original audio.
8. Add the guided character generator as an optional Library input.
9. Add 4K render/resume/validation and packaging.
10. Retire each legacy screen only after its replacement meets functional, migration and usability gates.

## 6. Legacy retirement gates

A legacy area may be removed only when:

- all supported legacy data imports successfully or produces an actionable report;
- the replacement covers the approved user outcome;
- golden media output and timing regressions are within the agreed threshold;
- jobs recover after forced close;
- required lint, type, test and build gates pass;
- no production workflow depends on the old write path;
- rollback instructions and backups have been tested.

## 7. UI/UX rebuild direction

The new UI should be production-management first, not a collection of processing screens:

- Home answers: what projects exist, which video needs action, and which jobs are running.
- Project Detail shows source/production channels, Video Items, cast mapping and outputs.
- Project Shell uses `Import -> Objects -> Reskin Demo -> Apply -> Review -> Export` with persistent status and context.
- Character Library is global and searchable; selection happens in context without leaving the task.
- Demo is the mandatory confidence gate before expensive full-video work.
- Advanced controls appear only for warnings or corrections; the happy path stays guided.
- Every long operation has estimate, progress, cancel/retry/resume and a visible artifact/status trail.

## 8. Recommendation to Hermes

Hermes should not receive a broad instruction such as “refactor the app.” After PRD/MP approval, create epics from the Master Plan and give Hermes one vertical, gate-bound task at a time. The first coding sprint should stabilize persistence/tests and establish the new domain spine; it should not start with visual polishing or new AI models.

The recommended final answer to “sửa code hay build lại?” is therefore:

> Rebuild the product architecture and user experience inside the existing repository; preserve and adapt validated media engines. Migrate incrementally, then delete legacy paths only after replacement gates pass.
