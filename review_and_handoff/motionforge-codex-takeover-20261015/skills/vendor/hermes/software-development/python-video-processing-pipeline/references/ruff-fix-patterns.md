# Ruff Fix Patterns for FastAPI + Pydantic v2 Code

Common linting issues when building FastAPI APIs with Pydantic v2, and their fixes.

## N815 — MixedCase Variable in Class Scope

**Trigger:** Pydantic model fields matching external spec names (camelCase).

**Fix:** Use `Field` with `alias` + `model_config = {"populate_by_name": True}`:

```python
# BAD — triggers N815
class Config(BaseModel):
    assetPath: str = ""
    fitMode: str = "contain"

# GOOD — clean Python names, alias for JSON
class Config(BaseModel):
    asset_path: str = Field(default="", alias="assetPath")
    fit_mode: str = Field(default="contain", alias="fitMode")
    model_config = {"populate_by_name": True}
```

## B904 — Raise Without Chain in Except

**Trigger:** `raise HTTPException(...)` inside `except` without `from`.

**Fix:** Always chain: `raise HTTPException(404, ...) from err`

```python
# BAD
try:
    data = svc.load()
except FileNotFoundError:
    raise HTTPException(404, "Not found")

# GOOD
try:
    data = svc.load()
except FileNotFoundError as err:
    raise HTTPException(404, "Not found") from err
```

## UP035 — Import from collections.abc

**Trigger:** `from typing import Callable`.

**Fix:** `from collections.abc import Callable` (Python 3.11+).

## F541 — f-string Without Placeholders

**Trigger:** `f"scene_0"` (no `{}` inside).

**Fix:** Remove `f` prefix: `"scene_0"`.

## I001 — Import Block Sorting

**Fix:** Run `ruff check --fix` — auto-fixes import order. Don't sort manually.

## SIM105 — try/except/pass → contextlib.suppress

**Trigger:** Bare `try: ... except: pass`.

**Fix:**
```python
with contextlib.suppress(Exception):
    risky_call()
```

## SIM108 — if/else → Ternary

**Trigger:** Simple variable assignment in if/else.

**Fix:**
```python
# BAD
if project.video_metadata:
    metadata = project.video_metadata
else:
    metadata = probe_video(source)

# GOOD
metadata = project.video_metadata or probe_video(source)
```

## F841 — Unused Variable

**Trigger:** Assigned but never read.

**Fix:** Remove assignment or use `_` prefix: `obj_ext_svc.extract_crops(...)` without `manifest =`.

## F821 — Undefined Name

**Trigger:** Using a name that was imported at module level inside a function body, but the import was removed by ruff's auto-fix (e.g. `from pathlib import Path` was moved to TYPE_CHECKING block, or an inner function uses a name from a `import X` that was cleaned up).

**Fix:** Add the import inside the function body where it's used:

```python
# BAD — Path used but not imported in this scope
def upload_replacement(file: UploadFile):
    suffix = Path(file.filename).suffix  # F821: Path undefined

# GOOD — import locally
def upload_replacement(file: UploadFile):
    from pathlib import Path
    suffix = Path(file.filename).suffix
```

This commonly happens when refactoring a route handler that was previously in a file with module-level imports, and ruff's `--fix` removes the module-level import as "unused" (because the function is the only consumer and ruff's TC rules moved it).

## E501 — Line Too Long (>100)

**Fix:** Break at natural points. For method chains, break before `.`:
```python
resp = client.patch(
    f"/api/projects/{project_id}/objects/{object_id}"
    "/replacement-settings",
    json={...},
)
```

## Iterative Fix Strategy

1. Run `ruff check app/ tests/` to see all issues
2. Run `ruff check app/ tests/ --fix` to auto-fix import sorting and simple issues
3. Fix remaining issues manually (B904, N815, E501 need hand edits)
4. Re-run to confirm clean
