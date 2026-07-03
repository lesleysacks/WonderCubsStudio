"""Tests for Workspace Context Engine business logic."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.database.schema import initialize_database
from src.database.workspace_repository import WorkspaceRepository
from src.models.workspace import Workspace
from src.services.workspace_service import WorkspaceService, WorkspaceValidationError


def test_workspace_crud_flow(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    workspace = _make_workspace(project_name=" Colors ")

    created = service.create_workspace(workspace)
    updated = service.update_workspace(created.uuid, replace(created, topic="Warm and cool colors"))

    assert created.project_name == "Colors"
    assert service.workspace_exists(created.uuid) is True
    assert updated.topic == "Warm and cool colors"
    assert service.load_workspace(created.uuid) == updated
    assert service.delete_workspace(created.uuid) is True
    assert service.workspace_exists(created.uuid) is False


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("project_name", "   ", "Project Name is required"),
        ("lesson", "", "Lesson is required"),
        ("language", "", "Language is required"),
        ("aspect_ratio", "2:1", "Aspect Ratio is invalid"),
        ("resolution", "HD", "Resolution is invalid"),
        ("duration", 0, "Duration must be positive"),
    ),
)
def test_workspace_validation_rules(tmp_path: Path, field: str, value: object, message: str) -> None:
    service = _make_service(tmp_path)
    workspace = replace(_make_workspace(), **{field: value})

    with pytest.raises(WorkspaceValidationError, match=message):
        service.create_workspace(workspace)


def test_save_workspace_creates_then_updates(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    workspace = _make_workspace()

    created = service.save_workspace(workspace)
    updated = service.save_workspace(replace(created, status="In Progress"))

    assert created.uuid == updated.uuid
    assert updated.status == "In Progress"
    assert len(service.list_workspaces()) == 1


def test_export_context_returns_agent_ready_json(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    workspace = service.create_workspace(_make_workspace())

    payload = service.export_context(workspace.uuid)

    assert payload["workspace"]["uuid"] == workspace.uuid
    assert payload["workspace"]["project_name"] == "Colors"
    assert payload["production"]["resolution"] == "1920x1080"
    assert payload["production"]["duration"] == 60
    assert payload["agents"]["story_agent"]["input"] == "workspace_context"
    assert payload["agents"]["voice_agent"]["input"] == "workspace_context"
    assert payload["agents"]["image_agent"]["input"] == "workspace_context"
    assert payload["agents"]["thumbnail_agent"]["input"] == "workspace_context"
    assert payload["agents"]["seo_agent"]["input"] == "workspace_context"


def test_switch_workspace_changes_active_context(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    colors = service.create_workspace(_make_workspace(uuid="colors-uuid", project_name="Colors"))
    shapes = service.create_workspace(_make_workspace(uuid="shapes-uuid", project_name="Shapes", lesson="Shapes"))

    switched = service.switch_workspace(colors.uuid)

    assert switched == colors
    assert service.get_active_workspace() == colors
    assert service.export_context()["workspace"]["project_name"] == "Colors"
    assert shapes.project_name == "Shapes"


def _make_service(tmp_path: Path) -> WorkspaceService:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)
    return WorkspaceService(WorkspaceRepository(database_file))


def _make_workspace(
    uuid: str = "workspace-uuid",
    project_name: str = "Colors",
    lesson: str = "Colors",
    language: str = "English",
    aspect_ratio: str = "16:9",
    resolution: str = "1920x1080",
    duration: int = 60,
) -> Workspace:
    return Workspace(
        uuid=uuid,
        project_name=project_name,
        lesson=lesson,
        topic="Primary colors",
        language=language,
        target_platform="YouTube",
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        duration=duration,
        style="Bright preschool animation",
        current_scene="Scene 1",
        status="Draft",
        created_at="2026-07-03 09:00:00",
        updated_at="2026-07-03 09:00:00",
    )
