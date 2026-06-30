"""Centralized filesystem paths for the application."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    """Filesystem paths used by WonderCubs Studio."""

    base_path: Path

    @property
    def assets_dir(self) -> Path:
        return self.base_path / "assets"

    @property
    def data_dir(self) -> Path:
        return self.base_path / "data"

    @property
    def logs_dir(self) -> Path:
        return self.base_path / "logs"

    @property
    def projects_dir(self) -> Path:
        return self.base_path / "projects"

    @property
    def templates_dir(self) -> Path:
        return self.base_path / "templates"

    @property
    def config_file(self) -> Path:
        return self.base_path / "config.json"

    @property
    def database_file(self) -> Path:
        return self.base_path / "database.db"

    def ensure_directories(self) -> None:
        """Create required application directories if they are missing."""
        for directory in (
            self.assets_dir,
            self.data_dir,
            self.logs_dir,
            self.projects_dir,
            self.templates_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
