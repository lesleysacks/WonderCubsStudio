"""Regression tests for audit findings D-01 and D-02 (title-based linking)."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sqlite3

import pytest

from src.controllers.main_controller import MainController
from src.database.schema import initialize_database
from src.models.workspace import Workspace
from src.services.settings_service import SettingsService
from src.utils.app_paths import AppPaths
from tests.db_fixtures import load_fixture


def _controller(tmp_path: Path, fixture: str | None = None) -> tuple[MainController, AppPaths]:
    paths = AppPaths(tmp_path)
    paths.ensure_directories()
    if fixture:
        load_fixture(fixture, paths.database_file)
    initialize_database(paths.database_file)
    return MainController(paths, SettingsService(paths.config_file, paths.projects_dir)), paths


def _statuses(controller: MainController) -> dict[str, str]:
    return {p.video_number: p.status for p in controller.list_projects()}


def _workspace_for(controller: MainController, project_id: int) -> Workspace:
    matches = [
        w for w in controller.get_workspace_controller().load_workspaces()
        if w.project_id == project_id
    ]
    assert len(matches) == 1
    return matches[0]


def test_d01_duplicate_titles_update_only_the_linked_project(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path)
    first = controller.create_project("Intro", "Hello")
    second = controller.create_project("Intro", "Goodbye")
    workspaces = controller.get_workspace_controller()

    workspaces.on_save_workspace(replace(_workspace_for(controller, first.id), status="Review"))

    assert _statuses(controller) == {"001": "Review", "002": "Draft"}
    workspaces.on_save_workspace(replace(_workspace_for(controller, second.id), status="Published"))
    assert _statuses(controller) == {"001": "Review", "002": "Published"}


def test_d02_renamed_workspace_keeps_its_project_link(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path)
    project = controller.create_project("Alpha", "Letters")
    workspaces = controller.get_workspace_controller()

    renamed = workspaces.on_save_workspace(
        replace(_workspace_for(controller, project.id), project_name="Alpha v2")
    )
    workspaces.on_save_workspace(replace(renamed, status="Ready to Publish"))

    saved = controller.list_projects()[0]
    assert saved.status == "Ready to Publish"
    assert saved.title == "Alpha"  # renaming the workspace never renames the project
    assert _workspace_for(controller, project.id).project_name == "Alpha v2"


def test_link_survives_a_form_draft_that_omits_project_id(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path)
    project = controller.create_project("Alpha", "Letters")
    service_draft = replace(_workspace_for(controller, project.id), project_id=None, style="Bold")

    controller.get_workspace_controller().on_save_workspace(service_draft)

    assert _workspace_for(controller, project.id).style == "Bold"


def test_invalid_status_on_linked_workspace_is_rejected_before_any_write(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path)
    project = controller.create_project("Alpha", "Letters")
    original = _workspace_for(controller, project.id)

    with pytest.raises(ValueError, match="status"):
        controller.get_workspace_controller().on_save_workspace(
            replace(original, status="In Progress", style="Changed")
        )

    assert _workspace_for(controller, project.id) == original
    assert controller.list_projects()[0].status == "Draft"


def test_unlinked_workspace_never_updates_a_project_with_the_same_title(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path)
    controller.create_project("Intro", "Hello")
    workspaces = controller.get_workspace_controller()

    workspaces.on_save_workspace(Workspace(project_name="Intro", lesson="Typed by hand", status="Published"))

    assert _statuses(controller) == {"001": "Draft"}


def test_one_project_cannot_be_linked_to_two_workspaces(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path)
    project = controller.create_project("Alpha", "Letters")

    with pytest.raises(sqlite3.IntegrityError):
        controller.get_workspace_controller().on_save_workspace(
            Workspace(project_name="Alpha copy", lesson="Letters", project_id=project.id)
        )


def test_link_to_a_missing_project_is_rejected(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path)

    with pytest.raises(sqlite3.IntegrityError):
        controller.get_workspace_controller().on_save_workspace(
            Workspace(project_name="Ghost", lesson="None", project_id=999)
        )


def test_migration_links_v0_3_workspaces_including_duplicates_and_renames(tmp_path: Path) -> None:
    controller, paths = _controller(tmp_path, "v0_3_release")
    links = {
        w.uuid: w.project_id for w in controller.get_workspace_controller().load_workspaces()
    }

    assert links == {
        "w-leo": 1, "w-cafe": 2, "w-intro-1": 3, "w-intro-2": 4, "w-alpha": 5, "w-ideas": None,
    }
    connection = sqlite3.connect(paths.database_file)
    details = json.loads(
        connection.execute("SELECT details FROM schema_migrations WHERE version = 2").fetchone()[0]
    )
    connection.close()
    assert details["unlinked_workspaces"] == [
        {"uuid": "w-ideas", "project_name": "Unrelated Ideas", "reason": "no project has this title"}
    ]


def test_migrated_duplicate_title_workspace_updates_only_its_own_project(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path, "v0_3_release")
    workspaces = controller.get_workspace_controller()
    intro_one = workspaces.on_open_workspace("w-intro-1")

    workspaces.on_save_workspace(replace(intro_one, status="Published"))

    statuses = _statuses(controller)
    assert statuses["003"] == "Published"
    assert statuses["004"] == "Draft"


def test_migration_leaves_ambiguous_manual_workspaces_unlinked(tmp_path: Path) -> None:
    controller, _ = _controller(tmp_path, "v0_3_sprint_3_4")
    links = {
        w.uuid: w.project_id for w in controller.get_workspace_controller().load_workspaces()
    }

    assert links == {"w-leo": 1, "w-intro": None, "w-ideas": None}
