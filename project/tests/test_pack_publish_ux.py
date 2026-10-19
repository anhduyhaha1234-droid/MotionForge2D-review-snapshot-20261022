"""S06-T05 focused tests: Pack Review & Publish UX endpoints.

Covers the nested publish endpoint ``/api/v2/characters/{id}/versions/{v}/publish``
(CAS revision handling, completeness gate, immutability) and the read-only
pose preview endpoint used by the Pack Review UI.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.api import deps
from app.persistence import DEFAULT_WORKSPACE_ID
from app.persistence.artifacts import ManagedRoot
from app.persistence.models import Artifact


def _session():
    service = deps._job_service
    assert service is not None
    return service._session_factory()


def _create_ready_image_artifact(suffix: str = "", write_file: bool = False) -> str:
    """Create a ready image artifact; optionally materialize the managed file."""
    import uuid as _uuid

    uid = _uuid.uuid4().hex[:8]
    rel_path = f"characters/test_pose_{uid}_{suffix}.png"
    if write_file:
        service = deps._job_service
        assert service is not None
        ManagedRoot(service._managed_root).atomic_write_bytes(
            rel_path, b"\x89PNG\r\n\x1a\n" + b"0" * 16
        )
    with _session() as s:
        art = Artifact(
            workspace_id=DEFAULT_WORKSPACE_ID,
            kind="image",
            relative_path=rel_path,
            state="ready",
            size_bytes=24,
            mime_type="image/png",
            sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        )
        s.add(art)
        s.commit()
        return art.id


def _make_character_with_version(
    client: TestClient, code: str = "pack_ux_test"
) -> tuple[str, dict]:
    """Create a character + first pack version; return (character_id, version)."""
    char_resp = client.post(
        "/api/v2/characters",
        json={"name": "Pack UX Test", "code": code},
    )
    assert char_resp.status_code == 201, char_resp.text
    char_id = char_resp.json()["id"]

    ver_resp = client.post(f"/api/v2/characters/{char_id}/versions")
    assert ver_resp.status_code == 201, ver_resp.text
    return char_id, ver_resp.json()


def _attach_all_slots(client: TestClient, version_id: str) -> None:
    slots = ["front", "three_quarter", "side", "back", "sitting", "walking"]
    for slot in slots:
        art_id = _create_ready_image_artifact(slot)
        att_resp = client.post(
            f"/api/v2/characters/versions/{version_id}/assets",
            json={"pose_slot": slot, "artifact_id": art_id},
        )
        assert att_resp.status_code == 200, att_resp.text


def test_nested_publish_rejects_missing_slots(client: TestClient) -> None:
    char_id, version = _make_character_with_version(client)

    resp = client.post(
        f"/api/v2/characters/{char_id}/versions/{version['version']}/publish",
        json={"revision": version["revision"]},
    )
    assert resp.status_code == 422, resp.text
    detail = resp.json()["detail"]
    assert "missing_slots" in detail
    assert len(detail["missing_slots"]) == 6


def test_nested_publish_success_and_immutability(client: TestClient) -> None:
    char_id, version = _make_character_with_version(client)
    _attach_all_slots(client, version["id"])

    resp = client.post(
        f"/api/v2/characters/{char_id}/versions/{version['version']}/publish",
        json={"revision": version["revision"]},
    )
    assert resp.status_code == 200, resp.text
    published = resp.json()
    assert published["status"] == "published"
    assert published["published_at"] is not None

    # Immutable: cannot attach assets to a published version.
    art_extra = _create_ready_image_artifact()
    att_fail = client.post(
        f"/api/v2/characters/versions/{version['id']}/assets",
        json={"pose_slot": "front", "artifact_id": art_extra},
    )
    assert att_fail.status_code == 409

    # Re-publish is idempotent with the NEW revision (CAS bumped after publish).
    repub = client.post(
        f"/api/v2/characters/{char_id}/versions/{version['version']}/publish",
        json={"revision": published["revision"]},
    )
    assert repub.status_code == 200
    assert repub.json()["status"] == "published"


def test_nested_publish_cas_conflict(client: TestClient) -> None:
    char_id, version = _make_character_with_version(client)
    _attach_all_slots(client, version["id"])

    # Stale revision → 409 conflict.
    resp = client.post(
        f"/api/v2/characters/{char_id}/versions/{version['version']}/publish",
        json={"revision": version["revision"] + 99},
    )
    assert resp.status_code == 409, resp.text


def test_nested_publish_not_found(client: TestClient) -> None:
    char_id, version = _make_character_with_version(client)

    # Unknown character → 404
    unknown_char = str(uuid.uuid4())
    resp = client.post(
        f"/api/v2/characters/{unknown_char}/versions/1/publish",
        json={"revision": 1},
    )
    assert resp.status_code == 404

    # Unknown version number for an existing character → 404
    resp = client.post(
        f"/api/v2/characters/{char_id}/versions/999/publish",
        json={"revision": version["revision"]},
    )
    assert resp.status_code == 404


def test_pose_preview_image_serves_managed_file(client: TestClient) -> None:
    char_id, version = _make_character_with_version(client, code="preview_test")

    # No asset attached → 404
    missing = client.get(
        f"/api/v2/characters/{char_id}/versions/{version['version']}/assets/front/image"
    )
    assert missing.status_code == 404

    # Attach a real artifact WITH a managed file on disk → 200 + image bytes
    art_id = _create_ready_image_artifact("front", write_file=True)
    att = client.post(
        f"/api/v2/characters/versions/{version['id']}/assets",
        json={"pose_slot": "front", "artifact_id": art_id},
    )
    assert att.status_code == 200, att.text

    img = client.get(
        f"/api/v2/characters/{char_id}/versions/{version['version']}/assets/front/image"
    )
    assert img.status_code == 200, img.text
    assert img.headers["content-type"].startswith("image/png")
    assert img.content.startswith(b"\x89PNG")

    # Unknown pose slot → 404
    bad = client.get(
        f"/api/v2/characters/{char_id}/versions/{version['version']}/assets/nope/image"
    )
    assert bad.status_code == 404


def test_pose_preview_unknown_character_404(client: TestClient) -> None:
    resp = client.get(
        f"/api/v2/characters/{uuid.uuid4()}/versions/1/assets/front/image"
    )
    assert resp.status_code == 404
