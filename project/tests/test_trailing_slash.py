"""Tests for trailing slash URL handling — no 405 errors."""

from __future__ import annotations


class TestTrailingSlashDelete:
    def test_delete_without_slash(self, client) -> None:
        """DELETE /api/projects/{id} returns 200."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.delete(f"/api/projects/{pid}")
        assert resp.status_code == 200

    def test_delete_with_slash(self, client) -> None:
        """DELETE /api/projects/{id}/ returns 200 (not 405)."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.delete(f"/api/projects/{pid}/")
        assert resp.status_code == 200


class TestTrailingSlashAutoSegment:
    def test_auto_segment_without_slash(self, client) -> None:
        """POST /api/projects/{id}/auto-segment-objects returns 404 (no frames)."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.post(f"/api/projects/{pid}/auto-segment-objects")
        assert resp.status_code == 404

    def test_auto_segment_with_slash(self, client) -> None:
        """POST /api/projects/{id}/auto-segment-objects/ returns 404 (not 405)."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.post(f"/api/projects/{pid}/auto-segment-objects/")
        assert resp.status_code == 404


class TestTrailingSlashCleanup:
    def test_cleanup_without_slash(self, client) -> None:
        """POST /api/projects/{id}/cleanup returns 200."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.post(f"/api/projects/{pid}/cleanup")
        assert resp.status_code == 200

    def test_cleanup_with_slash(self, client) -> None:
        """POST /api/projects/{id}/cleanup/ returns 200 (not 405)."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.post(f"/api/projects/{pid}/cleanup/")
        assert resp.status_code == 200


class TestTrailingSlashAutoMatch:
    def test_auto_match_without_slash(self, client) -> None:
        """POST /api/projects/{id}/objects/{oid}/auto-match returns 404."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.post(f"/api/projects/{pid}/objects/fakeid/auto-match")
        assert resp.status_code == 404

    def test_auto_match_with_slash(self, client) -> None:
        """POST /api/projects/{id}/objects/{oid}/auto-match/ returns 404 (not 405)."""
        create = client.post("/api/projects", json={"name": "Test"})
        pid = create.json()["project_id"]
        resp = client.post(f"/api/projects/{pid}/objects/fakeid/auto-match/")
        assert resp.status_code == 404
