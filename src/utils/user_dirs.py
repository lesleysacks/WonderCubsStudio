"""Per-user, per-platform locations for application data and documents.

Standard library only. Locations follow each platform's convention:

* Windows: ``%APPDATA%\\WonderCubs Studio``
* macOS:   ``~/Library/Application Support/WonderCubs Studio``
* Linux:   ``$XDG_DATA_HOME/wondercubs-studio`` (default ``~/.local/share``)

``WONDERCUBS_DATA_DIR`` overrides the data location (portable installs, tests).
"""
from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import sys

APP_DIR_NAME = "WonderCubs Studio"
LINUX_APP_DIR_NAME = "wondercubs-studio"
DATA_DIR_ENV = "WONDERCUBS_DATA_DIR"


def _platform(platform: str | None) -> str:
    value = platform or sys.platform
    if value.startswith("win"):
        return "windows"
    if value == "darwin":
        return "macos"
    return "linux"


def user_data_dir(
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the folder for databases, settings, logs and backups."""
    env = os.environ if env is None else env
    home = Path.home() if home is None else home
    override = env.get(DATA_DIR_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    kind = _platform(platform)
    if kind == "windows":
        base = env.get("APPDATA", "").strip()
        return (Path(base) if base else home / "AppData" / "Roaming") / APP_DIR_NAME
    if kind == "macos":
        return home / "Library" / "Application Support" / APP_DIR_NAME
    base = env.get("XDG_DATA_HOME", "").strip()
    root = Path(base) if base and Path(base).is_absolute() else home / ".local" / "share"
    return root / LINUX_APP_DIR_NAME


def user_documents_dir(
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Best-effort Documents folder; falls back to the home folder."""
    env = os.environ if env is None else env
    home = Path.home() if home is None else home
    kind = _platform(platform)
    if kind == "windows":
        profile = env.get("USERPROFILE", "").strip()
        return (Path(profile) if profile else home) / "Documents"
    if kind == "linux":
        configured = env.get("XDG_DOCUMENTS_DIR", "").strip()
        if configured and Path(configured).is_absolute():
            return Path(configured)
    documents = home / "Documents"
    return documents if documents.is_dir() or kind != "linux" else home


def default_projects_dir(
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Default location for new project folders (user-visible, easy to back up)."""
    return user_documents_dir(platform, env, home) / APP_DIR_NAME / "Projects"
