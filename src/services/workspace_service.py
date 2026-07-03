"""Workspace Context Engine business logic."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import re
from typing import Any

from src.database.workspace_repository import WorkspaceRepository
from src.models.workspace import Workspace
from src.utils.logger import get_logger


class WorkspaceValidationError(ValueError):
    """Raised when workspace context fails business validation."""


class WorkspaceNotFoundError(LookupError):
    """Raised when a workspace record cannot be found."""


class WorkspaceService:
    """Validate, switch, and export the active production workspace."""

    VALID_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3"}
    RESOLUTION_PATTERN = re.compile(r"^(?P<width>\d{3,5})x(?P<height>\d{3,5})$")

    def __init__(self, repository: WorkspaceRepository) -> None:
        self._repository = repository
        self._current_workspace_uuid: str | None = None
        self._logger = get_logger(__name__)

    def create_workspace(self, workspace: Workspace) -> Workspace:
        """Validate and save a new workspace."""
        clean_workspace = self._prepare_workspace(workspace)
        self.validate_workspace(clean_workspace)
        created = self._repository.create(clean_workspace)
        self._current_workspace_uuid = created.uuid
        self._logger.info("Workspace created and activated: %s", created.uuid)
        return created

    def load_workspace(self, workspace_uuid: str | None = None) -> Workspace:
        """Load a workspace by UUID, or the active workspace when omitted."""
        target_uuid = workspace_uuid or self._current_workspace_uuid
        if target_uuid is None:
            raise WorkspaceNotFoundError("No active workspace.")
        workspace = self._repository.get_by_id(target_uuid)
        if workspace is None:
            raise WorkspaceNotFoundError(f"Workspace not found: {target_uuid}")
        return workspace

    def save_workspace(self, workspace: Workspace) -> Workspace:
        """Create or update a workspace after validation."""
        if self._repository.exists(workspace.uuid):
            return self.update_workspace(workspace.uuid, workspace)
        return self.create_workspace(workspace)

    def update_workspace(self, workspace_uuid: str, workspace: Workspace) -> Workspace:
        """Validate and update an existing workspace."""
        if workspace.uuid != workspace_uuid:
            self._log_validation_failure("UUID cannot be modified.")
            raise WorkspaceValidationError("UUID cannot be modified.")

        existing_workspace = self.load_workspace(workspace_uuid)
        clean_workspace = self._prepare_workspace(
            replace(
                workspace,
                created_at=existing_workspace.created_at,
                updated_at=self._current_timestamp(),
            )
        )
        self.validate_workspace(clean_workspace)
        if not self._repository.update(clean_workspace):
            raise WorkspaceNotFoundError(f"Workspace not found: {workspace_uuid}")

        self._current_workspace_uuid = clean_workspace.uuid
        self._logger.info("Workspace updated and activated: %s", workspace_uuid)
        return clean_workspace

    def delete_workspace(self, workspace_uuid: str) -> bool:
        """Delete an existing workspace."""
        deleted = self._repository.delete(workspace_uuid)
        if not deleted:
            raise WorkspaceNotFoundError(f"Workspace not found: {workspace_uuid}")
        if self._current_workspace_uuid == workspace_uuid:
            self._current_workspace_uuid = None
        self._logger.info("Workspace deleted: %s", workspace_uuid)
        return deleted

    def switch_workspace(self, workspace_uuid: str) -> Workspace:
        """Make a persisted workspace the active production context."""
        workspace = self.load_workspace(workspace_uuid)
        self._current_workspace_uuid = workspace.uuid
        self._logger.info("Workspace switched: %s", workspace.uuid)
        return workspace

    def validate_workspace(self, workspace: Workspace) -> bool:
        """Validate workspace business rules."""
        if not workspace.project_name:
            self._log_validation_failure("Project Name is required.")
            raise WorkspaceValidationError("Project Name is required.")
        if not workspace.lesson:
            self._log_validation_failure("Lesson is required.")
            raise WorkspaceValidationError("Lesson is required.")
        if not workspace.language:
            self._log_validation_failure("Language is required.")
            raise WorkspaceValidationError("Language is required.")
        if workspace.aspect_ratio not in self.VALID_ASPECT_RATIOS:
            self._log_validation_failure(f"Aspect Ratio is invalid: {workspace.aspect_ratio}")
            raise WorkspaceValidationError("Aspect Ratio is invalid.")
        if not self._is_valid_resolution(workspace.resolution):
            self._log_validation_failure(f"Resolution is invalid: {workspace.resolution}")
            raise WorkspaceValidationError("Resolution is invalid.")
        if workspace.duration <= 0:
            self._log_validation_failure("Duration must be positive.")
            raise WorkspaceValidationError("Duration must be positive.")
        return True

    def export_context(self, workspace_uuid: str | None = None) -> dict[str, Any]:
        """Return a structured JSON-ready workspace context object."""
        workspace = self.load_workspace(workspace_uuid)
        payload: dict[str, Any] = {
            "workspace": {
                "uuid": workspace.uuid,
                "project_name": workspace.project_name,
                "lesson": workspace.lesson,
                "topic": workspace.topic,
                "language": workspace.language,
                "target_platform": workspace.target_platform,
                "status": workspace.status,
            },
            "production": {
                "resolution": workspace.resolution,
                "aspect_ratio": workspace.aspect_ratio,
                "duration": workspace.duration,
                "style": workspace.style,
                "current_scene": workspace.current_scene,
            },
            "agents": {
                "story_agent": {"input": "workspace_context"},
                "voice_agent": {"input": "workspace_context"},
                "image_agent": {"input": "workspace_context"},
                "thumbnail_agent": {"input": "workspace_context"},
                "seo_agent": {"input": "workspace_context"},
            },
            "metadata": {
                "created_at": workspace.created_at,
                "updated_at": workspace.updated_at,
            },
        }
        self._logger.info("Workspace context exported: %s", workspace.uuid)
        return payload

    def list_workspaces(self) -> list[Workspace]:
        """Return all persisted workspaces."""
        return self._repository.get_all()

    def workspace_exists(self, workspace_uuid: str) -> bool:
        """Return True when a workspace exists."""
        return self._repository.exists(workspace_uuid)

    def get_active_workspace(self) -> Workspace | None:
        """Return the active workspace, if one has been selected."""
        if self._current_workspace_uuid is None:
            return None
        return self.load_workspace(self._current_workspace_uuid)

    def _prepare_workspace(self, workspace: Workspace) -> Workspace:
        return replace(
            workspace,
            project_name=workspace.project_name.strip(),
            lesson=workspace.lesson.strip(),
            topic=workspace.topic.strip(),
            language=workspace.language.strip(),
            target_platform=workspace.target_platform.strip(),
            resolution=workspace.resolution.strip().lower(),
            aspect_ratio=workspace.aspect_ratio.strip(),
            style=workspace.style.strip(),
            current_scene=workspace.current_scene.strip(),
            status=workspace.status.strip() or "Draft",
        )

    def _is_valid_resolution(self, resolution: str) -> bool:
        match = self.RESOLUTION_PATTERN.match(resolution)
        if match is None:
            return False
        width = int(match.group("width"))
        height = int(match.group("height"))
        return width > 0 and height > 0

    def _log_validation_failure(self, message: str) -> None:
        self._logger.warning("Workspace validation failure: %s", message)

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
