"""Settings loading and saving."""
from __future__ import annotations

import json
from pathlib import Path

from src.models.settings import AppSettings


class SettingsService:
    """Manage JSON-backed application settings."""

    def __init__(self, config_file: Path, projects_dir: Path) -> None:
        self._config_file = config_file
        self._default_settings = AppSettings(
            default_project_folder=str(projects_dir),
            default_resolution="1920x1080",
            default_fps=30,
            author_name="WonderCubs Team",
            channel_name="WonderCubs",
        )

    def ensure_config(self) -> None:
        """Create the config file if it does not exist."""
        if not self._config_file.exists():
            self.save(self._default_settings)

    def load(self) -> AppSettings:
        """Load settings from disk."""
        self.ensure_config()
        with self._config_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return AppSettings(
            default_project_folder=str(data.get("default_project_folder", self._default_settings.default_project_folder)),
            default_resolution=str(data.get("default_resolution", self._default_settings.default_resolution)),
            default_fps=int(data.get("default_fps", self._default_settings.default_fps)),
            author_name=str(data.get("author_name", self._default_settings.author_name)),
            channel_name=str(data.get("channel_name", self._default_settings.channel_name)),
        )

    def save(self, settings: AppSettings) -> None:
        """Save settings to disk."""
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with self._config_file.open("w", encoding="utf-8") as file:
            json.dump(settings.to_dict(), file, indent=2)
