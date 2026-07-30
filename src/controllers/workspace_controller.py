"""Controller for Workspace Context Engine actions."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.models.workspace import Workspace
from src.services.workspace_service import WorkspaceService
from src.utils.logger import get_logger


class WorkspaceController:
    """Coordinate Workspace UI actions with WorkspaceService."""

    def __init__(
        self,
        service: WorkspaceService,
        project_status_saver: Callable[[str, str], object] | None = None,
    ) -> None:
        self._service = service
        self._project_status_saver = project_status_saver
        self._logger = get_logger(__name__)

    def on_new_workspace(self) -> Workspace:
        """Return a blank workspace draft for the UI."""
        self._logger.info("New workspace draft opened")
        return Workspace()

    def on_open_workspace(self, workspace_uuid: str) -> Workspace:
        """Load a workspace through the service."""
        return self._service.load_workspace(workspace_uuid)

    def on_save_workspace(self, workspace: Workspace) -> Workspace:
        """Create or update a workspace through the service."""
        if self._project_status_saver is not None:
            self._project_status_saver(workspace.project_name, workspace.status)
        return self._service.save_workspace(workspace)

    def on_close_workspace(self) -> Workspace | None:
        """Close the active workspace for UI purposes."""
        self._logger.info("Workspace closed")
        return None

    def on_switch_workspace(self, workspace_uuid: str) -> Workspace:
        """Switch the active workspace through the service."""
        return self._service.switch_workspace(workspace_uuid)

    def on_context_changed(self, workspace: Workspace) -> bool:
        """Validate a changed workspace draft without persistence."""
        return self._service.validate_workspace(workspace)

    def on_delete_workspace(self, workspace_uuid: str) -> bool:
        """Delete a workspace through the service."""
        return self._service.delete_workspace(workspace_uuid)

    def on_export_context(self, workspace_uuid: str | None = None) -> dict[str, Any]:
        """Export workspace context through the service."""
        return self._service.export_context(workspace_uuid)

    def load_workspaces(self) -> list[Workspace]:
        """Return all workspaces for initial workspace loading."""
        return self._service.list_workspaces()

    def get_active_workspace(self) -> Workspace | None:
        """Return the active workspace for display."""
        return self._service.get_active_workspace()
