"""Tests for delete project and auto-segment endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _patch_project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override project root so all tests use a temp directory."""
    test_root = tmp_path / "motionforge_test"
    test_root.mkdir()

    from app.api import deps
    from app.config import AppConfig

    test_config = AppConfig(
        project_root=test_root,
        models_dir=test_root / "models",
        output_dir=test_root / "output",
    )
    monkeypatch.setattr(deps, "_config", test_config)
    monkeypatch.setattr(
        deps,
        "_project_wf",
        __import__(
            "app.workflow.project_workflow",
            fromlist=["ProjectWorkflowService"],
        ).ProjectWorkflowService(test_config),
    )
    monkeypatch.setattr(
        deps,
        "_job_service",
        __import__(
            "app.workflow.job_service", fromlist=["JobService"],
        ).JobService(),
    )
    monkeypatch.setattr(
        deps,
        "_replacement_service",
        __import__(
            "app.workflow.replacement_service",
            fromlist=["ReplacementService"],
        ).ReplacementService(deps._project_wf),
    )
    monkeypatch.setattr(
        deps,
        "_seg_service",
        __import__(
            "app.workflow.segmentation_service",
            fromlist=["SegmentationService"],
        ).SegmentationService(test_config),
    )

    return test_root


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    from app.api.app import app

    return TestClient(app, raise_server_exceptions=False)


class TestDeleteProject:
    def test_delete_nonexistent(self, client: TestClient) -> None:
        """DELETE nonexistent project returns 404."""
        response = client.delete("/api/projects/nonexistent123")
        assert response.status_code == 404

    def test_delete_existing(self, client: TestClient) -> None:
        """DELETE existing project removes it."""
        # Create
        create_resp = client.post("/api/projects", json={"name": "ToDelete"})
        assert create_resp.status_code == 201
        pid = create_resp.json()["project_id"]

        # Delete
        del_resp = client.delete(f"/api/projects/{pid}")
        assert del_resp.status_code == 200
        assert del_resp.json()["ok"] is True

        # Verify gone
        get_resp = client.get(f"/api/projects/{pid}")
        assert get_resp.status_code == 404


class TestAutoSegment:
    def test_auto_segment_no_frames(self, client: TestClient) -> None:
        """Auto-segment with no frames returns 404."""
        create_resp = client.post("/api/projects", json={"name": "EmptyProj"})
        assert create_resp.status_code == 201
        pid = create_resp.json()["project_id"]

        response = client.post(f"/api/projects/{pid}/auto-segment-objects")
        assert response.status_code == 404

    def test_auto_segment_nonexistent_project(self, client: TestClient) -> None:
        """Auto-segment on nonexistent project returns 404."""
        response = client.post("/api/projects/nope/auto-segment-objects")
        assert response.status_code == 404

    def test_auto_segment_distinct_names(self, client: TestClient) -> None:
        """Auto-segment returns distinct names with size for each object."""
        import cv2
        import numpy as np

        # Create project
        create_resp = client.post("/api/projects", json={"name": "NamesProj"})
        pid = create_resp.json()["project_id"]

        # Create a synthetic frame with two distinct objects (white bg, dark objects)
        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((300, 400, 3), 255, dtype=np.uint8)  # white background
        frame[50:200, 50:150] = (0, 0, 0)   # large left object
        frame[80:130, 250:350] = (0, 0, 0)  # medium right object
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        resp = client.post(
            f"/api/projects/{pid}/auto-segment-objects",
            params={"scene_id": 0, "min_area": 100},
        )
        assert resp.status_code == 200
        objs = resp.json()["objects"]
        assert len(objs) >= 2

        # Every object has a distinct name containing size
        names = [o["name"] for o in objs]
        assert len(set(names)) == len(names), f"Duplicate names: {names}"
        for o in objs:
            assert "×" in o["name"] and "px" in o["name"], o["name"]
            # Name should reference the size
            assert str(o["bbox"]["width"]) in o["name"]
            assert str(o["bbox"]["height"]) in o["name"]


class TestObjectCrop:
    def test_crop_nonexistent_object(self, client: TestClient) -> None:
        """GET crop for nonexistent object returns 404."""
        create_resp = client.post("/api/projects", json={"name": "CropProj"})
        pid = create_resp.json()["project_id"]
        resp = client.get(f"/api/projects/{pid}/objects/nope/crop")
        assert resp.status_code == 404

    def test_crop_generates_after_create(self, client: TestClient) -> None:
        """GET crop returns image/png after creating an object with a frame.

        Uses a synthetic frame created in the test project's frames dir,
        then creates an object and verifies the crop endpoint serves PNG.
        """
        import cv2
        import numpy as np

        # Create project
        create_resp = client.post("/api/projects", json={"name": "CropProj2"})
        pid = create_resp.json()["project_id"]

        # Create a synthetic frame at projects/{pid}/frames/scene_0/frame_000000.png
        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 255)  # red square
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        # Create object with point selection on the red square
        r = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "CropObj",
                "selection": {
                    "mode": "point",
                    "frame_index": 0,
                    "x": 100,
                    "y": 100,
                },
                "scene_id": 0,
            },
        )
        assert r.status_code == 201
        oid = r.json()["object_id"]

        # GET crop (no trailing slash)
        resp = client.get(f"/api/projects/{pid}/objects/{oid}/crop")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/png")

        # GET crop (trailing slash) — no 405
        resp2 = client.get(f"/api/projects/{pid}/objects/{oid}/crop/")
        assert resp2.status_code == 200
        assert resp2.headers["content-type"].startswith("image/png")


class TestCropBase64AndClear:
    def test_auto_segment_crop_base64(self, client: TestClient) -> None:
        """Auto-segment returns crop_png_base64 for each object."""
        import cv2
        import numpy as np

        create_resp = client.post("/api/projects", json={"name": "B64Proj"})
        pid = create_resp.json()["project_id"]

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((300, 400, 3), 255, dtype=np.uint8)
        frame[50:200, 50:150] = (0, 0, 0)
        frame[80:130, 250:350] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        resp = client.post(
            f"/api/projects/{pid}/auto-segment-objects",
            params={"scene_id": 0, "min_area": 100},
        )
        assert resp.status_code == 200
        objs = resp.json()["objects"]
        assert len(objs) >= 1
        for o in objs:
            assert "crop_png_base64" in o
            assert o["crop_png_base64"] != "", "crop_png_base64 must be non-empty"
            # Verify it decodes as a PNG
            import base64
            raw = base64.b64decode(o["crop_png_base64"])
            assert raw[:8] == b"\x89PNG\r\n\x1a\n", "Not a valid PNG"

    def test_clear_objects(self, client: TestClient) -> None:
        """DELETE /objects clears all tracked objects."""
        create_resp = client.post("/api/projects", json={"name": "ClearProj"})
        pid = create_resp.json()["project_id"]

        # Create an object (needs a frame)
        import cv2
        import numpy as np

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        r = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "Obj1",
                "selection": {"mode": "point", "frame_index": 0, "x": 100, "y": 100},
                "scene_id": 0,
            },
        )
        assert r.status_code == 201

        # Verify object exists
        resp = client.get(f"/api/projects/{pid}/objects")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # DELETE all objects (no trailing slash)
        resp = client.delete(f"/api/projects/{pid}/objects")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify cleared
        resp = client.get(f"/api/projects/{pid}/objects")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

        # DELETE with trailing slash — no 405
        resp2 = client.delete(f"/api/projects/{pid}/objects/")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "ok"


class TestDeleteSingleAndClear:
    def _make_frame_and_object(
        self, client, pid: str, x: int = 100, y: int = 100
    ) -> str:
        """Create a synthetic frame + one object, return object_id."""
        import cv2
        import numpy as np

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        r = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "ObjX",
                "selection": {"mode": "point", "frame_index": 0, "x": x, "y": y},
                "scene_id": 0,
            },
        )
        assert r.status_code == 201
        return r.json()["object_id"]

    def _make_object_with_mask(self, client, pid: str) -> str:
        """Create a synthetic frame + object + mask file, return object_id."""
        import cv2
        import numpy as np

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        r = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "MaskedObj",
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
        assert r.status_code == 201
        oid = r.json()["object_id"]

        # Write a mask file
        mask_dir = proj_root / "projects" / pid / "objects" / oid / "masks"
        mask_dir.mkdir(parents=True, exist_ok=True)
        mask = np.zeros((200, 200), dtype=np.uint8)
        mask[60:140, 60:140] = 255
        cv2.imwrite(str(mask_dir / "mask_000000.png"), mask)
        return oid

    def test_delete_single_object(self, client: TestClient) -> None:
        """Deleting one object keeps the others."""
        create_resp = client.post("/api/projects", json={"name": "DelOne"})
        pid = create_resp.json()["project_id"]

        oid1 = self._make_frame_and_object(client, pid)
        # Create a second object
        import cv2
        import numpy as np

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)
        r2 = client.post(
            f"/api/projects/{pid}/objects",
            json={
                "name": "ObjY",
                "selection": {"mode": "point", "frame_index": 0, "x": 50, "y": 50},
                "scene_id": 0,
            },
        )
        oid2 = r2.json()["object_id"]

        # Verify 2 objects exist
        resp = client.get(f"/api/projects/{pid}/objects")
        assert len(resp.json()) == 2

        # Delete oid1 (no trailing slash)
        resp = client.delete(f"/api/projects/{pid}/objects/{oid1}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        remaining = [o["object_id"] for o in resp.json()["project"]["objects"]]
        assert oid1 not in remaining
        assert oid2 in remaining

        # Trailing slash also works
        resp2 = client.delete(f"/api/projects/{pid}/objects/{oid2}/")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "ok"

        # All gone now
        resp3 = client.get(f"/api/projects/{pid}/objects")
        assert len(resp3.json()) == 0

    def test_clear_all_objects(self, client: TestClient) -> None:
        """Clearing all objects returns project with empty objects list."""
        create_resp = client.post("/api/projects", json={"name": "ClearAll"})
        pid = create_resp.json()["project_id"]

        self._make_frame_and_object(client, pid)
        self._make_frame_and_object(client, pid, x=50, y=50)

        resp = client.delete(f"/api/projects/{pid}/objects")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["project"]["objects"] == []

        # Verify via GET too
        resp2 = client.get(f"/api/projects/{pid}/objects")
        assert len(resp2.json()) == 0

    def test_auto_segment_returns_crop_b64(self, client: TestClient) -> None:
        """Auto-segment returns non-empty crop_png_base64 per object."""
        import cv2
        import numpy as np

        create_resp = client.post("/api/projects", json={"name": "CropB64"})
        pid = create_resp.json()["project_id"]

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((300, 400, 3), 255, dtype=np.uint8)
        frame[50:200, 50:150] = (0, 0, 0)
        frame[80:130, 250:350] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        resp = client.post(
            f"/api/projects/{pid}/auto-segment-objects",
            params={"scene_id": 0, "min_area": 100},
        )
        assert resp.status_code == 200
        objs = resp.json()["objects"]
        assert len(objs) >= 1
        for o in objs:
            assert "crop_png_base64" in o
            assert o["crop_png_base64"] != ""
            import base64
            raw = base64.b64decode(o["crop_png_base64"])
            assert raw[:8] == b"\x89PNG\r\n\x1a\n"

    def test_create_object_dedupes_duplicate_bbox(self, client: TestClient) -> None:
        """Creating an object with the same bbox returns the existing object."""
        import cv2
        import numpy as np

        create_resp = client.post("/api/projects", json={"name": "Dedupe"})
        pid = create_resp.json()["project_id"]

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        payload = {
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
        }
        r1 = client.post(f"/api/projects/{pid}/objects", json=payload)
        assert r1.status_code == 201
        oid1 = r1.json()["object_id"]

        # Same bbox → should return the SAME object (duplicate)
        r2 = client.post(f"/api/projects/{pid}/objects", json=payload)
        assert r2.status_code == 201
        assert r2.json().get("duplicate") is True
        assert r2.json()["object_id"] == oid1

        # Verify only 1 object exists
        resp = client.get(f"/api/projects/{pid}/objects")
        assert len(resp.json()) == 1

    def test_replacement_image_served_after_upload(self, client: TestClient) -> None:
        """GET replacement-image returns the uploaded file (200 image/png)."""
        import cv2
        import numpy as np

        create_resp = client.post("/api/projects", json={"name": "RepImg"})
        pid = create_resp.json()["project_id"]

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        payload = {
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
        }
        r = client.post(f"/api/projects/{pid}/objects", json=payload)
        assert r.status_code == 201
        oid = r.json()["object_id"]

        # Upload a replacement image
        import base64
        ok, enc = cv2.imencode(".png", np.full((64, 64, 3), 200, dtype=np.uint8))
        assert ok
        png_bytes = base64.b64decode(base64.b64encode(enc.tobytes()))
        up = client.post(
            f"/api/projects/{pid}/objects/{oid}/replacement",
            files={"file": ("char.png", png_bytes, "image/png")},
        )
        assert up.status_code == 200

        # GET the image — must be served
        img = client.get(f"/api/projects/{pid}/objects/{oid}/replacement-image")
        assert img.status_code == 200
        assert img.headers["content-type"] == "image/png"
        assert img.content[:8] == b"\x89PNG\r\n\x1a\n"

        # Trailing slash variant too
        img2 = client.get(f"/api/projects/{pid}/objects/{oid}/replacement-image/")
        assert img2.status_code == 200

    def test_auto_match_fallback_when_no_motion(self, client: TestClient) -> None:
        """auto-match returns 200 OK even when source.motion is None."""
        import cv2
        import numpy as np

        create_resp = client.post("/api/projects", json={"name": "AutoMatch"})
        pid = create_resp.json()["project_id"]

        from app.api import deps
        proj_root = deps._config.project_root

        def make_frame(scene: int) -> None:
            frame_dir = proj_root / "projects" / pid / "frames" / f"scene_{scene}"
            frame_dir.mkdir(parents=True, exist_ok=True)
            frame = np.full((200, 200, 3), 255, dtype=np.uint8)
            frame[50:150, 50:150] = (0, 0, 0)
            cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)

        make_frame(0)
        make_frame(1)

        payload = {
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
        }
        r1 = client.post(f"/api/projects/{pid}/objects", json=payload)
        assert r1.status_code == 201
        oid1 = r1.json()["object_id"]

        # Second object in a DIFFERENT scene (no motion data either)
        payload2 = {
            "name": "Nhân vật #2",
            "selection": {
                "mode": "bounding_box",
                "frame_index": 0,
                "x": 70,
                "y": 70,
                "width": 80,
                "height": 80,
            },
            "scene_id": 1,
        }
        r2 = client.post(f"/api/projects/{pid}/objects", json=payload2)
        assert r2.status_code == 201
        oid2 = r2.json()["object_id"]

        # auto-match with NO motion data on source → must NOT 400
        resp = client.post(f"/api/projects/{pid}/objects/{oid1}/auto-match")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert oid2 in body["matched"]

        # Trailing slash variant
        resp2 = client.post(f"/api/projects/{pid}/objects/{oid1}/auto-match/")
        assert resp2.status_code == 200

    def test_mask_and_inpainted_endpoints(self, client: TestClient) -> None:
        """GET object mask image + inpainted frame must serve 200 image/png."""
        create_resp = client.post("/api/projects", json={"name": "MaskTest"})
        pid = create_resp.json()["project_id"]
        oid = self._make_object_with_mask(client, pid)

        # Mask image endpoint
        r = client.get(f"/api/projects/{pid}/objects/{oid}/masks/0")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/png")

        # Trailing slash variant
        r2 = client.get(f"/api/projects/{pid}/objects/{oid}/masks/0/")
        assert r2.status_code == 200

        # Inpainted frame endpoint
        r3 = client.get(f"/api/projects/{pid}/objects/{oid}/inpainted/0")
        assert r3.status_code == 200
        assert r3.headers["content-type"].startswith("image/png")

        # Trailing slash variant
        r4 = client.get(f"/api/projects/{pid}/objects/{oid}/inpainted/0/")
        assert r4.status_code == 200

    def test_mask_and_inpainted_fallback_without_mask(self, client: TestClient) -> None:
        """When no mask exists, inpainted endpoint falls back to original frame."""
        create_resp = client.post("/api/projects", json={"name": "MaskFallback"})
        pid = create_resp.json()["project_id"]
        # Create a frame so the inpainted endpoint can find it
        import cv2
        import numpy as np

        from app.api import deps
        proj_root = deps._config.project_root
        frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame = np.full((200, 200, 3), 255, dtype=np.uint8)
        frame[50:150, 50:150] = (0, 0, 0)
        cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)
        # Create an object but do NOT create a mask
        payload = {
            "name": "Vật thể #1",
            "selection": {
                "mode": "bounding_box",
                "frame_index": 0,
                "x": 100,
                "y": 100,
                "width": 60,
                "height": 60,
            },
            "scene_id": 0,
        }
        r1 = client.post(f"/api/projects/{pid}/objects", json=payload)
        assert r1.status_code == 201
        oid = r1.json()["object_id"]

        # Inpainted must still return 200 (fallback to original frame)
        r3 = client.get(f"/api/projects/{pid}/objects/{oid}/inpainted/0")
        assert r3.status_code == 200
        assert r3.headers["content-type"].startswith("image/")
