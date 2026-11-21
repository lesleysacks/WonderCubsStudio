"""Centralized filesystem paths for the application."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.user_dirs import default_projects_dir, user_data_dir


@dataclass(frozen=True)
class AppPaths:
    """Filesystem paths used by WonderCubs Studio.

    ``base_path`` is the installation (source) folder and is treated as
    read-only. User data lives under ``data_root``. When ``data_root`` is not
    given, data is kept under ``base_path`` (the pre-M0.5 layout), which tests
    and legacy-data detection use.
    """

    base_path: Path
    data_root: Path | None = None
    default_projects_root: Path | None = None

    @classmethod
    def for_current_user(cls, base_path: Path) -> "AppPaths":
        """Paths for an installed application: data in the per-user folder."""
        return cls(
            base_path=base_path,
            data_root=user_data_dir(),
            default_projects_root=default_projects_dir(),
        )

    @property
    def root(self) -> Path:
        return self.data_root if self.data_root is not None else self.base_path

    @property
    def assets_dir(self) -> Path:
        return self.base_path / "assets"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def projects_dir(self) -> Path:
        """Default project folder (the saved setting may point elsewhere)."""
        if self.default_projects_root is not None:
            return self.default_projects_root
        return self.root / "projects"

    @property
    def templates_dir(self) -> Path:
        return self.base_path / "templates"

    @property
    def config_file(self) -> Path:
        return self.root / "config.json"

    @property
    def database_file(self) -> Path:
        return self.data_dir / "database.db"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    def ensure_directories(self) -> None:
        """Create required directories if they are missing.

        With a separate ``data_root`` nothing is written to the installation
        folder; the project folder is created when the first project is.
        """
        if self.data_root is None:
            directories = (
                self.assets_dir,
                self.data_dir,
                self.logs_dir,
                self.projects_dir,
                self.templates_dir,
            )
        else:
            directories = (self.data_dir, self.logs_dir)
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
