"""Main application controller."""
from __future__ import annotations

from src.database.dashboard_repository import DashboardRepository
from src.database.character_repository import CharacterRepository
from src.database.project_repository import ProjectRepository
from src.database.workspace_repository import WorkspaceRepository
from src.database.prompt_repository import PromptRepository
from src.controllers.character_controller import CharacterController
from src.controllers.workspace_controller import WorkspaceController
from src.controllers.prompt_controller import PromptController
from src.models.dashboard import DashboardData
from src.models.project import Project
from src.models.settings import AppSettings
from src.models.workspace import Workspace
from src.services.character_service import CharacterService
from src.services.dashboard_service import DashboardService
from src.services.explorer_service import ExplorerService
from src.services.project_service import ProjectService
from src.services.settings_service import SettingsService
from src.services.workspace_service import WorkspaceService
from src.services.prompt_service import PromptService
from src.utils.app_paths import AppPaths
from src.utils.logger import get_logger
from src.utils.event_bus import EventBus, EventCallback


class MainController:
    """Bridge UI actions to application services."""

    def __init__(self, paths: AppPaths, settings_service: SettingsService) -> None:
        self._logger = get_logger(__name__)
        self._settings_service = settings_service
        repository = ProjectRepository(paths.database_file)
        dashboard_repository = DashboardRepository(paths.database_file)
        character_repository = CharacterRepository(paths.database_file)
        workspace_repository = WorkspaceRepository(paths.database_file)
        prompt_repository = PromptRepository(paths.database_file)
        self._event_bus = EventBus()
        self._project_service = ProjectService(
            repository, paths.projects_dir, self._event_bus
        )
        self._dashboard_service = DashboardService(
            dashboard_repository, self._project_service
        )
        self._character_service = CharacterService(character_repository)
        self._workspace_service = WorkspaceService(workspace_repository)
        self._prompt_service = PromptService(
            prompt_repository, self._workspace_service, self._character_service
        )
        self._character_controller = CharacterController(self._character_service)
        self._workspace_controller = WorkspaceController(
            self._workspace_service, self._project_service.change_status_by_title
        )
        self._prompt_controller = PromptController(self._prompt_service)
        self._explorer_service = ExplorerService()

    def create_project(self, title: str, lesson: str, status: str = ProjectService.DEFAULT_STATUS) -> Project:
        """Create a project from UI input."""
        self._logger.info("Creating project: %s", title)
        project = self._project_service.create_project(title, lesson, status)
        self._workspace_service.create_workspace(
            Workspace(
                project_name=project.title,
                lesson=project.lesson,
                topic=project.title,
                status=project.status,
            )
        )
        return project

    def get_next_project_number(self) -> str:
        """Return the database-generated number for the next project."""
        return self._project_service.get_next_project_number()

    def get_project_folder_preview(self, title: str) -> str:
        """Return a live folder preview for a project title."""
        return self._project_service.get_folder_preview(title)

    def list_projects(self) -> list[Project]:
        """Return all projects for display."""
        return self._project_service.list_projects()

    def change_project_status(self, project_id: int, status: str) -> Project:
        """Persist a project lifecycle change through the service."""
        return self._project_service.change_status(project_id, status)

    def subscribe(self, event_name: str, callback: EventCallback) -> None:
        self._event_bus.subscribe(event_name, callback)

    def unsubscribe(self, event_name: str, callback: EventCallback) -> None:
        self._event_bus.unsubscribe(event_name, callback)

    def open_project_folder(self, project: Project) -> None:
        """Open a project folder in Windows Explorer."""
        self._logger.info("Opening project folder: %s", project.folder_path)
        self._explorer_service.open_folder(project.folder_path)

    def load_dashboard(self) -> DashboardData:
        """Return dashboard data for the home screen."""
        return self._dashboard_service.get_dashboard_data()

    def load_settings(self) -> AppSettings:
        """Load application settings."""
        return self._settings_service.load()

    def save_settings(self, settings: AppSettings) -> None:
        """Save application settings."""
        self._logger.info("Saving settings")
        self._settings_service.save(settings)

    def get_character_controller(self) -> CharacterController:
        """Return the Character Workspace controller."""
        return self._character_controller

    def get_workspace_controller(self) -> WorkspaceController:
        """Return the Workspace Context controller."""
        return self._workspace_controller

    def get_prompt_controller(self) -> PromptController:
        """Return the Prompt Engine controller."""
        return self._prompt_controller
