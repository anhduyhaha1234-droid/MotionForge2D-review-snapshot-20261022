"""Character preset library manager — multi-pose template characters.

Provides three built-in character reference packs (Boy Hacker, Thỏ Pink
Cute, Gấu Nâu), each with 6 canonical poses (sitting, standing,
three_quarter, walking, talking, back) as PNG assets, plus AI auto-pose
matching logic that selects the best pose from the aspect ratio of the
original character's bounding box:

- width > height * 1.1   → sitting (lying/wide pose)
- height > width * 1.3   → standing / walking (tall pose)
- centroid far from bbox center (looking away) → back
- otherwise              → talking (balanced pose)
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import cv2
import numpy as np

from app.schemas import CharacterPosePaths, CharacterReferencePack


class CharacterSpec(TypedDict):
    """Static description of a built-in character reference pack."""

    label: str
    poses: dict[str, str]


# Built-in character reference packs: id → {name, poses}
BUILTIN_CHARACTERS: dict[str, CharacterSpec] = {
    "dan_choi": {
        "label": "Dân Chơi (Streetwear)",
        "poses": {
            "sitting": "dan_choi_sitting.png",
            "standing": "dan_choi_standing.png",
            "three_quarter": "dan_choi_three_quarter.png",
            "walking": "dan_choi_walking.png",
            "talking": "dan_choi_talking.png",
            "back": "dan_choi_back.png",
        },
    },
    "boy_hacker": {
        "label": "Boy Hacker",
        "poses": {
            "sitting": "boy_hacker_sitting.png",
            "standing": "boy_hacker_standing.png",
            "three_quarter": "boy_hacker_three_quarter.png",
            "walking": "boy_hacker_walking.png",
            "talking": "boy_hacker_talking.png",
            "back": "boy_hacker_back.png",
        },
    },
    "tho_cute": {
        "label": "Thỏ Pink Cute",
        "poses": {
            "sitting": "tho_cute_sitting.png",
            "standing": "tho_cute_standing.png",
            "three_quarter": "tho_cute_three_quarter.png",
            "walking": "tho_cute_walking.png",
            "talking": "tho_cute_talking.png",
            "back": "tho_cute_back.png",
        },
    },
    "gau_nau": {
        "label": "Gấu Nâu",
        "poses": {
            "sitting": "gau_nau_sitting.png",
            "standing": "gau_nau_standing.png",
            "three_quarter": "gau_nau_three_quarter.png",
            "walking": "gau_nau_walking.png",
            "talking": "gau_nau_talking.png",
            "back": "gau_nau_back.png",
        },
    },
}

POSE_LABELS: dict[str, str] = {
    "sitting": "🪑 Ngồi",
    "standing": "🧍 Đứng",
    "three_quarter": "🚶 Góc 45°",
    "walking": "🚶 Đi bộ",
    "talking": "💬 Nói chuyện",
    "back": "🔙 Quay lưng",
}


def _draw_character(canvas: np.ndarray, color: tuple[int, int, int], pose: str) -> None:
    """Draw a simple character silhouette on a transparent canvas."""
    h, w = canvas.shape[:2]
    cx = w // 2
    body_bottom = int(h * 0.82)

    # Head (circle)
    head_r = int(h * 0.16)
    head_cy = int(h * 0.16)
    cv2.circle(canvas, (cx, head_cy), head_r, color, -1)

    if pose == "sitting":
        # Torso leaning back, legs forward (wide aspect)
        cv2.ellipse(
            canvas, (cx, int(h * 0.45)),
            (int(w * 0.28), int(h * 0.18)), 0, 0, 360, color, -1,
        )
        # Thighs forward
        cv2.rectangle(
            canvas, (cx - int(w * 0.22), int(h * 0.52)),
            (cx - int(w * 0.02), int(h * 0.62)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.02), int(h * 0.52)),
            (cx + int(w * 0.22), int(h * 0.62)), color, -1,
        )
        # Shins down
        cv2.rectangle(
            canvas, (cx - int(w * 0.2), int(h * 0.62)),
            (cx - int(w * 0.12), int(h * 0.78)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.12), int(h * 0.62)),
            (cx + int(w * 0.2), int(h * 0.78)), color, -1,
        )
    elif pose == "standing":
        # Tall upright body
        cv2.rectangle(
            canvas, (cx - int(w * 0.14), int(h * 0.28)),
            (cx + int(w * 0.14), body_bottom), color, -1,
        )
        # Arms
        cv2.rectangle(
            canvas, (cx - int(w * 0.2), int(h * 0.30)),
            (cx - int(w * 0.14), int(h * 0.55)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.14), int(h * 0.30)),
            (cx + int(w * 0.2), int(h * 0.55)), color, -1,
        )
        # Legs
        cv2.rectangle(
            canvas, (cx - int(w * 0.13), body_bottom - int(h * 0.2)),
            (cx - int(w * 0.03), body_bottom), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.03), body_bottom - int(h * 0.2)),
            (cx + int(w * 0.13), body_bottom), color, -1,
        )
    elif pose == "walking":
        # Slightly tilted body + legs apart
        cv2.rectangle(
            canvas, (cx - int(w * 0.13), int(h * 0.28)),
            (cx + int(w * 0.13), body_bottom - int(h * 0.05)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx - int(w * 0.2), int(h * 0.30)),
            (cx - int(w * 0.13), int(h * 0.55)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.13), int(h * 0.30)),
            (cx + int(w * 0.2), int(h * 0.55)), color, -1,
        )
        # Stride legs
        cv2.rectangle(
            canvas, (cx - int(w * 0.16), body_bottom - int(h * 0.2)),
            (cx - int(w * 0.02), body_bottom), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.05), body_bottom - int(h * 0.2)),
            (cx + int(w * 0.18), body_bottom), color, -1,
        )
    elif pose == "three_quarter":
        # Body slightly angled; head + shoulders offset to one side
        cv2.ellipse(
            canvas, (cx, int(h * 0.40)),
            (int(w * 0.18), int(h * 0.22)), 0, 0, 360, color, -1,
        )
        cv2.rectangle(
            canvas, (cx - int(w * 0.16), int(h * 0.30)),
            (cx + int(w * 0.10), body_bottom), color, -1,
        )
        cv2.rectangle(
            canvas, (cx - int(w * 0.2), int(h * 0.32)),
            (cx - int(w * 0.12), int(h * 0.52)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.06), int(h * 0.32)),
            (cx + int(w * 0.14), int(h * 0.52)), color, -1,
        )
        # Legs offset (walking angle hint)
        cv2.rectangle(
            canvas, (cx - int(w * 0.14), body_bottom - int(h * 0.2)),
            (cx - int(w * 0.04), body_bottom), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.04), body_bottom - int(h * 0.2)),
            (cx + int(w * 0.14), body_bottom), color, -1,
        )
    elif pose == "back":
        # Body + head seen from behind (no face features)
        cv2.rectangle(
            canvas, (cx - int(w * 0.14), int(h * 0.28)),
            (cx + int(w * 0.14), body_bottom), color, -1,
        )
        cv2.rectangle(
            canvas, (cx - int(w * 0.2), int(h * 0.30)),
            (cx - int(w * 0.14), int(h * 0.55)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.14), int(h * 0.30)),
            (cx + int(w * 0.2), int(h * 0.55)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx - int(w * 0.13), body_bottom - int(h * 0.2)),
            (cx + int(w * 0.13), body_bottom), color, -1,
        )
        # Hair hint (small cap on head)
        cv2.circle(
            canvas, (cx, int(h * 0.16)),
            int(h * 0.07), color, -1,
        )
    else:  # talking
        # Body + open mouth indication (small circle below head)
        cv2.rectangle(
            canvas, (cx - int(w * 0.14), int(h * 0.28)),
            (cx + int(w * 0.14), body_bottom), color, -1,
        )
        cv2.rectangle(
            canvas, (cx - int(w * 0.2), int(h * 0.30)),
            (cx - int(w * 0.14), int(h * 0.55)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx + int(w * 0.14), int(h * 0.30)),
            (cx + int(w * 0.2), int(h * 0.55)), color, -1,
        )
        cv2.rectangle(
            canvas, (cx - int(w * 0.13), body_bottom - int(h * 0.2)),
            (cx + int(w * 0.13), body_bottom), color, -1,
        )
        # Mouth bubble
        cv2.circle(
            canvas, (cx + int(w * 0.24), int(h * 0.12)),
            int(h * 0.05), color, -1,
        )


class CharacterPresetManager:
    """Manage built-in character preset assets (multi-pose PNGs)."""

    def __init__(self, assets_root: Path) -> None:
        self.assets_root = Path(assets_root)

    # ── Asset generation / bootstrap ──────────────────────────────────────

    def ensure_assets(self) -> None:
        """Generate all preset PNGs if they do not exist yet."""
        for key, spec in BUILTIN_CHARACTERS.items():
            for pose, filename in spec["poses"].items():
                target = self.assets_root / filename
                if target.is_file():
                    continue
                self._generate_asset(filename, pose, key)

    def _generate_asset(self, filename: str, pose: str, set_key: str) -> None:
        """Generate a transparent PNG for a pose with a set-specific color."""
        palette: dict[str, tuple[int, int, int]] = {
            "boy_hacker": (70, 130, 220),      # cool blue
            "tho_cute": (250, 180, 210),       # pink
            "gau_nau": (150, 110, 80),         # brown
        }
        color = palette.get(set_key, (200, 200, 200))

        # Tall poses → tall canvas; sitting → wide; angled/back → square
        if pose in ("standing", "walking", "three_quarter"):
            w, h = 512, 768
        elif pose == "sitting":
            w, h = 768, 512
        else:
            w, h = 640, 640

        canvas = np.zeros((h, w, 4), dtype=np.uint8)
        body = np.zeros((h, w, 3), dtype=np.uint8)
        _draw_character(body, color, pose)
        canvas[:, :, :3] = body
        canvas[:, :, 3] = np.where(np.any(body > 0, axis=2), 255, 0).astype(np.uint8)

        self.assets_root.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(self.assets_root / filename), canvas)

    # ── Listing ───────────────────────────────────────────────────────────

    def list_characters(self) -> list[dict[str, object]]:
        """Return all built-in character sets with their poses."""
        self.ensure_assets()
        result: list[dict[str, object]] = []
        for key, spec in BUILTIN_CHARACTERS.items():
            poses: list[dict[str, str]] = []
            for pose, filename in spec["poses"].items():
                poses.append(
                    {
                        "pose": pose,
                        "label": POSE_LABELS.get(pose, pose),
                        "filename": filename,
                        "url": f"/api/presets/characters/{key}/{pose}/image",
                    }
                )
            result.append(
                {
                    "id": key,
                    "label": spec["label"],
                    "poses": poses,
                }
            )
        return result

    def asset_path(self, set_key: str, pose: str) -> Path | None:
        """Return the absolute path of a preset asset, or None."""
        spec = BUILTIN_CHARACTERS.get(set_key)
        if spec is None:
            return None
        filename = spec["poses"].get(pose)
        if filename is None:
            return None
        self.ensure_assets()
        p = self.assets_root / filename
        return p if p.is_file() else None

    # ── Reference packs (CharacterReferencePack schema) ───────────────────

    def get_reference_pack(self, character_id: str) -> CharacterReferencePack | None:
        """Return the reference pack for a character id, or None."""
        spec = BUILTIN_CHARACTERS.get(character_id)
        if spec is None:
            return None
        return CharacterReferencePack(
            character_id=character_id,
            name=str(spec["label"]),
            poses=CharacterPosePaths(**{k: v for k, v in spec["poses"].items()}),
        )

    def list_reference_packs(self) -> list[CharacterReferencePack]:
        """Return all built-in reference packs (schema-validated)."""
        self.ensure_assets()
        return [
            pack
            for cid in BUILTIN_CHARACTERS
            if (pack := self.get_reference_pack(cid)) is not None
        ]

    # ── AI auto-pose matching ─────────────────────────────────────────────

    @staticmethod
    def auto_pose_for_bbox(
        width: float, height: float,
        centroid_x: float | None = None,
        centroid_y: float | None = None,
        bbox_x: float | None = None,
        bbox_y: float | None = None,
    ) -> str:
        """Pick a pose from the original character bbox aspect ratio + pose.

        - width  > height * 1.1  → sitting (lying/wide)
        - height > width * 1.3   → standing (tall)
        - centroid far from bbox center horizontally → back (looking away)
        - otherwise              → talking (balanced)
        """
        if width <= 0 or height <= 0:
            return "talking"
        if width > height * 1.1:
            return "sitting"
        if height > width * 1.3:
            return "standing"
        # Centroid shifted far to one side of the bbox → character looks away
        if (
            centroid_x is not None
            and bbox_x is not None
            and width > 0
        ):
            center_x = bbox_x + width / 2.0
            if abs(centroid_x - center_x) > width * 0.3:
                return "back"
        return "talking"


def get_preset_manager() -> CharacterPresetManager:
    """Get the singleton preset manager rooted at the project data dir."""
    from app.api import deps

    root = Path(deps._config.project_root)
    return CharacterPresetManager(root / "presets" / "characters")
