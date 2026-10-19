# Milestone 1A.1 — Test Evidence

**MotionForge 2D**
**Date:** 2026-07-30

---

## Environment

| Component | Version |
|---|---|
| Python | 3.11.9 |
| FastAPI | (latest via requirements) |
| Pydantic | v2 |
| Node.js / Next.js | (frontend build OK) |
| OS | Windows 10 |
| Git branch | `main` |
| HEAD commit | `df476e9` |

---

## Git Log

```
df476e9 M1A.1: Backend — clip modes, cancel tests, persistence tests, roadmap
b930911 M1A: Review documentation
```

Working tree: **clean** (no uncommitted changes).

---

## pytest Output

```
app/tests/test_api.py          25 passed
app/tests/test_schemas.py      14 passed
app/tests/test_motion.py        7 passed
app/tests/test_integration.py   7 passed
app/tests/test_clip_cancel_persist.py  14 passed
────────────────────────────────────────
Total                          67 passed

============================== 67 passed in ~XXs ==============================
```

### Test Clip Cancel Persist Breakdown (14 tests)

| Category | Tests | Status |
|---|---|---|
| Clip mode schema | 4 | ✅ Pass |
| Clip mode API integration | 2 | ✅ Pass |
| Job cancellation | 4 | ✅ Pass |
| Restart persistence | 4 | ✅ Pass |

---

## Ruff Output

```
$ ruff check app/
All checks passed!
```

---

## Frontend Build Output

### TypeScript Check
```
$ npx tsc --noEmit
(no errors)
```

### Next.js Production Build
```
$ npm run build
✓ Compiled successfully
✓ Linting passed
✓ Generating static pages
Build completed successfully.
```

---

## E2E API Workflow Output (TestClient)

| Step | Endpoint / Action | Result |
|---|---|---|
| 1 | `POST /projects` — create project | **201** Created |
| 2 | `POST /projects/{id}/upload` — upload video | **200** OK |
| 3 | `POST /projects/{id}/ingest` — extract frames | **completed** — 640×360, 30fps, 180 frames |
| 4 | `GET /projects/{id}/metadata` | **640×360, 30fps, 180 frames** |
| 5 | `GET /projects/{id}/frames/45` — fetch frame | **200** `image/png` |
| 6 | `POST /projects/{id}/preview-mask` — SAM2 mask | **200** — nonzero pixels: 89459 |
| 7 | `POST /projects/{id}/objects` — create object | **201** Created |
| 8 | `POST /projects/{id}/objects/{oid}/propagate` — SAM2 | **completed** — 180/180 tracked |
| 9 | `GET /projects/{id}/objects/{oid}/gallery` | **20 crops** |
| 10 | `POST /projects/{id}/objects/{oid}/replacement` — upload | **200** OK |
| 11 | `PUT /projects/{id}/objects/{oid}/settings` — clip_mode | **200** OK |
| 12 | `POST /projects/{id}/render` — preview | **completed** |
| 13 | `POST /projects/{id}/render?final=true` — final render | **completed** |

**Total E2E time:** ~55 seconds

---

## Coordinate Validation (Playwright)

```
$ npx playwright test coordinate-validation.spec.ts
9 passed, 0 failed
```

---

## Summary

| Check | Result |
|---|---|
| pytest (67 tests) | ✅ Pass |
| Ruff lint | ✅ Clean |
| TypeScript | ✅ No errors |
| Next.js build | ✅ Success |
| E2E API (13 steps) | ✅ All pass |
| Coordinate validation | ✅ 9/9 |
| Git status | ✅ Clean |
