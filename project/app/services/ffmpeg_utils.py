"""Shared utilities for FFmpeg/ffprobe binary discovery.

This module is the SINGLE authority for locating the FFmpeg and ffprobe
executables used by every MotionForge service. Do not duplicate the
discovery logic elsewhere; import ``find_ffmpeg`` / ``find_ffprobe`` from
here instead.

Resolution order (first match wins):

1. Explicit environment override:
   ``MOTIONFORGE_FFMPEG`` / ``MOTIONFORGE_FFPROBE`` — the path must point to
   an executable-suitable file for the platform (Windows: ``.exe``; POSIX:
   regular file with execute permission) or an actionable error is raised.
   No silent fallback.
2. Executable on ``PATH`` (via :func:`shutil.which`).
3. Windows WinGet Links directory, derived from ``LOCALAPPDATA``
   (``%LOCALAPPDATA%\\Microsoft\\WinGet\\Links\\<name>.exe``).
4. Portable app-managed location. There is no such contract in the repo
   today; when one is introduced, add it here (see README "FFmpeg
   configuration").
5. Actionable :class:`FileNotFoundError` with install guidance — never a
   guessed username/machine path.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def _is_executable_candidate(path: Path) -> bool:
    """Return True if ``path`` looks like an executable binary.

    The check is a cross-platform suitability contract; it never executes
    the candidate.

    - Windows (``os.name == "nt"``): the file must have a supported
      executable suffix. The only suffix supported by this contract is
      ``.exe``; other suffixes (``.bat``, ``.cmd``, ``.ps1``, no suffix)
      are intentionally NOT accepted because FFmpeg/ffprobe are native
      executables, not script interpreters we control.
    - POSIX: the file must be a regular file with at least one execute
      permission bit set (``os.access(..., os.X_OK)``).
    """
    if not path.is_file():
        return False
    if os.name == "nt":
        return path.suffix.lower() == ".exe"
    return os.access(path, os.X_OK)


def _env_override(name: str) -> str | None:
    """Return the validated explicit override for ``name`` if set.

    The override must be a non-empty string pointing to an existing,
    executable-suitable file (see :func:`_is_executable_candidate`). A
    set-but-invalid override raises FileNotFoundError instead of silently
    falling back to the other resolution steps.
    """
    env_key = f"MOTIONFORGE_{name.upper()}"
    raw = os.environ.get(env_key, "").strip()
    if not raw:
        return None
    override = Path(raw)
    if not _is_executable_candidate(override):
        raise FileNotFoundError(
            f"{env_key} is set to {raw!r}, but that path is not an "
            f"executable-suitable file for this platform (on Windows a "
            f".exe file is required; on POSIX a regular file with execute "
            f"permission). Fix the variable or unset it to use the normal "
            f"discovery order."
        )
    return str(override)


def _winget_links_candidate(name: str) -> Path | None:
    """Return the WinGet Links candidate for ``name``, if present.

    The WinGet Links directory is resolved from ``LOCALAPPDATA`` so the
    lookup works for any Windows user (no hard-coded username). Only
    executable-suitable candidates are accepted.
    """
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return None
    candidate = Path(local_app_data) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
    if _is_executable_candidate(candidate):
        return candidate
    return None


def _portable_candidate(name: str) -> Path | None:
    """Return a portable app-managed FFmpeg location, if a contract exists.

    No portable-location contract is defined in the repository yet. When a
    portable bundle is added, resolve it here (e.g. from an environment
    variable or a path relative to the repo) and document it in the README.
    """
    del name  # reserved for the future portable-location contract
    return None


def _find_binary(name: str) -> str:
    """Find a binary by name using the documented resolution order.

    Args:
        name: Binary name (e.g., "ffmpeg" or "ffprobe").

    Returns:
        Full path to the binary.

    Raises:
        FileNotFoundError: If the binary is not found anywhere.
    """
    # 1. Explicit environment override (validated — no silent fallback)
    override = _env_override(name)
    if override is not None:
        return override

    # 2. Executable on PATH
    found = shutil.which(name)
    if found:
        return found

    # 3. Windows WinGet Links (derived from LOCALAPPDATA)
    winget = _winget_links_candidate(name)
    if winget is not None:
        # Add to PATH for subprocess children so sibling tools (ffprobe,
        # ffplay) resolve the same way.
        links_dir = str(winget.parent)
        if links_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = links_dir + os.pathsep + os.environ.get("PATH", "")
        return str(winget)

    # 4. Portable app-managed location (no contract defined yet)
    portable = _portable_candidate(name)
    if portable is not None:
        return str(portable)

    # 5. Actionable error — never guess a username/machine path
    raise FileNotFoundError(
        f"{name} not found. Install FFmpeg (which also provides ffprobe) "
        "and ensure it is on PATH, or install via `winget install "
        "Gyan.FFmpeg`, or set the MOTIONFORGE_FFMPEG / MOTIONFORGE_FFPROBE "
        "environment variables to the full path of the executables. See "
        "README.md 'FFmpeg configuration'."
    )


def find_ffmpeg() -> str:
    """Locate the ffmpeg executable.

    See module docstring for the resolution order.
    """
    return _find_binary("ffmpeg")


def find_ffprobe() -> str:
    """Locate the ffprobe executable.

    See module docstring for the resolution order.
    """
    return _find_binary("ffprobe")
