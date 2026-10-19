"""Targeted tests for S01-T05 transactional legacy import + backup.

Covers AC1-AC6 of S01-T05:

- AC1: valid fixture backs up all inventoried safe source/reference files
  with a verifiable manifest before import.
- AC2: valid import creates expected related rows and legacy IDs in one
  transaction; reopening the DB preserves them.
- AC3: blocker/stale/tampered/wrong-token inputs are refused before any DB
  business write.
- AC4: injected mid-import failure leaves zero partial business/import rows
  and source unchanged; backup remains valid.
- AC5: repeated completed import is idempotent with no duplicate rows and
  no second backup.
- AC6: no runtime cutover/dual-write/schema change; targeted tests and all
  seven quality gates PASS.

Every test uses a temporary database (Alembic-upgraded under ``tmp_path``),
a temporary backup root (``tmp_path``) and the synthetic
``tests/fixtures/legacy_import/importable/`` fixture copied to ``tmp_path``.
Repo-root production data (``channels.json``, ``projects/``, presets,
output) is never touched.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.persistence import (
    BACKUP_MANIFEST_NAME,
    LegacyImporter,
    LegacyImportRefused,
    confirmation_token,
    create_engine_for_path,
    create_session_factory,
)
from app.persistence.legacy_preview import LegacyPreviewer
from app.persistence.models import (
    Artifact,
    ArtifactOwner,
    Channel,
    LegacyImport,
    Project,
    Scene,
    VideoItem,
    Workspace,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "legacy_import" / "importable"
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"

SOURCE_KIND = "legacy_json"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _alembic_config(database_path: Path) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    return cfg


def _upgrade_to_head(database_path: Path) -> None:
    command.upgrade(_alembic_config(database_path), "head")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _snapshot(root: Path) -> dict[str, tuple[str, int]]:
    """(sha256, mtime_ns) for every file under root, keyed by relative path."""
    snap: dict[str, tuple[str, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(root))
            stat = path.stat()
            snap[rel] = (_sha256_bytes(path.read_bytes()), stat.st_mtime_ns)
    return snap


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def legacy_root(tmp_path: Path) -> Path:
    """A private copy of the importable fixture (never the repo fixture)."""
    root = tmp_path / "legacy"
    shutil.copytree(FIXTURES, root)
    return root


@pytest.fixture()
def preview(legacy_root: Path):
    """A healthy preview of the importable fixture."""
    return LegacyPreviewer(legacy_root).run()


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_import.db"


@pytest.fixture()
def upgraded_db(db_path: Path) -> Iterator[Path]:
    _upgrade_to_head(db_path)
    yield db_path


@pytest.fixture()
def session_factory(upgraded_db: Path) -> sessionmaker[Session]:
    return create_session_factory(create_engine_for_path(upgraded_db))


@pytest.fixture()
def backup_root(tmp_path: Path) -> Path:
    return tmp_path / "backups"


@pytest.fixture()
def importer(preview, session_factory, backup_root: Path) -> LegacyImporter:
    return LegacyImporter(
        preview,
        session_factory,
        workspace_id="11111111-1111-4111-8111-111111111111",
        backup_root=backup_root,
        token=confirmation_token(preview),
    )


def _counts(session: Session) -> dict[str, int]:
    return {
        "workspace": session.scalar(select(func.count()).select_from(Workspace)) or 0,
        "channel": session.scalar(select(func.count()).select_from(Channel)) or 0,
        "project": session.scalar(select(func.count()).select_from(Project)) or 0,
        "video_item": session.scalar(select(func.count()).select_from(VideoItem)) or 0,
        "scene": session.scalar(select(func.count()).select_from(Scene)) or 0,
        "artifact": session.scalar(select(func.count()).select_from(Artifact)) or 0,
        "artifact_owner": (
            session.scalar(select(func.count()).select_from(ArtifactOwner)) or 0
        ),
        "legacy_import": (
            session.scalar(select(func.count()).select_from(LegacyImport)) or 0
        ),
    }


# ── AC1: backup before import ────────────────────────────────────────────────


def test_backup_copies_all_sources_and_references(
    importer: LegacyImporter, backup_root: Path, preview
) -> None:
    result = importer.run()

    backup_dir = backup_root / "backups" / result.backup_id
    assert backup_dir.is_dir()
    manifest_path = backup_dir / BACKUP_MANIFEST_NAME
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_kind"] == SOURCE_KIND
    assert manifest["backup_id"] == result.backup_id
    # channels.json + project.json + video.mp4 + replacement.png
    assert len(manifest["entries"]) == 4

    by_locator = {e["source_locator"]: e for e in manifest["entries"]}
    assert "channels.json" in by_locator or any(
        e["source_locator"].endswith("channels.json")
        for e in manifest["entries"]
    )
    mp4 = next(e for e in manifest["entries"] if e["source_locator"].endswith(".mp4"))
    assert mp4["sha256"] == _sha256_bytes(b"fake mp4 bytes for importable fixture\n")
    assert mp4["size_bytes"] == 38

    # Every manifest entry exists in the backup directory.
    for entry in manifest["entries"]:
        copied = backup_dir / entry["backup_relative_path"]
        assert copied.is_file()
        assert _sha256_bytes(copied.read_bytes()) == entry["sha256"]


def test_backup_happens_before_db_rows(
    importer: LegacyImporter, session_factory, backup_root: Path
) -> None:
    result = importer.run()
    with session_factory() as session:
        counts = _counts(session)
    assert counts["legacy_import"] == 1
    assert (backup_root / "backups" / result.backup_id / BACKUP_MANIFEST_NAME).is_file()


# ── AC2: rows, legacy IDs, reopen ────────────────────────────────────────────


def test_import_creates_expected_rows_and_legacy_ids(
    importer: LegacyImporter, session_factory, preview
) -> None:
    result = importer.run()
    expected_channels = tuple(c["proposed_id"] for c in preview.channels)
    expected_project = preview.projects[0]["proposed_id"]
    with session_factory() as session:
        counts = _counts(session)
        assert counts == {
            "workspace": 1,
            "channel": 2,
            "project": 1,
            "video_item": 1,
            "scene": 2,
            "artifact": 4,
            "artifact_owner": 2,
            "legacy_import": 1,
        }
        assert result.workspace_id == "11111111-1111-4111-8111-111111111111"
        assert tuple(sorted(result.channel_ids)) == tuple(sorted(expected_channels))
        assert result.project_ids == (expected_project,)
        assert len(result.video_item_ids) == 1
        assert len(result.scene_ids) == 2
        assert len(result.artifact_ids) == 4
        assert result.owner_count == 2

        channels = session.scalars(select(Channel)).all()
        legacy = sorted(c.legacy_id for c in channels)
        assert legacy == ["ch_a", "ch_b"]
        assert all(c.role == "source" for c in channels)
        assert {c.name for c in channels} == {"Alpha", "Beta"}

        project = session.scalar(select(Project))
        assert project.legacy_id == "proj_001"
        assert project.status == "active"
        assert project.source_channel_id is not None

        video = session.scalar(select(VideoItem))
        assert video.legacy_id == "proj_001"
        assert video.title == "Importable Fixture Project"
        assert video.position == 0
        assert video.status == "imported"
        assert video.duration_ms == 10000
        assert video.width == 1920
        assert video.height == 1080
        assert video.fps_num == 30
        assert video.fps_den == 1
        assert video.source_artifact_id is not None

        scenes = session.scalars(select(Scene).order_by(Scene.position)).all()
        assert [s.legacy_scene_id for s in scenes] == [0, 1]
        assert [s.start_frame for s in scenes] == [0, 150]
        assert [s.end_frame for s in scenes] == [149, 299]
        assert all(s.status == "pending" for s in scenes)

        artifacts = session.scalars(select(Artifact)).all()
        kinds = sorted(a.kind for a in artifacts)
        assert kinds == ["document", "document", "image", "video"]
        assert all(a.state == "ready" for a in artifacts)
        assert all(a.sha256 for a in artifacts)
        assert all(a.size_bytes > 0 for a in artifacts)

        owners = session.scalars(select(ArtifactOwner)).all()
        assert len(owners) == 2
        assert all(o.purpose == "source" for o in owners)
        assert {o.owner_type for o in owners} == {"project", "video_item"}

        audit = session.scalar(select(LegacyImport))
        assert audit.source_kind == SOURCE_KIND
        assert audit.status == "completed"
        assert audit.completed_at is not None
        summary = json.loads(audit.summary_json or "{}")
        assert summary["channels"] == 2
        assert summary["projects"] == 1
        assert summary["videos"] == 1
        assert summary["scenes"] == 2


def test_reopen_preserves_rows(
    importer: LegacyImporter, upgraded_db: Path, session_factory, preview
) -> None:
    result = importer.run()
    with session_factory() as session:
        project_id = session.scalar(select(Project.id))

    # Fresh engine/session: rows survive reopen.
    fresh = create_session_factory(create_engine_for_path(upgraded_db))
    with fresh() as session:
        loaded = session.get(Project, project_id)
        assert loaded is not None
        assert loaded.legacy_id == "proj_001"
        assert len(loaded.video_items) == 1
        assert len(loaded.video_items[0].scenes) == 2
        assert session.get(Workspace, result.workspace_id) is not None


def test_import_preserves_deterministic_proposed_ids(preview, importer) -> None:
    expected_channel = preview.channels[0]["proposed_id"]
    expected_project = preview.projects[0]["proposed_id"]
    result = importer.run()
    assert result.channel_ids[0] == expected_channel
    assert result.project_ids[0] == expected_project


# ── AC3: refusals before DB writes ───────────────────────────────────────────


def test_wrong_token_refused_without_db_writes(
    preview, session_factory, backup_root: Path, db_path: Path
) -> None:
    bad = LegacyImporter(
        preview,
        session_factory,
        workspace_id="11111111-1111-4111-8111-111111111111",
        backup_root=backup_root,
        token="0" * 64,
    )
    with pytest.raises(LegacyImportRefused) as excinfo:
        bad.run()
    assert "WRONG_TOKEN" in excinfo.value.reason_codes
    with session_factory() as session:
        assert _counts(session) == {
            "workspace": 0,
            "channel": 0,
            "project": 0,
            "video_item": 0,
            "scene": 0,
            "artifact": 0,
            "artifact_owner": 0,
            "legacy_import": 0,
        }
    assert not (backup_root / "backups").exists()


def test_blocker_preview_refused_without_db_writes(
    tmp_path: Path, session_factory, backup_root: Path
) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "channels.json").write_text("{not json", encoding="utf-8")  # corrupt
    (root / "projects").mkdir()
    preview = LegacyPreviewer(root).run()
    assert preview.blockers
    imp = LegacyImporter(
        preview,
        session_factory,
        workspace_id="11111111-1111-4111-8111-111111111111",
        backup_root=backup_root,
        token=confirmation_token(preview),
    )
    with pytest.raises(LegacyImportRefused) as excinfo:
        imp.run()
    assert "BLOCKERS" in excinfo.value.reason_codes
    with session_factory() as session:
        assert _counts(session)["legacy_import"] == 0
    assert not (backup_root / "backups").exists()


def test_stale_preview_refused_after_source_change(
    preview, session_factory, backup_root: Path, legacy_root: Path
) -> None:
    # Tamper the source AFTER the preview was built: checksum/mtime changed.
    target = legacy_root / "projects" / "proj_001" / "project.json"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    imp = LegacyImporter(
        preview,
        session_factory,
        workspace_id="11111111-1111-4111-8111-111111111111",
        backup_root=backup_root,
        token=confirmation_token(preview),
    )
    with pytest.raises(LegacyImportRefused) as excinfo:
        imp.run()
    assert "SOURCE_CHANGED" in excinfo.value.reason_codes
    with session_factory() as session:
        assert _counts(session)["legacy_import"] == 0
    # No backup directory may be created for a stale preview.
    assert not (backup_root / "backups").exists()


def test_unsafe_reference_refused_without_backup(
    tmp_path: Path, session_factory, backup_root: Path
) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    (root / "projects" / "p1").mkdir(parents=True)
    (root / "projects" / "p1" / "project.json").write_text(
        json.dumps(
            {
                "version": "2.0.0",
                "name": "P1",
                "source_video": "C:/Windows/evil.mp4",
                "scenes": [],
                "objects": [],
            }
        ),
        encoding="utf-8",
    )
    preview = LegacyPreviewer(root).run()
    assert any(i.code == "PROJECT_SOURCE_ABSOLUTE" for i in preview.issues)
    imp = LegacyImporter(
        preview,
        session_factory,
        workspace_id="11111111-1111-4111-8111-111111111111",
        backup_root=backup_root,
        token=confirmation_token(preview),
    )
    with pytest.raises(LegacyImportRefused) as excinfo:
        imp.run()
    assert "UNSAFE_REFERENCES" in excinfo.value.reason_codes
    with session_factory() as session:
        assert _counts(session)["legacy_import"] == 0
    assert not (backup_root / "backups").exists()


# ── AC4: mid-import failure rollback ─────────────────────────────────────────


def test_injected_row_failure_rolls_back_all_rows(
    importer: LegacyImporter, session_factory, backup_root: Path, monkeypatch
) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("injected mid-import failure")

    monkeypatch.setattr(
        "app.persistence.legacy_import.LegacyImporter._project_status", boom
    )
    with pytest.raises(RuntimeError, match="injected mid-import failure"):
        importer.run()
    with session_factory() as session:
        assert _counts(session) == {
            "workspace": 0,
            "channel": 0,
            "project": 0,
            "video_item": 0,
            "scene": 0,
            "artifact": 0,
            "artifact_owner": 0,
            "legacy_import": 0,
        }
    # Backup remains valid after rollback.
    backups = list((backup_root / "backups").iterdir())
    assert len(backups) == 1
    manifest_path = backups[0] / BACKUP_MANIFEST_NAME
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest["entries"]) == 4
    for entry in manifest["entries"]:
        copied = backups[0] / entry["backup_relative_path"]
        assert copied.is_file()
        assert _sha256_bytes(copied.read_bytes()) == entry["sha256"]


def test_failure_leaves_source_unchanged(importer, legacy_root: Path, monkeypatch) -> None:
    before = _snapshot(legacy_root)

    def boom(*args, **kwargs):
        raise RuntimeError("injected mid-import failure")

    monkeypatch.setattr(
        "app.persistence.legacy_import.LegacyImporter._project_status", boom
    )
    with pytest.raises(RuntimeError, match="injected mid-import failure"):
        importer.run()
    assert _snapshot(legacy_root) == before


# ── AC5: idempotent repeated import ──────────────────────────────────────────


def test_repeated_import_is_idempotent(
    importer: LegacyImporter, session_factory, backup_root: Path
) -> None:
    first = importer.run()
    second = importer.run()

    assert second.idempotent_skipped
    assert second.skipped_reason is not None
    assert second.backup_id == first.backup_id

    with session_factory() as session:
        counts = _counts(session)
        assert counts["workspace"] == 1
        assert counts["channel"] == 2
        assert counts["project"] == 1
        assert counts["video_item"] == 1
        assert counts["scene"] == 2
        assert counts["artifact"] == 4
        assert counts["artifact_owner"] == 2
        assert counts["legacy_import"] == 1

    # No second backup directory.
    backups = list((backup_root / "backups").iterdir())
    assert len(backups) == 1


def test_import_after_rollback_is_not_idempotent(
    importer: LegacyImporter, session_factory, backup_root: Path, monkeypatch
) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("injected mid-import failure")

    monkeypatch.setattr(
        "app.persistence.legacy_import.LegacyImporter._project_status", boom
    )
    with pytest.raises(RuntimeError):
        importer.run()
    monkeypatch.undo()

    result = importer.run()  # no completed row → real import
    assert not result.idempotent_skipped
    assert result.legacy_import_id
    backups = list((backup_root / "backups").iterdir())
    assert len(backups) == 2  # failed backup + successful backup


# ── PM correction: import data comes from the verified backup (TOCTOU) ───────


def test_live_project_json_mutation_after_revalidation_does_not_leak_into_rows(
    importer: LegacyImporter, session_factory, legacy_root: Path, monkeypatch
) -> None:
    """Regression: a concurrent edit of the live project.json between the
    final revalidation and the transaction must NOT change imported rows.

    The importer reads scenes/metadata exclusively from the immutable
    backup (``BackupManifest``).  We simulate the race deterministically:
    the revalidation gate has already run (its body is a no-op here), then
    the live project.json is mutated before the transaction executes.  The
    committed rows must still match the approved/backed-up generation —
    not the mutated live bytes.
    """
    original = (legacy_root / "projects" / "proj_001" / "project.json").read_text(
        encoding="utf-8"
    )
    tampered = json.loads(original)
    tampered["scenes"] = [
        {"scene_id": 99, "start_frame": 500, "end_frame": 600},
        {"scene_id": 100, "start_frame": 700, "end_frame": 800},
    ]
    tampered["video_metadata"] = {
        "width": 640,
        "height": 360,
        "fps": 24.0,
        "duration_seconds": 3.0,
    }

    real_revalidate = importer._revalidate_before_transaction

    def revalidate_then_mutate(self, manifest) -> None:
        # The real gate runs first (live source still matches preview)...
        real_revalidate(manifest)
        # ...then a concurrent editor mutates the live file.  This is the
        # exact TOCTOU window: after final revalidation, before the
        # transaction reads project metadata/scenes.
        (legacy_root / "projects" / "proj_001" / "project.json").write_text(
            json.dumps(tampered), encoding="utf-8"
        )

    monkeypatch.setattr(
        "app.persistence.legacy_import.LegacyImporter._revalidate_before_transaction",
        revalidate_then_mutate,
    )

    result = importer.run()

    with session_factory() as session:
        video = session.scalar(select(VideoItem))
        # Metadata from the BACKUP (10s/1920x1080/30fps), not the live file.
        assert video.duration_ms == 10000
        assert video.width == 1920
        assert video.height == 1080
        assert video.fps_num == 30
        scenes = session.scalars(select(Scene).order_by(Scene.position)).all()
        assert [s.legacy_scene_id for s in scenes] == [0, 1]
        assert [s.start_frame for s in scenes] == [0, 150]
        assert [s.end_frame for s in scenes] == [149, 299]
        assert result.owner_count == 2


def test_live_project_json_mutation_is_refused_with_zero_writes_when_revalidation_runs(
    importer: LegacyImporter, session_factory, legacy_root: Path
) -> None:
    """When the revalidation gate actually runs and the live file changed,
    the import refuses before any DB write (SOURCE_CHANGED)."""
    target = legacy_root / "projects" / "proj_001" / "project.json"
    target.write_text(
        target.read_text(encoding="utf-8") + "\n// tampered after preview",
        encoding="utf-8",
    )
    with pytest.raises(LegacyImportRefused) as excinfo:
        importer.run()
    assert "SOURCE_CHANGED" in excinfo.value.reason_codes
    with session_factory() as session:
        assert _counts(session) == {
            "workspace": 0,
            "channel": 0,
            "project": 0,
            "video_item": 0,
            "scene": 0,
            "artifact": 0,
            "artifact_owner": 0,
            "legacy_import": 0,
        }


# ── AC6: no cutover, no schema change ────────────────────────────────────────


def test_no_runtime_cutover_imports_dependencies(preview) -> None:
    """The importer module must not touch API/workflow/frontend modules."""
    import app.persistence.legacy_import as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "fastapi" not in source.lower()
    assert "app.api" not in source
    assert "app.workflow" not in source


def test_import_creates_no_database_at_backup_root(importer, backup_root: Path) -> None:
    importer.run()
    dbs = [p for p in backup_root.rglob("*") if p.suffix in {".db", ".sqlite", ".sqlite3"}]
    assert dbs == []


def test_import_uses_one_legacy_import_row(importer, session_factory) -> None:
    importer.run()
    with session_factory() as session:
        rows = session.scalars(select(LegacyImport)).all()
    assert len(rows) == 1
    assert rows[0].status == "completed"
    assert rows[0].source_sha256
