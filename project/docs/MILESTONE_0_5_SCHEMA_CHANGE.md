# Milestone 0.5 — Schema Change Documentation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-07-29 | Initial schema (Milestone 0) |
| 2.0.0 | 2026-07-29 | Added tracking metadata, occlusion, confidence |

---

## Changes from 1.0.0 to 2.0.0

### New fields in `FrameMotion`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `confidence` | `float` | `1.0` | Tracking confidence, range 0.0–1.0 |
| `occluded` | `bool` | `False` | Object known to be behind another object |
| `needs_review` | `bool` | `False` | Tracking quality uncertain |
| `mask_path` | `str \| None` | `None` | Relative path to binary mask PNG |

### New fields in `SceneMotion`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tracking_backend` | `str` | `"unknown"` | Backend used: "sam2", "contour" |
| `model_version` | `str` | `""` | Model identifier, e.g. "sam2.1_hiera_l" |
| `anchor` | `Anchor` | `{x:0.5, y:0.5}` | Compositing anchor point (relative 0–1) |

### New model: `Anchor`

```python
class Anchor(BaseModel):
    x: float = 0.5  # 0.0 = left, 1.0 = right (relative to bbox)
    y: float = 0.5  # 0.0 = top, 1.0 = bottom (relative to bbox)
```

### Default version bump

`ProjectData.version` default changed from `"1.0.0"` to `"2.0.0"`.

---

## Semantic Definitions

| Concept | Definition |
|---------|-----------|
| Frame index | Zero-based. First frame = 0. |
| Scene end frame | INCLUSIVE. Scene [0, 89] = 90 frames. |
| Rotation unit | Degrees, from `cv2.minAreaRect`, normalized to [-90, 90]. |
| Coordinate unit | Pixels, origin at top-left of frame. |
| Confidence range | 0.0 (no confidence) to 1.0 (certain). |
| Anchor range | 0.0 to 1.0, relative to bounding box dimensions. |
| Visibility | `True` if object is considered present (mask area > threshold). |
| Occluded | `True` if object is known to be hidden behind another object. |
| Visibility vs Occluded | Visibility=False means "not detected". Occluded=True means "detected as hidden". Both can be True simultaneously (object partially visible behind obstacle). |

---

## Migration

Function `migrate_v1_to_v2(data: dict) -> dict` in `app/schemas/__init__.py`.

- Adds default values for all new fields
- Preserves existing data
- Idempotent (running on v2 data is a no-op)
- Does NOT modify the version field (caller should set it)

### Usage

```python
from app.schemas import migrate_v1_to_v2, ProjectData

with open("old_project.json") as f:
    raw = json.load(f)

migrated = migrate_v1_to_v2(raw)
project = ProjectData.model_validate(migrated)
```

---

## Backward Compatibility

- v1.0.0 JSON loads into v2.0.0 Pydantic model without errors (new fields have defaults)
- v2.0.0 JSON with extra fields is valid Pydantic input
- No fields were removed or renamed
- No field types changed
