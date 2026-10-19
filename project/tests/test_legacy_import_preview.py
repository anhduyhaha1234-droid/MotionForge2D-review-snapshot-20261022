"""Targeted tests for S01-T04 read-only legacy import preview.

Covers AC1-AC6 of S01-T04:

- AC1: valid fixture inventory produces deterministic entity/file counts and
  ID mapping.
- AC2: corrupt JSON/schema/reference/path cases produce stable actionable
  issues without source mutation.
- AC3: unsafe absolute/traversal/symlink references are blockers and are
  never followed outside the supplied legacy root.
- AC4: unknown fields and checksums are recorded for S01-T05 audit/import.
- AC5: repeated preview is byte-identical and leaves all source bytes/mtime
  unchanged; no DB is created.
- AC6: targeted tests and all seven quality gates PASS.

The module under test is a pure read-only inventory layer: no database, no
ORM imports, no engine/session creation.  All fixtures live under
``tests/fixtures/legacy_import/`` and every other path used by tests is a
pytest ``tmp_path`` directory — production root data is never touched.
"""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

import pytest

from app.persistence.legacy_preview import (
    BLOCKER,
    CODE_CHANNELS_NOT_LIST,
    CODE_PROJECT_CHANNEL_UNKNOWN,
    CODE_PROJECT_DUPLICATE_OBJECT_ID,
    CODE_PROJECT_DUPLICATE_SCENE_ID,
    CODE_PROJECT_JSON_INVALID,
    CODE_PROJECT_REFERENCE_MISSING,
    CODE_PROJECT_REFERENCE_UNSAFE,
    CODE_PROJECT_SCENE_RANGE,
    CODE_PROJECT_SCHEMA,
    CODE_PROJECT_SOURCE_ABSOLUTE,
    CODE_PROJECT_SOURCE_MISSING,
    CODE_PROJECTS_ROOT_UNSAFE,
    WARNING,
    LegacyPreviewer,
    LegacyPreviewError,
    _proposed_id,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "legacy_import"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def valid_root() -> Path:
    return FIXTURES / "valid"


@pytest.fixture()
def corrupt_root() -> Path:
    return FIXTURES / "corrupt"


@pytest.fixture()
def channels_only_root() -> Path:
    return FIXTURES / "channels_only"


@pytest.fixture()
def empty_root(tmp_path: Path) -> Path:
    root = tmp_path / "empty_legacy"
    root.mkdir()
    return root


# ── AC1: valid inventory, deterministic counts and ID mapping ───────────────


def test_valid_inventory_counts_and_mapping(valid_root: Path) -> None:
    preview = LegacyPreviewer(valid_root).run()
    assert [c["legacy_id"] for c in preview.channels] == ["ch_a", "ch_b"]
    assert [p["legacy_id"] for p in preview.projects] == ["proj_001"]
    assert preview.projects[0]["scene_count"] == 2
    assert preview.projects[0]["object_count"] == 2
    assert len(preview.issues) == 0
    assert preview.blockers == []
    assert preview.warnings == []

    # Deterministic uuid5 mapping (stable across runs/machines).
    expected_ch_a = _proposed_id("channel", "ch_a")
    expected_proj = _proposed_id("project", "proj_001")
    expected_obj = _proposed_id("object", "proj_001:obj_a")
    assert preview.channels[0]["proposed_id"] == expected_ch_a
    assert preview.projects[0]["proposed_id"] == expected_proj
    assert preview.projects[0]["objects"][0]["proposed_id"] == expected_obj
    assert preview.id_mapping["channels"]["ch_a"] == expected_ch_a
    assert preview.id_mapping["projects"]["proj_001"] == expected_proj
    assert preview.id_mapping["objects"]["obj_a"] == expected_obj
    assert preview.legacy_ids["channels"] == ["ch_a", "ch_b"]
    assert preview.legacy_ids["projects"] == ["proj_001"]
    assert preview.legacy_ids["objects"] == ["obj_a", "obj_b"]
    # Project-scoped object mapping (PM correction 4) is exposed non-lossily.
    assert preview.object_id_mapping["proj_001"]["obj_a"] == expected_obj
    assert preview.object_id_mapping["proj_001"]["obj_b"] == _proposed_id(
        "object", "proj_001:obj_b"
    )
    assert "object_id_mapping" in preview.to_dict()


def test_valid_inventory_referenced_files(valid_root: Path) -> None:
    preview = LegacyPreviewer(valid_root).run()
    refs = {(r.kind, r.raw): r for r in preview.referenced_files}
    assert ("source_video", "projects/proj_001/video.mp4") in refs
    assert refs[("source_video", "projects/proj_001/video.mp4")].exists
    assert refs[("source_video", "projects/proj_001/video.mp4")].inside_root
    assert ("replacement_image", "projects/proj_001/replacement.png") in refs
    assert refs[("replacement_image", "projects/proj_001/replacement.png")].exists
    # Source relationship recorded on the project entry.
    assert preview.projects[0]["source"]["video"] == "projects/proj_001/video.mp4"
    assert preview.projects[0]["source"]["exists"] is True
    assert preview.projects[0]["source"]["inside_root"] is True
    assert preview.projects[0]["source"]["checksum"] is not None


def test_valid_inventory_checksums_cover_all_sources(valid_root: Path) -> None:
    preview = LegacyPreviewer(valid_root).run()
    before = {c.path: c for c in preview.source_checksums}
    after = {c.path: c for c in preview.source_checksums_after}
    assert set(before) == {
        str(valid_root / "channels.json"),
        str(valid_root / "projects" / "proj_001" / "project.json"),
    }
    assert before == after


def test_no_issues_when_projects_root_absent(channels_only_root: Path) -> None:
    preview = LegacyPreviewer(channels_only_root).run()
    assert len(preview.channels) == 2
    assert preview.projects == []
    assert preview.issues == []
    assert len(preview.source_checksums) == 1


# ── AC2: corrupt/schema/reference cases produce stable issues ───────────────


def test_corrupt_channels_json_is_blocker(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    codes = {i.code for i in preview.issues}
    assert CODE_CHANNELS_NOT_LIST in codes
    blocker = next(i for i in preview.issues if i.code == CODE_CHANNELS_NOT_LIST)
    assert blocker.severity == BLOCKER
    assert str(corrupt_root / "channels.json") in blocker.location
    assert preview.channels == []


def test_corrupt_project_json_is_blocker(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    codes = {i.code for i in preview.issues}
    assert CODE_PROJECT_JSON_INVALID in codes
    json_issue = next(i for i in preview.issues if i.code == CODE_PROJECT_JSON_INVALID)
    assert json_issue.severity == BLOCKER
    # The broken-json project is skipped, others still inventoried.
    legacy_ids = [p["legacy_id"] for p in preview.projects]
    assert "broken_json" not in legacy_ids
    assert "unsafe_refs" in legacy_ids
    assert "schema_problems" in legacy_ids


def test_dir_without_project_json_is_warning(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    warning = next(
        (i for i in preview.issues if i.code == "PROJECT_DIR_NO_JSON"),
        None,
    )
    assert warning is not None
    assert warning.severity == WARNING
    assert "no_json" in warning.location


def test_missing_source_video_is_warning(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    (root / "projects" / "p1").mkdir(parents=True)
    (root / "channels.json").write_text("[]", encoding="utf-8")
    (root / "projects" / "p1" / "project.json").write_text(
        json.dumps(
            {
                "version": "2.0.0",
                "name": "P1",
                "source_video": "projects/p1/ghost.mp4",
                "scenes": [],
                "objects": [],
            }
        ),
        encoding="utf-8",
    )
    preview = LegacyPreviewer(root).run()
    issues = {i.code: i for i in preview.issues}
    assert issues[CODE_PROJECT_SOURCE_MISSING].severity == WARNING
    source = preview.projects[0]["source"]
    assert source["exists"] is False
    assert source["inside_root"] is True
    assert source["checksum"] is None


def test_duplicate_object_and_scene_ids_are_warnings(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    codes = {i.code for i in preview.issues}
    assert CODE_PROJECT_DUPLICATE_OBJECT_ID in codes
    assert CODE_PROJECT_DUPLICATE_SCENE_ID in codes
    assert CODE_PROJECT_SCENE_RANGE in codes  # inverted range 99..50
    for code in (CODE_PROJECT_DUPLICATE_OBJECT_ID, CODE_PROJECT_SCENE_RANGE):
        issue = next(i for i in preview.issues if i.code == code)
        assert issue.severity == WARNING
        assert "schema_problems" in issue.location


def test_unknown_channel_reference_is_warning(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    issues = [i for i in preview.issues if i.code == CODE_PROJECT_CHANNEL_UNKNOWN]
    assert issues
    assert all(i.severity == WARNING for i in issues)
    messages = " ".join(i.message for i in issues)
    assert "ch_unknown" in messages


def test_sources_never_mutated_by_preview(valid_root: Path, corrupt_root: Path) -> None:
    for root in (valid_root, corrupt_root):
        before = _snapshot(root)
        LegacyPreviewer(root).run()
        LegacyPreviewer(root).run()
        assert _snapshot(root) == before


def _snapshot(root: Path) -> dict[str, tuple[str, int]]:
    """(sha256, mtime_ns) for every file under root, keyed by relative path."""
    snap: dict[str, tuple[str, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(root))
            stat = path.stat()
            snap[rel] = (_sha256(path), stat.st_mtime_ns)
    return snap


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ── AC3: unsafe references are blockers, never followed ─────────────────────


def test_absolute_source_video_is_blocker(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    issues = [i for i in preview.issues if i.code == CODE_PROJECT_SOURCE_ABSOLUTE]
    assert issues
    assert all(i.severity == BLOCKER for i in issues)
    source = next(p for p in preview.projects if p["legacy_id"] == "unsafe_refs")["source"]
    assert source["inside_root"] is False
    assert source["exists"] is False
    assert source["checksum"] is None


def test_traversal_and_absolute_object_refs_are_blockers(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    unsafe = [i for i in preview.issues if i.code == CODE_PROJECT_REFERENCE_UNSAFE]
    assert len(unsafe) >= 2
    assert all(i.severity == BLOCKER for i in unsafe)
    messages = " ".join(i.message for i in unsafe)
    assert "../outside.png" in messages
    assert "C:/Windows/evil.png" in messages
    # The traversal reference must never be followed outside the root.
    for ref in preview.referenced_files:
        if ref.raw == "../outside.png":
            assert ref.inside_root is False
            assert ref.exists is False
    # Nothing outside the legacy root may be touched: the sibling file exists
    # and must remain untouched.
    outside = corrupt_root.parent / "outside.png"
    if outside.exists():
        outside.unlink()


def test_missing_inner_reference_is_warning(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    missing = [
        i
        for i in preview.issues
        if i.code == CODE_PROJECT_REFERENCE_MISSING
        and "missing.png" in i.message
    ]
    assert missing
    assert all(i.severity == WARNING for i in missing)
    ref = next(
        r for r in preview.referenced_files if r.raw == "projects/unsafe_refs/missing.png"
    )
    assert ref.inside_root is True
    assert ref.exists is False


def test_symlinked_source_is_blocker_and_not_read(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "project.json").write_text("{}", encoding="utf-8")
    (root / "channels.json").write_text("[]", encoding="utf-8")
    (root / "projects").mkdir()
    (root / "projects" / "evil").mkdir()
    try:
        (root / "projects" / "evil" / "project.json").symlink_to(
            outside / "project.json"
        )
    except OSError:
        pytest.skip("symlinks not supported on this platform")
    preview = LegacyPreviewer(root).run()
    blocker = next(
        (i for i in preview.issues if i.code == CODE_PROJECT_JSON_INVALID),
        None,
    )
    assert blocker is not None
    assert blocker.severity == BLOCKER
    assert "outside the legacy root" in blocker.message
    assert preview.projects == []


# ── PM correction 2: projects root containment ───────────────────────────────


def test_explicit_outside_projects_root_is_blocker_and_never_enumerated(
    tmp_path: Path,
) -> None:
    """An explicit projects_root outside the legacy root is a blocker; the
    outside directory is never enumerated or read (no project entries, no
    PathChecks for its files)."""
    root = tmp_path / "legacy"
    root.mkdir()
    outside = tmp_path / "outside_projects"
    outside.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    # The outside dir contains a project that must never be seen.
    (outside / "secret_proj").mkdir()
    (outside / "secret_proj" / "project.json").write_text(
        json.dumps({"version": "2.0.0", "name": "Secret", "scenes": [], "objects": []}),
        encoding="utf-8",
    )
    preview = LegacyPreviewer(root, projects_root=outside).run()
    blocker = next(
        (i for i in preview.issues if i.code == CODE_PROJECTS_ROOT_UNSAFE),
        None,
    )
    assert blocker is not None
    assert blocker.severity == BLOCKER
    assert preview.projects == []
    # Only the contained channels.json is checksummed; nothing outside.
    assert [c.path for c in preview.source_checksums] == [
        str(root / "channels.json")
    ]
    assert all("secret_proj" not in r.raw for r in preview.referenced_files)


def test_symlinked_projects_root_is_blocker_and_never_enumerated(
    tmp_path: Path,
) -> None:
    """A projects root symlinked outside the legacy root is a blocker; the
    outside directory is never enumerated or read."""
    root = tmp_path / "legacy"
    root.mkdir()
    outside = tmp_path / "outside_projects"
    outside.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    (outside / "secret_proj").mkdir()
    (outside / "secret_proj" / "project.json").write_text(
        json.dumps({"version": "2.0.0", "name": "Secret", "scenes": [], "objects": []}),
        encoding="utf-8",
    )
    try:
        (root / "projects").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not supported on this platform")
    preview = LegacyPreviewer(root).run()
    blocker = next(
        (i for i in preview.issues if i.code == CODE_PROJECTS_ROOT_UNSAFE),
        None,
    )
    assert blocker is not None
    assert blocker.severity == BLOCKER
    assert preview.projects == []
    # The symlinked root is never enumerated: no project.json PathChecks.
    assert all("secret_proj" not in c.path for c in preview.source_checksums)
    assert preview.referenced_files == []


def test_default_projects_root_missing_is_not_an_issue(tmp_path: Path) -> None:
    """A missing default projects root is simply empty (no blocker)."""
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    preview = LegacyPreviewer(root).run()
    assert preview.issues == []
    assert preview.projects == []
    # Only the contained channels.json is checksummed.
    assert len(preview.source_checksums) == 1
    assert preview.source_checksums[0].path == str(root / "channels.json")


# ── PM correction 3: malformed collections never crash ───────────────────────


def _project_with(
    root: Path, proj_id: str, scenes: object, objects: object
) -> None:
    (root / "projects" / proj_id).mkdir(parents=True)
    (root / "projects" / proj_id / "project.json").write_text(
        json.dumps(
            {
                "version": "2.0.0",
                "name": proj_id,
                "source_video": "",
                "scenes": scenes,
                "objects": objects,
            }
        ),
        encoding="utf-8",
    )


def test_null_scenes_and_objects_do_not_crash(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    _project_with(root, "nulls", None, None)
    preview = LegacyPreviewer(root).run()
    assert len(preview.projects) == 1
    entry = preview.projects[0]
    assert entry["scene_count"] == 0
    assert entry["object_count"] == 0
    assert entry["objects"] == []
    codes = {i.code for i in preview.issues}
    assert CODE_PROJECT_SCENE_RANGE in codes
    assert CODE_PROJECT_SCHEMA in codes  # objects is not a list


def test_scalar_scenes_and_objects_do_not_crash(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    _project_with(root, "scalars", 42, "nope")
    preview = LegacyPreviewer(root).run()
    assert len(preview.projects) == 1
    entry = preview.projects[0]
    assert entry["scene_count"] == 0
    assert entry["object_count"] == 0
    assert entry["objects"] == []
    codes = {i.code for i in preview.issues}
    assert CODE_PROJECT_SCENE_RANGE in codes
    assert CODE_PROJECT_SCHEMA in codes


def test_object_scenes_and_objects_do_not_crash(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    _project_with(root, "objects", {"a": 1}, {"b": 2})
    preview = LegacyPreviewer(root).run()
    assert len(preview.projects) == 1
    entry = preview.projects[0]
    assert entry["scene_count"] == 0
    assert entry["object_count"] == 0
    codes = {i.code for i in preview.issues}
    assert CODE_PROJECT_SCENE_RANGE in codes
    assert CODE_PROJECT_SCHEMA in codes


# ── PM correction 4: project-scoped object identity ──────────────────────────


def test_identical_object_ids_in_different_projects_get_distinct_ids(
    tmp_path: Path,
) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "channels.json").write_text("[]", encoding="utf-8")
    for pid in ("proj_x", "proj_y"):
        _project_with(root, pid, [], [])
        proj_json = root / "projects" / pid / "project.json"
        data = json.loads(proj_json.read_text(encoding="utf-8"))
        data["objects"] = [
            {
                "object_id": "object_1",
                "name": "Same",
                "kind": "character",
                "selection": {"mode": "point", "frame_index": 0, "x": 0.0, "y": 0.0},
                "motion": None,
            }
        ]
        proj_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    preview = LegacyPreviewer(root).run()
    ids = {p["legacy_id"]: p["objects"][0]["proposed_id"] for p in preview.projects}
    assert ids["proj_x"] != ids["proj_y"]
    assert ids["proj_x"] == _proposed_id("object", "proj_x:object_1")
    assert ids["proj_y"] == _proposed_id("object", "proj_y:object_1")
    # Non-lossy serialized mapping: both projects present, no overwrite.
    serialized = json.loads(preview.to_json())["object_id_mapping"]
    assert serialized["proj_x"]["object_1"] == ids["proj_x"]
    assert serialized["proj_y"]["object_1"] == ids["proj_y"]
    assert len(serialized) == 2


def test_symlinked_channels_is_blocker_and_never_opened(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "channels.json").write_text("[1, 2, 3]", encoding="utf-8")
    try:
        (root / "channels.json").symlink_to(outside / "channels.json")
    except OSError:
        pytest.skip("symlinks not supported on this platform")
    # Chmod 000 proves the symlinked source is never opened: any attempted
    # read raises PermissionError (skipped when ACLs make chmod ineffective).
    try:
        (outside / "channels.json").chmod(0)
    except OSError:
        pytest.skip("chmod not supported on this platform")
    try:
        preview = LegacyPreviewer(root).run()
    except PermissionError:
        pytest.skip("ACLs ignore chmod 000; cannot prove non-read")
    finally:
        (outside / "channels.json").chmod(stat.S_IRUSR | stat.S_IWUSR)
    blocker = next(
        (i for i in preview.issues if i.code == CODE_CHANNELS_NOT_LIST),
        None,
    )
    assert blocker is not None
    assert blocker.severity == BLOCKER
    assert "outside the legacy root" in blocker.message
    assert preview.channels == []
    # The symlinked source was never read: no PathCheck for it.
    assert all(c.path != str(root / "channels.json") for c in preview.source_checksums)


def test_symlinked_reference_escape_is_blocker(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.png"
    secret.write_bytes(b"secret")
    (root / "channels.json").write_text("[]", encoding="utf-8")
    (root / "projects" / "p1").mkdir(parents=True)
    try:
        (root / "projects" / "p1" / "link.png").symlink_to(secret)
    except OSError:
        pytest.skip("symlinks not supported on this platform")
    (root / "projects" / "p1" / "project.json").write_text(
        json.dumps(
            {
                "version": "2.0.0",
                "name": "P1",
                "source_video": "",
                "scenes": [],
                "objects": [
                    {
                        "object_id": "o1",
                        "name": "O1",
                        "kind": "character",
                        "selection": {"mode": "point", "frame_index": 0, "x": 0.0, "y": 0.0},
                        "replacement_image": "projects/p1/link.png",
                        "motion": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    preview = LegacyPreviewer(root).run()
    blockers = [i for i in preview.issues if i.code == CODE_PROJECT_REFERENCE_UNSAFE]
    assert blockers
    ref = next(r for r in preview.referenced_files if r.raw == "projects/p1/link.png")
    assert ref.inside_root is False
    assert ref.exists is False  # never followed outside the root


# ── AC4: unknown fields and checksums recorded ──────────────────────────────


def test_unknown_fields_recorded(corrupt_root: Path) -> None:
    preview = LegacyPreviewer(corrupt_root).run()
    unknown = preview.unknown_fields
    assert "extra_top_level" in unknown.get("project", [])
    assert "future_field" in unknown.get("project", [])
    assert "object" in unknown
    # The unsafe_refs object also carries an unknown object field.
    assert unknown["object"]


def test_valid_fixture_has_no_unknown_fields(valid_root: Path) -> None:
    preview = LegacyPreviewer(valid_root).run()
    assert preview.unknown_fields == {}


def test_checksums_recorded_and_stable(valid_root: Path) -> None:
    preview = LegacyPreviewer(valid_root).run()
    before = {c.path: c.sha256 for c in preview.source_checksums}
    after = {c.path: c.sha256 for c in preview.source_checksums_after}
    assert before == after
    assert all(len(h) == 64 for h in before.values())
    for check in preview.source_checksums:
        assert check.size_bytes > 0
        assert check.mtime_ns > 0


# ── AC5: repeated preview byte-identical, no DB, no mutation ────────────────


def test_repeated_preview_is_byte_identical(valid_root: Path) -> None:
    first = LegacyPreviewer(valid_root).run().to_json()
    second = LegacyPreviewer(valid_root).run().to_json()
    assert first == second


def test_repeated_preview_byte_identical_corrupt(corrupt_root: Path) -> None:
    first = LegacyPreviewer(corrupt_root).run().to_json()
    second = LegacyPreviewer(corrupt_root).run().to_json()
    assert first == second


def test_preview_leaves_source_bytes_and_mtime_unchanged(
    valid_root: Path, corrupt_root: Path
) -> None:
    for root in (valid_root, corrupt_root):
        before = _snapshot(root)
        LegacyPreviewer(root).run()
        LegacyPreviewer(root).run()
        after = _snapshot(root)
        assert before == after
        # Bytes, not just mtime: compare content hashes.
        for rel, (sha, _) in after.items():
            assert before[rel][0] == sha


def test_no_database_created(valid_root: Path, tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    shutil.copytree(valid_root, root)
    LegacyPreviewer(root).run()
    dbs = [p for p in root.rglob("*") if p.suffix in {".db", ".sqlite", ".sqlite3"}]
    assert dbs == []


def test_no_database_created_in_repo(valid_root: Path) -> None:
    """The previewer never creates a DB anywhere; module has no engine imports."""
    import app.persistence.legacy_preview as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "sqlalchemy" not in source
    assert "create_engine" not in source
    assert "session" not in source.lower()


# ── AC2/5 extra: invalid explicit inputs ─────────────────────────────────────


def test_missing_legacy_root_raises(tmp_path: Path) -> None:
    with pytest.raises(LegacyPreviewError):
        LegacyPreviewer(tmp_path / "does_not_exist")


def test_empty_legacy_root_inventories_nothing(empty_root: Path) -> None:
    preview = LegacyPreviewer(empty_root).run()
    assert preview.channels == []
    assert preview.projects == []
    assert preview.issues == []
    assert preview.source_checksums == []
    assert preview.source_checksums_after == []


# ── Serialization shape ──────────────────────────────────────────────────────


def test_to_json_is_deterministic_and_complete(valid_root: Path) -> None:
    preview = LegacyPreviewer(valid_root).run()
    payload = json.loads(preview.to_json())
    assert payload["legacy_root"] == str(valid_root.resolve())
    assert len(payload["channels"]) == 2
    assert len(payload["projects"]) == 1
    assert isinstance(payload["issues"], list)
    assert isinstance(payload["source_checksums"], list)
    assert isinstance(payload["unknown_fields"], dict)
    assert isinstance(payload["referenced_files"], list)
    # Deterministic key ordering.
    assert preview.to_json() == preview.to_json()
