# Milestone 1A.1 — Persistence Validation

**MotionForge 2D**
**Date:** 2026-07-30

---

## Overview

Persistence tests verify that project state survives across application restarts. All data is stored on disk as JSON files and validated after simulated restart.

---

## 1. Project Persists

**Test:** Create a project, shut down, restart, verify project exists.

| Step | Result |
|---|---|
| Create project via `POST /projects` | 201 — project ID returned |
| Verify project JSON exists on disk | ✅ File present |
| Restart application | — |
| Retrieve project via `GET /projects/{id}` | ✅ Project data intact |

**Stored location:** `projects/{id}/project.json`

---

## 2. Object Persists

**Test:** Create an object (with mask data), restart, verify object data.

| Step | Result |
|---|---|
| Create object via `POST /projects/{id}/objects` | 201 — object ID returned |
| Verify object data in `project.json` | ✅ Object entry present |
| Restart application | — |
| Retrieve object via `GET /projects/{id}/objects/{oid}` | ✅ Object data intact |

**Stored in:** `projects/{id}/project.json` → `objects[]` array.

---

## 3. Gallery Persists

**Test:** Generate gallery crops, restart, verify gallery manifest.

| Step | Result |
|---|---|
| Trigger propagation → gallery generation | 20 crops created |
| Verify `gallery_manifest.json` on disk | ✅ File present with 20 entries |
| Restart application | — |
| Retrieve gallery via `GET /projects/{id}/objects/{oid}/gallery` | ✅ 20 crops returned |

**Stored location:** `projects/{id}/objects/{oid}/gallery_manifest.json`

---

## 4. Replacement Config Persists (with `clip_mode`)

**Test:** Set replacement config with each clip mode, restart, verify config.

| Clip Mode | Set | Retrieved After Restart | Match |
|---|---|---|---|
| `asset_alpha` | ✅ 200 | ✅ `asset_alpha` | ✅ |
| `original_mask` | ✅ 200 | ✅ `original_mask` | ✅ |
| `intersection` | ✅ 200 | ✅ `intersection` | ✅ |

**Stored in:** `projects/{id}/objects/{oid}/replacement_config.json`

### Config Fields Verified

| Field | Persisted | Retrieved |
|---|---|---|
| `replacement_path` | ✅ | ✅ |
| `clip_mode` | ✅ | ✅ |
| `position_x` | ✅ | ✅ |
| `position_y` | ✅ | ✅ |
| `scale` | ✅ | ✅ |
| `rotation` | ✅ | ✅ |

---

## Persistence Mechanism

- **Format:** JSON files on local filesystem.
- **Write timing:** Config and project data are written synchronously on each API call.
- **Read timing:** On application startup, all project directories are scanned and loaded.
- **Concurrency:** File-level locking is not implemented (single-user desktop app).

---

## Summary

| Item | Persisted | Verified |
|---|---|---|
| Project metadata | ✅ | ✅ |
| Object data | ✅ | ✅ |
| Gallery manifest | ✅ | ✅ |
| Replacement config | ✅ | ✅ |
| `clip_mode` field | ✅ | ✅ |
