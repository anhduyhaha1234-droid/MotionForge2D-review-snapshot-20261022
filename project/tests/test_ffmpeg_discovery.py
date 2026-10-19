"""Tests for the shared FFmpeg/ffprobe discovery authority.

These tests exercise the resolution order and error behavior of
``app.services.ffmpeg_utils`` WITHOUT relying on any machine installation:
every scenario is built from temporary directories and monkeypatched
environment state, so the suite passes on a machine with no FFmpeg.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from app.services import ffmpeg_utils


def _is_windows() -> bool:
    """Return True when running on Windows (os.name == 'nt')."""
    return os.name == "nt"


def _make_platform_executable(path: Path) -> None:
    """Create a candidate that satisfies the platform suitability contract.

    - Windows: create the file with a ``.exe`` suffix (content irrelevant).
    - POSIX: create a regular file and set the owner execute bit.
    """
    path.write_bytes(b"fake-binary")
    if not _is_windows():
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove discovery-affecting env vars and PATH for each test."""
    monkeypatch.delenv("MOTIONFORGE_FFMPEG", raising=False)
    monkeypatch.delenv("MOTIONFORGE_FFPROBE", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)


@pytest.fixture
def fake_binary(tmp_path: Path) -> Path:
    """Create a dummy executable-suitable binary (per platform contract)."""
    exe = tmp_path / "ffmpeg.exe"
    _make_platform_executable(exe)
    return exe


class TestValidOverride:
    def test_ffmpeg_override_wins(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Valid MOTIONFORGE_FFMPEG override is returned verbatim."""
        exe = tmp_path / "ffmpeg.exe"
        _make_platform_executable(exe)
        monkeypatch.setenv("MOTIONFORGE_FFMPEG", str(exe))
        # PATH is stripped so the override is the ONLY way to resolve.
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        assert ffmpeg_utils.find_ffmpeg() == str(exe)

    def test_ffprobe_override_wins(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Valid MOTIONFORGE_FFPROBE override is returned verbatim."""
        exe = tmp_path / "ffprobe.exe"
        _make_platform_executable(exe)
        monkeypatch.setenv("MOTIONFORGE_FFPROBE", str(exe))
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        assert ffmpeg_utils.find_ffprobe() == str(exe)


class TestInvalidOverride:
    def test_ffmpeg_invalid_override_raises(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """A set-but-invalid override raises — no silent fallback to PATH."""
        monkeypatch.setenv("MOTIONFORGE_FFMPEG", str(tmp_path / "missing.exe"))
        monkeypatch.setenv("PATH", str(tmp_path))
        with pytest.raises(FileNotFoundError, match="MOTIONFORGE_FFMPEG"):
            ffmpeg_utils.find_ffmpeg()

    def test_ffprobe_invalid_override_raises(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """A set-but-invalid ffprobe override raises."""
        monkeypatch.setenv("MOTIONFORGE_FFPROBE", str(tmp_path / "missing.exe"))
        with pytest.raises(FileNotFoundError, match="MOTIONFORGE_FFPROBE"):
            ffmpeg_utils.find_ffprobe()


class TestInvalidOverrideCandidate:
    """Invalid override candidates must raise and never fall back.

    A candidate that exists as a file but does NOT satisfy the platform
    executable-suitability contract (Windows: .exe suffix; POSIX: regular
    file with execute permission) must be rejected with an actionable
    FileNotFoundError — even when a valid binary exists on PATH.
    """

    def test_text_file_override_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """A regular non-executable text file override is rejected.

        The candidate does not satisfy the platform executable-suitability
        contract (Windows: must end in .exe; POSIX: must have the execute
        bit), so the override raises an actionable error instead of
        silently falling back to PATH.
        """
        text_file = tmp_path / "ffmpeg.txt"
        text_file.write_text("this is not a binary\n", encoding="utf-8")
        monkeypatch.setenv("MOTIONFORGE_FFMPEG", str(text_file))
        # A valid candidate on PATH must NOT be used as a fallback.
        real = tmp_path / "real" / "ffmpeg.exe"
        real.parent.mkdir()
        _make_platform_executable(real)
        monkeypatch.setenv("PATH", str(real.parent))
        with pytest.raises(FileNotFoundError, match="MOTIONFORGE_FFMPEG"):
            ffmpeg_utils.find_ffmpeg()

    def test_unsupported_suffix_override_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """An override with an unsupported suffix is rejected on Windows.

        On POSIX the suffix is irrelevant (regular file + execute bit is
        sufficient), so this assertion is scoped to Windows only.
        """
        if not _is_windows():
            pytest.skip("Unsupported-suffix contract applies on Windows only")
        script = tmp_path / "ffmpeg.bat"
        script.write_text("@echo fake\n", encoding="utf-8")
        monkeypatch.setenv("MOTIONFORGE_FFMPEG", str(script))
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        with pytest.raises(FileNotFoundError, match="MOTIONFORGE_FFMPEG"):
            ffmpeg_utils.find_ffmpeg()

    def test_non_executable_override_rejected_on_posix(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """A regular file without execute permission is rejected on POSIX."""
        if _is_windows():
            pytest.skip("Execute-bit contract applies on POSIX only")
        non_exec = tmp_path / "ffmpeg"
        non_exec.write_bytes(b"fake-binary")
        # No chmod: owner execute bit is NOT set.
        monkeypatch.setenv("MOTIONFORGE_FFMPEG", str(non_exec))
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        with pytest.raises(FileNotFoundError, match="MOTIONFORGE_FFMPEG"):
            ffmpeg_utils.find_ffmpeg()

    def test_missing_override_rejected_no_fallback(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """A missing override raises even when PATH has a valid candidate."""
        monkeypatch.setenv("MOTIONFORGE_FFMPEG", str(tmp_path / "missing.exe"))
        real = tmp_path / "real" / "ffmpeg.exe"
        real.parent.mkdir()
        _make_platform_executable(real)
        monkeypatch.setenv("PATH", str(real.parent))
        with pytest.raises(FileNotFoundError, match="MOTIONFORGE_FFMPEG"):
            ffmpeg_utils.find_ffmpeg()


class TestPathDiscovery:
    def test_path_used_when_no_override(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """Executable on PATH is found when no override is set."""
        exe = tmp_path / "ffmpeg.exe"
        _make_platform_executable(exe)
        monkeypatch.setenv("PATH", str(tmp_path))
        found = ffmpeg_utils.find_ffmpeg()
        # shutil.which may normalize the extension case on Windows (.EXE).
        assert Path(found).resolve() == exe.resolve()
        assert Path(found).name.lower() == "ffmpeg.exe"

    def test_path_respects_pathexe_on_windows(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """PATH discovery follows PATHEXT; on Windows .cmd resolves.

        NOTE: this covers PATH discovery via shutil.which (which honors
        PATHEXT). It does NOT mean .cmd is a supported override suffix —
        the override contract requires .exe on Windows.
        """
        exe = tmp_path / "ffprobe.cmd"
        exe.write_bytes(b"@echo fake")
        monkeypatch.setenv("PATH", str(tmp_path))
        found = ffmpeg_utils.find_ffprobe()
        assert Path(found).resolve() == exe.resolve()


class TestWingetLinks:
    def test_winget_links_used(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """WinGet Links candidate under LOCALAPPDATA is found."""
        links = tmp_path / "Local" / "Microsoft" / "WinGet" / "Links"
        links.mkdir(parents=True)
        exe = links / "ffmpeg.exe"
        _make_platform_executable(exe)
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
        # Strip PATH so the WinGet fallback is the only resolver.
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        assert ffmpeg_utils.find_ffmpeg() == str(exe)

    def test_winget_links_ignored_without_localappdata(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """No LOCALAPPDATA -> WinGet candidate is skipped (not-found error)."""
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        with pytest.raises(FileNotFoundError, match="not found"):
            ffmpeg_utils.find_ffmpeg()


class TestNotFound:
    def test_not_found_error_is_actionable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """Not-found raises an actionable error with install guidance."""
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        with pytest.raises(FileNotFoundError) as excinfo:
            ffmpeg_utils.find_ffmpeg()
        message = str(excinfo.value)
        assert "ffmpeg not found" in message
        assert "MOTIONFORGE_FFMPEG" in message
        assert "winget" in message

    def test_ffprobe_not_found_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """ffprobe not-found error names the right binary and override."""
        monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
        with pytest.raises(FileNotFoundError) as excinfo:
            ffmpeg_utils.find_ffprobe()
        message = str(excinfo.value)
        assert "ffprobe not found" in message
        assert "MOTIONFORGE_FFPROBE" in message


class TestModuleContract:
    def test_module_is_single_authority(self) -> None:
        """The module exports the two public discovery functions."""
        assert callable(ffmpeg_utils.find_ffmpeg)
        assert callable(ffmpeg_utils.find_ffprobe)

    def test_winget_helper_returns_none_without_localappdata(self) -> None:
        """_winget_links_candidate returns None when LOCALAPPDATA is unset."""
        assert ffmpeg_utils._winget_links_candidate("ffmpeg") is None

    def test_portable_candidate_is_reserved(self) -> None:
        """No portable-location contract exists yet -> always None."""
        assert ffmpeg_utils._portable_candidate("ffmpeg") is None

    def test_candidate_contract_exe_accepted(self, tmp_path: Path) -> None:
        """An .exe candidate satisfies the suitability contract."""
        exe = tmp_path / "ffmpeg.exe"
        _make_platform_executable(exe)
        assert ffmpeg_utils._is_executable_candidate(exe) is True

    def test_candidate_contract_missing_rejected(self, tmp_path: Path) -> None:
        """A missing path never satisfies the suitability contract."""
        missing = tmp_path / "ffmpeg.exe"
        assert ffmpeg_utils._is_executable_candidate(missing) is False

    def test_candidate_contract_text_file_rejected(self, tmp_path: Path) -> None:
        """A regular text file without the platform contract is rejected.

        On Windows the contract is suffix-based: a text file named .exe
        IS accepted (Windows itself treats the suffix as the executable
        marker), while a text file with any other suffix is rejected. On
        POSIX the file must have the execute bit, regardless of suffix.
        """
        if _is_windows():
            non_exe = tmp_path / "ffmpeg.txt"
            non_exe.write_text("this is not a binary\n", encoding="utf-8")
            assert ffmpeg_utils._is_executable_candidate(non_exe) is False
        else:
            no_exec = tmp_path / "ffmpeg"
            no_exec.write_text("this is not a binary\n", encoding="utf-8")
            assert ffmpeg_utils._is_executable_candidate(no_exec) is False

    def test_candidate_contract_posix_execute_bit(self, tmp_path: Path) -> None:
        """On POSIX, execute permission is required (suffix is irrelevant)."""
        if _is_windows():
            pytest.skip("Execute-bit contract applies on POSIX only")
        no_exec = tmp_path / "ffmpeg"
        no_exec.write_bytes(b"fake-binary")
        assert ffmpeg_utils._is_executable_candidate(no_exec) is False
        _make_platform_executable(no_exec)
        assert ffmpeg_utils._is_executable_candidate(no_exec) is True
