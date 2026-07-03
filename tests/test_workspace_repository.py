"""Tests for workspace persistence."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

from src.database.schema import initialize_database
from src.database.workspace_repository import WorkspaceRepository
from src.models.workspace import Workspace


def test_initialize_database_creates_workspaces_table_without_affecting_existing_tables(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)

    with sqlite3.connect(database_file) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "Workspaces" in tables
    assert "Characters" in tables
    assert "Projects" in tables
    assert "Goals" in tables


def test_workspace_repository_create_get_all_exists_update_and_delete(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)
    repository = WorkspaceRepository(database_file)

    colors = _make_workspace(uuid="colors-uuid", project_name="Colors", lesson="Colors")
    shapes = _make_workspace(uuid="shapes-uuid", project_name="Shapes", lesson="Shapes")

    repository.create(colors)
    repository.create(shapes)

    assert repository.exists(colors.uuid) is True
    assert repository.get_by_id(colors.uuid) == colors
    assert [workspace.project_name for workspace in repository.get_all()] == ["Colors", "Shapes"]

    updated_colors = replace(colors, current_scene="Scene 2", updated_at="2026-07-03 10:00:00")
    assert repository.update(updated_colors) is True
    assert repository.get_by_id(colors.uuid) == updated_colors

    assert repository.delete(colors.uuid) is True
    assert repository.exists(colors.uuid) is False
    assert repository.get_by_id(colors.uuid) is None
    assert repository.delete(colors.uuid) is False


def test_workspace_repository_raises_sqlite_errors(tmp_path: Path) -> None:
    database_file = tmp_path / "missing-schema.db"
    repository = WorkspaceRepository(database_file)

    with pytest.raises(sqlite3.Error):
        repository.create(_make_workspace())


def _make_workspace(
    uuid: str = "workspace-uuid",
    project_name: str = "Colors",
    lesson: str = "Colors",
) -> Workspace:
    return Workspace(
        uuid=uuid,
        project_name=project_name,
        lesson=lesson,
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
