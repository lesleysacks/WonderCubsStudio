"""Main application controller."""
from __future__ import annotations

from src.database.project_repository import ProjectRepository
from src.models.project import Project
from src.models.settings import AppSettings
from src.services.explorer_service import ExplorerService
from src.services.project_service import ProjectService
from src.services.settings_service import SettingsService
from src.utils.app_paths import AppPaths
from src.utils.logger import get_logger


class MainController:
    """Bridge UI actions to application services."""

    def __init__(self, paths: AppPaths, settings_service: SettingsService) -> None:
        self._logger = get_logger(__name__)
        self._settings_service = settings_service
        repository = ProjectRepository(paths.database_file)
        self._project_service = ProjectService(repository, paths.projects_dir)
        self._explorer_service = ExplorerService()

    def create_project(self, video_number: str, title: str, lesson: str) -> Project:
        """Create a project from UI input."""
        self._logger.info("Creating project %s - %s", video_number, title)
        return self._project_service.create_project(video_number, title, lesson)

    def list_projects(self) -> list[Project]:
        """Return all projects for display."""
        return self._project_service.list_projects()

    def open_project_folder(self, project: Project) -> None:
        """Open a project folder in Windows Explorer."""
        self._logger.info("Opening project folder: %s", project.folder_path)
        self._explorer_service.open_folder(project.folder_path)

    def load_settings(self) -> AppSettings:
        """Load application settings."""
        return self._settings_service.load()

    def save_settings(self, settings: AppSettings) -> None:
        """Save application settings."""
        self._logger.info("Saving settings")
        self._settings_service.save(settings)
