"""Settings loading and saving."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path

from src.models.settings import AppSettings
from src.utils.logger import get_logger


class SettingsService:
    """Manage JSON-backed application settings."""

    def __init__(self, config_file: Path, projects_dir: Path) -> None:
        self._config_file = config_file
        self._logger = get_logger(__name__)
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
        """Load settings from disk.

        A file that cannot be parsed is kept as ``config.json.corrupt-<time>``
        and defaults are used, so one bad edit cannot block the application.
        Individual missing or invalid values fall back to their defaults.
        """
        self.ensure_config()
        defaults = self._default_settings
        try:
            with self._config_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("settings file does not contain a JSON object")
        except (ValueError, UnicodeDecodeError) as error:
            self._quarantine(error)
            return defaults
        return AppSettings(
            default_project_folder=self._project_folder(data.get("default_project_folder")),
            default_resolution=str(data.get("default_resolution", defaults.default_resolution)),
            default_fps=self._int(data.get("default_fps"), defaults.default_fps),
            author_name=str(data.get("author_name", defaults.author_name)),
            channel_name=str(data.get("channel_name", defaults.channel_name)),
        )

    def save(self, settings: AppSettings) -> None:
        """Save settings to disk atomically (a crash never leaves half a file)."""
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._config_file.with_name(self._config_file.name + ".tmp")
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(settings.to_dict(), file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, self._config_file)

    def get_projects_dir(self) -> Path:
        """The folder new projects are created in, from the saved setting."""
        return Path(self.load().default_project_folder)

    def _project_folder(self, value: object) -> str:
        text = str(value).strip() if value is not None else ""
        if not text:
            return self._default_settings.default_project_folder
        folder = Path(text).expanduser()
        if not folder.is_absolute():
            # Relative values (the pre-M0.5 default was "projects") are
            # relative to the folder holding the settings file.
            folder = self._config_file.parent / folder
        return str(folder)

    @staticmethod
    def _int(value: object, default: int) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default

    def _quarantine(self, error: Exception) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        kept = self._config_file.with_name(f"{self._config_file.name}.corrupt-{stamp}")
        try:
            os.replace(self._config_file, kept)
            self._logger.warning("Unreadable settings kept as %s; using defaults (%s)", kept, error)
        except OSError:
            self._logger.warning("Unreadable settings file %s; using defaults (%s)", self._config_file, error)
