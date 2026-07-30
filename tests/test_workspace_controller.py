"""Smoke tests for Workspace Context controller actions."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from src.controllers.workspace_controller import WorkspaceController
from src.models.workspace import Workspace


def test_workspace_loads_correctly() -> None:
    service = FakeWorkspaceService([_make_workspace()])
    controller = WorkspaceController(service)  # type: ignore[arg-type]

    workspaces = controller.load_workspaces()

    assert [workspace.project_name for workspace in workspaces] == ["Colors"]


def test_save_button_flow_calls_workspace_service() -> None:
    service = FakeWorkspaceService()
    controller = WorkspaceController(service)  # type: ignore[arg-type]

    workspace = _make_workspace()
    saved = controller.on_save_workspace(workspace)
    updated = controller.on_save_workspace(replace(saved, status="In Progress"))

    assert service.saved == [workspace.uuid, workspace.uuid]
    assert updated.status == "In Progress"


def test_failed_workspace_save_skips_project_lifecycle_sync() -> None:
    workspace = _make_workspace()
    lifecycle_updates: list[tuple[str, str]] = []
    project_updated_events: list[dict[str, str]] = []

    class FailingWorkspaceService(FakeWorkspaceService):
        def save_workspace(self, workspace: Workspace) -> Workspace:
            raise RuntimeError("workspace save failed")

    def save_project_status(project_name: str, status: str) -> None:
        lifecycle_updates.append((project_name, status))
        project_updated_events.append(
            {"project_name": project_name, "status": status}
        )

    controller = WorkspaceController(
        FailingWorkspaceService(),
        project_status_saver=save_project_status,
    )  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="workspace save failed"):
        controller.on_save_workspace(workspace)

    assert lifecycle_updates == []
    assert project_updated_events == []


def test_successful_workspace_save_precedes_sync_and_uses_saved_values() -> None:
    original = _make_workspace()
    saved_workspace = replace(
        original,
        project_name="Saved Project Name",
        status="Review",
    )
    calls: list[str] = []
    synchronized: list[tuple[str, str]] = []

    class RecordingWorkspaceService(FakeWorkspaceService):
        def save_workspace(self, workspace: Workspace) -> Workspace:
            calls.append("workspace")
            return saved_workspace

    def save_project_status(project_name: str, status: str) -> None:
        calls.append("project")
        synchronized.append((project_name, status))

    controller = WorkspaceController(
        RecordingWorkspaceService(),
        project_status_saver=save_project_status,
    )  # type: ignore[arg-type]

    result = controller.on_save_workspace(original)

    assert calls == ["workspace", "project"]
    assert synchronized == [("Saved Project Name", "Review")]
    assert result is saved_workspace


def test_switch_workspace_flow_calls_service() -> None:
    service = FakeWorkspaceService([_make_workspace()])
    controller = WorkspaceController(service)  # type: ignore[arg-type]

    switched = controller.on_switch_workspace("workspace-uuid")

    assert switched.project_name == "Colors"
    assert service.switched == ["workspace-uuid"]


def test_context_changed_validates_draft() -> None:
    service = FakeWorkspaceService([_make_workspace()])
    controller = WorkspaceController(service)  # type: ignore[arg-type]

    assert controller.on_context_changed(_make_workspace()) is True

    assert service.validated == ["workspace-uuid"]


def test_export_context_button_flow_calls_service() -> None:
    service = FakeWorkspaceService([_make_workspace()])
    controller = WorkspaceController(service)  # type: ignore[arg-type]

    payload = controller.on_export_context("workspace-uuid")

    assert payload["workspace"]["project_name"] == "Colors"
    assert service.exported == ["workspace-uuid"]


def test_delete_and_close_workspace_flow() -> None:
    service = FakeWorkspaceService([_make_workspace()])
    controller = WorkspaceController(service)  # type: ignore[arg-type]

    assert controller.on_delete_workspace("workspace-uuid") is True
    assert controller.on_close_workspace() is None

    assert service.deleted == ["workspace-uuid"]


class FakeWorkspaceService:
    """Small service fake for Workspace UI action smoke tests."""

    def __init__(self, workspaces: list[Workspace] | None = None) -> None:
        self._workspaces = {workspace.uuid: workspace for workspace in workspaces or []}
        self.saved: list[str] = []
        self.switched: list[str] = []
        self.validated: list[str] = []
        self.exported: list[str] = []
        self.deleted: list[str] = []
        self.active_uuid: str | None = None

    def save_workspace(self, workspace: Workspace) -> Workspace:
        self.saved.append(workspace.uuid)
        self._workspaces[workspace.uuid] = workspace
        return workspace

    def load_workspace(self, workspace_uuid: str) -> Workspace:
        return self._workspaces[workspace_uuid]

    def switch_workspace(self, workspace_uuid: str) -> Workspace:
        self.switched.append(workspace_uuid)
        self.active_uuid = workspace_uuid
        return self._workspaces[workspace_uuid]

    def validate_workspace(self, workspace: Workspace) -> bool:
        self.validated.append(workspace.uuid)
        return True

    def delete_workspace(self, workspace_uuid: str) -> bool:
        self.deleted.append(workspace_uuid)
        del self._workspaces[workspace_uuid]
        return True

    def export_context(self, workspace_uuid: str | None = None) -> dict[str, Any]:
        self.exported.append(workspace_uuid or "")
        workspace = self._workspaces[workspace_uuid or self.active_uuid or ""]
        return {"workspace": {"uuid": workspace.uuid, "project_name": workspace.project_name}}

    def list_workspaces(self) -> list[Workspace]:
        return sorted(self._workspaces.values(), key=lambda workspace: workspace.project_name)

    def get_active_workspace(self) -> Workspace | None:
        if self.active_uuid is None:
            return None
        return self._workspaces[self.active_uuid]


def _make_workspace() -> Workspace:
    return Workspace(
        uuid="workspace-uuid",
        project_name="Colors",
        lesson="Colors",
        topic="Primary colors",
        language="English",
        target_platform="YouTube",
        resolution="1920x1080",
        aspect_ratio="16:9",
        duration=60,
        style="Bright preschool animation",
        current_scene="Scene 1",
        status="Draft",
        created_at="2026-07-03 09:00:00",
        updated_at="2026-07-03 09:00:00",
    )
