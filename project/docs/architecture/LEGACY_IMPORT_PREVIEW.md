# Legacy Import Preview Contract V1

**Status:** Implemented by S01-T04
**Epic:** E01 — Durable Domain, Persistence and Jobs
**Sprint:** S01 — Persistence foundation
**Owner module:** `app/persistence/legacy_preview.py`
**Companion:** `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md` (migration policy)

## 1. Purpose

Before the S01-T05 import/cutover, the user gets a deterministic, read-only
inventory of the legacy JSON data (channels + projects): entity counts,
legacy IDs, proposed deterministic new IDs, source relationships, referenced
files, validation issues and checksum evidence — **without changing any
source file and without creating a database**.

## 2. Non-goals (this task)

- No database/ORM/engine imports, no repository methods, no `legacy_import`
  row writes, no Alembic revisions, no backup/cutover/transactional import.
- No API/workflow/service/frontend behavior changes.
- Production repo-root data (`channels.json`, `projects/`, presets, output)
  is never assumed and never used as a test target.  The previewer is
  exercised only against explicit fixture roots.

## 3. Input contract

`LegacyPreviewer(legacy_root, channels_file=None, projects_root=None)`

- `legacy_root` is **required and explicit**.  The previewer never discovers
  or assumes repo-root data.
- Defaults resolve **inside** the supplied legacy root:
  `legacy_root/channels.json` and `legacy_root/projects`.
- `legacy_root` must exist and be a directory, otherwise
  `LegacyPreviewError` is raised (invalid input, not a data issue).
- Invalid explicit inputs raise `LegacyPreviewError`; data content problems
  are always reported as issues, never raised.

## 4. Containment (AC3)

- `legacy_root` (resolved) is the boundary.  Every referenced path is
  resolved against it and tested with `os.path.commonpath`; siblings are
  never inside.
- Unsafe references (absolute paths, `..` traversal, drive/UNC paths,
  symlink/junction escapes) are **blockers** and are **never followed** —
  the previewer only records `inside_root=False` and the issue.
- Source files (`channels.json`, `project.json`) and the **projects root
  itself** are containment-checked before any read/enumeration: an explicit
  or symlinked projects root outside the legacy root produces the blocker
  `PROJECTS_ROOT_UNSAFE` and is never enumerated (PM corrections 1–2).
- Existence checks happen only for references already proven inside the
  root.

## 5. Defensive parsing (AC2)

- One corrupt item becomes an issue; inventory continues.  Examples:
  - channels file not valid JSON / not a list → blocker, empty inventory.
  - channel entry not an object → warning, entry skipped.
  - channel missing/duplicate `channel_id` → blocker, entry skipped.
  - project dir without `project.json` → warning, dir skipped.
  - `project.json` invalid JSON or not an object → blocker, dir skipped.
  - invalid scene entries, duplicate scene/object ids, unknown channel
    references → warnings.
  - source-video or object reference outside the root → blocker.
  - referenced file missing inside the root → warning.

## 6. Deterministic identity mapping (AC1)

- Proposed IDs are `uuid5` over a stable per-kind namespace
  (`motionforge:legacy-import`): `proposed = uuid5(NS, f"{kind}:{legacy_id}")`
  with kinds `channel`, `project`, `object`.
- **Object identity is project-scoped** (PM correction 4): the UUID key is
  `f"object:{project_legacy_id}:{object_id}"`, so two projects that both
  contain `object_id="object_1"` receive different deterministic IDs.  The
  serialized DTO exposes `object_id_mapping` — a per-project mapping
  `{project_legacy_id: {object_id: proposed_id}}` — so the mapping is
  non-lossy and no entry is ever overwritten.
- Same legacy ID always maps to the same proposed ID; legacy IDs are never
  reused as primary keys (domain contract §2).

## 7. Unknown fields and audit data (AC4)

- Unknown top-level channel fields are collected under
  `unknown_fields["channel"]`.
- Unknown project object fields are collected under
  `unknown_fields["object"]` (per-project unknown fields are aggregated;
  object entries keep their own `references`).
- Names are deduplicated and sorted; nothing is silently discarded.

## 8. Output DTO

`LegacyPreview`:

| Field | Content |
|---|---|
| `legacy_root` | Resolved legacy root |
| `generated_at` | UTC ISO timestamp |
| `channels` | `{legacy_id, proposed_id, name, target_lang, default_preset_id, created_at}` |
| `projects` | `{legacy_id, proposed_id, name, task_status, channel_id, created_at, updated_at, version, scene_count, object_count, scenes, objects, source{...}}` |
| `issues` | `{severity, code, location, message}` sorted by severity/code/location/message |
| `source_checksums` / `source_checksums_after` | `{path, sha256, size_bytes, mtime_ns}` before/after |
| `unknown_fields` | `{kind: [names]}` |
| `referenced_files` | `{kind, raw, exists, inside_root}` sorted |
| `object_id_mapping` | `{project_legacy_id: {object_id: proposed_id}}` — non-lossy project-scoped object mapping |

- `blockers` / `warnings` split the issue list by severity.
- `legacy_ids` / `id_mapping` are convenience aggregations.
- `to_dict()` / `to_json()` make serialization caller-controlled and
  deterministic (`sort_keys=True`, `ensure_ascii=False`).

## 9. Read-only guarantee (AC5)

- The previewer performs only `read_text`/`stat`/`is_file` operations on
  sources and contained references.
- `source_checksums` (before) and `source_checksums_after` (after) must be
  identical for a healthy preview; tests assert this.
- No database is created: the module never imports engine/ORM modules and
  never opens a connection.
- Repeated previews produce byte-identical JSON (modulo `generated_at`).

## 10. Issue codes

| Code | Severity | Meaning |
|---|---|---|
| `CHANNELS_NOT_LIST` | blocker | channels.json unreadable/not a list |
| `CHANNEL_ITEM_NOT_OBJECT` | warning | channel entry skipped |
| `CHANNEL_MISSING_ID` | blocker | no valid `channel_id` |
| `CHANNEL_DUPLICATE_ID` | blocker | duplicate `channel_id` |
| `PROJECT_DIR_NO_JSON` | warning | dir has no project.json |
| `PROJECTS_ROOT_UNSAFE` | blocker | projects root resolves outside legacy root; never enumerated |
| `PROJECT_JSON_INVALID` | blocker | project.json corrupt |
| `PROJECT_SCHEMA` | blocker/warning | root not object / objects not list |
| `PROJECT_PATH_UNSAFE` | blocker | project path escapes root (reserved) |
| `PROJECT_SOURCE_ABSOLUTE` | blocker | source_video outside root |
| `PROJECT_SOURCE_MISSING` | warning | source_video empty/missing |
| `PROJECT_REFERENCE_UNSAFE` | blocker | object reference escapes root |
| `PROJECT_REFERENCE_MISSING` | warning | object reference missing |
| `PROJECT_CHANNEL_UNKNOWN` | warning | project→channel unresolved |
| `PROJECT_DUPLICATE_OBJECT_ID` | warning | duplicate object_id |
| `PROJECT_DUPLICATE_SCENE_ID` | warning | duplicate scene_id |
| `PROJECT_SCENE_RANGE` | warning | invalid scene entry/range |
