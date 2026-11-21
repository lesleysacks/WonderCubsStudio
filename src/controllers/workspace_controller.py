"""Controller for Workspace Context Engine actions."""
from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import Any

from src.models.project import ProjectStatus
from src.models.workspace import Workspace
from src.services.export_service import write_text_file
from src.services.workspace_service import WorkspaceService
from src.utils.logger import get_logger


class WorkspaceController:
    """Coordinate Workspace UI actions with WorkspaceService."""

    def __init__(
        self,
        service: WorkspaceService,
        project_status_saver: Callable[[str, str], object] | None = None,
        project_link_saver: Callable[[int, str], object] | None = None,
    ) -> None:
        """Create the controller.

        ``project_link_saver(project_id, status)`` keeps a linked project's
        lifecycle in step with its workspace. ``project_status_saver(name,
        status)`` is a legacy hook kept for compatibility; the application does
        not wire it, because names are not unique (audit finding D-01).
        """
        self._service = service
        self._project_status_saver = project_status_saver
        self._project_link_saver = project_link_saver
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
        linked = workspace.project_id is not None and self._project_link_saver is not None
        if linked:
            # Reject an invalid lifecycle value before anything is written, so a
            # linked workspace and its project cannot drift apart.
            ProjectStatus.parse(workspace.status)
        saved_workspace = self._service.save_workspace(workspace)
        if linked and saved_workspace.project_id is not None:
            self._project_link_saver(saved_workspace.project_id, saved_workspace.status)
        elif self._project_status_saver is not None:
            self._project_status_saver(
                saved_workspace.project_name,
                saved_workspace.status,
            )
        return saved_workspace

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

    def on_export_context_to_file(self, workspace_uuid: str, file_path: str | Path) -> Path:
        """Write the workspace context JSON to ``file_path``."""
        payload = self._service.export_context(workspace_uuid)
        return write_text_file(file_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    def load_workspaces(self) -> list[Workspace]:
        """Return all workspaces for initial workspace loading."""
        return self._service.list_workspaces()

    def get_active_workspace(self) -> Workspace | None:
        """Return the active workspace for display."""
        return self._service.get_active_workspace()
