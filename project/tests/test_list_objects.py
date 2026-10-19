"""Tests for list_objects endpoint returning objects with thumbnails."""

from __future__ import annotations


class TestListObjects:
    def test_list_objects_empty(self, client) -> None:
        """GET /objects returns [] for project with no objects."""
        r = client.post("/api/projects", json={"name": "ObjTest"})
        pid = r.json()["project_id"]

        resp = client.get(f"/api/projects/{pid}/objects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 0

    def test_list_objects_has_thumbnail_field(self, client) -> None:
        """Each object response includes thumbnail_base64 field."""
        r = client.post("/api/projects", json={"name": "ObjTest2"})
        pid = r.json()["project_id"]

        resp = client.get(f"/api/projects/{pid}/objects")
        assert resp.status_code == 200
        for obj in resp.json():
            assert "thumbnail_base64" in obj

    def test_list_objects_trailing_slash(self, client) -> None:
        """GET /objects/ also works (no 404/405)."""
        r = client.post("/api/projects", json={"name": "ObjTest3"})
        pid = r.json()["project_id"]

        resp = client.get(f"/api/projects/{pid}/objects/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
