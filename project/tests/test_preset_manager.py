"""Tests for the character preset library & AI auto-pose matching.

S00-T01 isolation contract:
- The `client` fixture comes from tests/conftest.py; it patches
  ``app.api.deps._config`` so route-level ``get_preset_manager()`` resolves to
  a temporary project root — never the production ``presets/characters`` dir.
- The production preset directory is only ever snapshotted READ-ONLY; no test
  constructs a manager rooted at it and no test calls ``ensure_assets()`` on it.
- All asset generation runs under pytest temporary paths.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.preset_manager import CharacterPresetManager


@pytest.fixture(scope="session")
def isolated_assets_root(tmp_path_factory: pytest.TempPathFactory):
    """Session-scoped isolated preset assets root (never production data)."""
    return tmp_path_factory.mktemp("preset_assets") / "presets" / "characters"


def _snapshot_preset_dir(prod_dir: Path) -> dict[str, str] | None:
    """Read-only snapshot of a preset dir: {filename: sha256}. Never writes."""
    if not prod_dir.is_dir():
        return None
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(prod_dir.glob("*.png"))
    }


class TestPresetManager:
    def test_auto_pose_for_bbox_wide(self) -> None:
        """width > height * 1.1 → sitting (lying/wide pose)."""
        from app.services.preset_manager import CharacterPresetManager

        assert CharacterPresetManager.auto_pose_for_bbox(200, 100) == "sitting"
        assert CharacterPresetManager.auto_pose_for_bbox(250, 200) == "sitting"

    def test_auto_pose_for_bbox_tall(self) -> None:
        """height > width * 1.3 → standing (tall pose)."""
        from app.services.preset_manager import CharacterPresetManager

        assert CharacterPresetManager.auto_pose_for_bbox(100, 200) == "standing"
        assert CharacterPresetManager.auto_pose_for_bbox(100, 140) == "standing"

    def test_auto_pose_for_bbox_balanced(self) -> None:
        """Neither → talking (balanced pose)."""
        from app.services.preset_manager import CharacterPresetManager

        assert CharacterPresetManager.auto_pose_for_bbox(100, 100) == "talking"
        assert CharacterPresetManager.auto_pose_for_bbox(100, 110) == "talking"

    def test_auto_pose_for_bbox_back(self) -> None:
        """Centroid far from bbox center → back (looking away)."""
        from app.services.preset_manager import CharacterPresetManager

        # Balanced aspect (not wide/tall), centroid shifted far right
        assert (
            CharacterPresetManager.auto_pose_for_bbox(
                100, 100, centroid_x=180, centroid_y=50, bbox_x=0, bbox_y=0
            )
            == "back"
        )
        # Centroid near center → talking
        assert (
            CharacterPresetManager.auto_pose_for_bbox(
                100, 100, centroid_x=55, centroid_y=50, bbox_x=0, bbox_y=0
            )
            == "talking"
        )

    def test_auto_pose_zero_size(self) -> None:
        """Zero/invalid sizes must not crash and return talking."""
        from app.services.preset_manager import CharacterPresetManager

        assert CharacterPresetManager.auto_pose_for_bbox(0, 0) == "talking"
        assert CharacterPresetManager.auto_pose_for_bbox(-5, 100) == "talking"

    def test_builtin_sets_cover_six_poses(self) -> None:
        """Each built-in set has all 6 canonical reference poses."""
        from app.services.preset_manager import BUILTIN_CHARACTERS

        assert "dan_choi" in BUILTIN_CHARACTERS
        assert len(BUILTIN_CHARACTERS) >= 4
        expected = {
            "sitting",
            "standing",
            "three_quarter",
            "walking",
            "talking",
            "back",
        }
        for key, spec in BUILTIN_CHARACTERS.items():
            assert set(spec["poses"].keys()) == expected, key

    def test_reference_pack_schema(self) -> None:
        """CharacterReferencePack validates id/name + 6 pose paths."""
        from app.schemas import CharacterPosePaths, CharacterReferencePack

        pack = CharacterReferencePack(
            character_id="boy_hacker",
            name="Boy Hacker",
            poses=CharacterPosePaths(),
        )
        assert pack.character_id == "boy_hacker"
        assert pack.name == "Boy Hacker"
        assert pack.poses.sitting == "sitting.png"
        assert pack.poses.three_quarter == "three_quarter.png"
        assert pack.poses.back == "back.png"
        assert len(pack.poses.model_dump()) == 6

    def test_reference_packs_endpoint(
        self, client: TestClient, isolated_assets_root
    ) -> None:
        """Manager builds reference packs with 6 poses each (isolated assets).

        S00-T01: uses an isolated assets root so ensure_assets() never writes
        into the production presets/characters directory.
        """
        pm = CharacterPresetManager(isolated_assets_root)
        packs = pm.list_reference_packs()
        assert len(packs) >= 4
        ids = {p.character_id for p in packs}
        assert "dan_choi" in ids
        for pack in packs:
            assert len(pack.poses.model_dump()) == 6

    def test_list_characters_endpoint(self, client: TestClient) -> None:
        """GET /api/presets/characters returns character sets × 6 poses."""
        r = client.get("/api/projects/presets/characters")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        chars = body["characters"]
        assert len(chars) >= 4
        labels = {c["label"] for c in chars}
        assert "Dân Chơi (Streetwear)" in labels
        for c in chars:
            assert len(c["poses"]) == 6

    def test_character_preset_image_endpoint(self, client: TestClient) -> None:
        """GET preset image returns 200 image/png for every set+pose."""
        r = client.get("/api/projects/presets/characters")
        assert r.status_code == 200
        for c in r.json()["characters"]:
            for pose in c["poses"]:
                img = client.get(
                    f"/api/projects/presets/characters/{c['id']}/{pose['pose']}/image"
                )
                assert img.status_code == 200, (c["id"], pose["pose"])
                assert img.headers["content-type"].startswith("image/png")

    def test_apply_character_preset_endpoint(self, client: TestClient) -> None:
        """POST apply copies the pose PNG and sets replacement_config."""
        import cv2
        import numpy as np

        from app.api import deps

        create = client.post("/api/projects", json={"name": "PresetApply"})
        pid = create.json()["project_id"]

        # Frame + object
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        obj = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "Nhân vật #1",
                "selection": {
                    "mode": "bounding_box",
                    "frame_index": 0,
                    "x": 60,
                    "y": 60,
                    "width": 80,
                    "height": 80,
                },
                "scene_id": 0,
            },
        )
        assert obj.status_code == 201
        oid = obj.json()["object_id"]

        r = client.post(f"/api/projects/{pid}/presets/characters/boy_hacker/sitting/apply")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "ok"
        assert body["object_id"] == oid
        assert body["pose"] == "sitting"
        assert body["asset_path"] == f"objects/{oid}/replacement.png"

        # The replacement PNG must exist on disk
        repl = proj_root / "projects" / pid / "objects" / oid / "replacement.png"
        assert repl.is_file()
        assert repl.stat().st_size > 0

        # Replacement image endpoint serves the preset
        img = client.get(f"/api/projects/{pid}/objects/{oid}/replacement-image")
        assert img.status_code == 200
        assert img.headers["content-type"].startswith("image/png")

    def test_auto_match_returns_pose(self, client: TestClient) -> None:
        """auto-match now reports the AI-chosen pose based on bbox aspect."""
        import cv2
        import numpy as np

        from app.api import deps

        create = client.post("/api/projects", json={"name": "PoseMatch"})
        pid = create.json()["project_id"]

        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        # Wide object (width 120 > height 60 * 1.1) → sitting
        obj1 = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "WideObj",
                "selection": {
                    "mode": "bounding_box",
                    "frame_index": 0,
                    "x": 40,
                    "y": 90,
                    "width": 120,
                    "height": 60,
                },
                "scene_id": 0,
            },
        )
        assert obj1.status_code == 201
        oid1 = obj1.json()["object_id"]

        # Tall object (width 40 < height 90 / 1.3) → standing in scene 1
        obj2 = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "TallObj",
                "selection": {
                    "mode": "bounding_box",
                    "frame_index": 0,
                    "x": 80,
                    "y": 40,
                    "width": 40,
                    "height": 90,
                },
                "scene_id": 1,
            },
        )
        assert obj2.status_code == 201

        r = client.post(f"/api/projects/{pid}/objects/{oid1}/auto-match")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "ok"
        assert body["pose"] == "sitting"
        assert obj2.json()["object_id"] in body["matched"]


class TestIsolation:
    def test_isolated_manager_writes_only_tmp_assets(
        self, isolated_assets_root
    ) -> None:
        """Asset generation runs on tmp root only; production dir is untouched.

        S00-T01: the production preset directory is snapshotted read-only and
        no manager rooted at it is ever constructed or invoked.
        """
        prod_dir = Path.cwd() / "presets" / "characters"
        prod_before = _snapshot_preset_dir(prod_dir)

        pm = CharacterPresetManager(isolated_assets_root)
        pm.ensure_assets()

        # Generated assets live under the tmp root only.
        assert isolated_assets_root.is_dir()
        pngs = list(isolated_assets_root.glob("*.png"))
        assert len(pngs) >= 4 * 6

        # Production preset dir file set AND content unchanged.
        assert _snapshot_preset_dir(prod_dir) == prod_before

    def test_endpoint_generates_assets_under_tmp_root(
        self, client: TestClient
    ) -> None:
        """GET /api/projects/presets/characters works and writes only tmp.

        Regression for S00-T01: the endpoint's get_preset_manager() must
        resolve to the isolated (tmp) project root; production preset dir and
        root channels.json must remain byte-identical.
        """
        from app.api import deps

        prod_dir = Path.cwd() / "presets" / "characters"
        prod_before = _snapshot_preset_dir(prod_dir)

        root_channels = Path.cwd() / "channels.json"
        channels_before = root_channels.read_bytes() if root_channels.exists() else None

        # Endpoint works and returns all built-in sets.
        r = client.get("/api/projects/presets/characters")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        chars = body["characters"]
        assert len(chars) >= 4
        for c in chars:
            assert len(c["poses"]) == 6

        # Assets were generated under the ISOLATED root (deps._config patched
        # to a tmp project root by conftest's _patch_project_root).
        isolated_dir = deps._config.project_root / "presets" / "characters"
        assert isolated_dir.is_dir()
        assert len(list(isolated_dir.glob("*.png"))) >= 4 * 6

        # Production preset dir and root channels.json unchanged.
        assert _snapshot_preset_dir(prod_dir) == prod_before
        channels_after = root_channels.read_bytes() if root_channels.exists() else None
        assert channels_after == channels_before
