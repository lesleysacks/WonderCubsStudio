"""Exports write real files (P-01) and Today's Goal can be set (P-02)."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from src.controllers.main_controller import MainController
from src.database.schema import initialize_database
from src.models.character import Character
from src.models.prompt import Prompt
from src.services.export_service import suggested_file_name, write_text_file
from src.services.project_service import ProjectService
from src.services.settings_service import SettingsService
from src.utils.app_paths import AppPaths

FOLDER = "Exports Ünïcødé 日本"


@pytest.fixture
def controller(tmp_path: Path) -> MainController:
    paths = AppPaths(tmp_path)
    paths.ensure_directories()
    initialize_database(paths.database_file)
    return MainController(paths, SettingsService(paths.config_file, paths.projects_dir))


@pytest.fixture
def out(tmp_path: Path) -> Path:
    folder = tmp_path / FOLDER
    folder.mkdir()
    return folder


def test_character_export_writes_the_same_json_payload(controller: MainController, out: Path) -> None:
    characters = controller.get_character_controller()
    leo = characters.on_save_character(Character(name="Zoë", species="Fox", catchphrase="¡Vamos!"))

    written = characters.on_export_character_to_file(leo.uuid, out / "zoë.json")

    assert json.loads(written.read_text(encoding="utf-8")) == characters.on_export_character(leo.uuid)
    assert "¡Vamos!" in written.read_text(encoding="utf-8")  # readable, not \\u-escaped


def test_workspace_export_writes_the_context_payload(controller: MainController, out: Path) -> None:
    controller.create_project("Café Été", "Seasons")
    workspaces = controller.get_workspace_controller()
    workspace = workspaces.get_active_workspace()

    written = workspaces.on_export_context_to_file(workspace.uuid, out / "context.json")

    assert json.loads(written.read_text(encoding="utf-8")) == workspaces.on_export_context(workspace.uuid)


@pytest.mark.parametrize("export_format", ["json", "txt", "markdown"])
def test_prompt_export_writes_each_format(controller: MainController, out: Path, export_format: str) -> None:
    prompts = controller.get_prompt_controller()
    prompt = prompts.on_save_prompt(Prompt(name="Opener", category="Story", template="Hello {{NAME}}"))

    written = prompts.on_export_prompt_to_file(
        prompt.id, export_format, out / f"opener.{export_format}", values={"NAME": "Zoë"}
    )

    expected = prompts.on_export_prompt(prompt.id, export_format, values={"NAME": "Zoë"})
    assert written.read_text(encoding="utf-8").rstrip("\n") == expected.rstrip("\n")


def test_export_replaces_an_existing_file_atomically(tmp_path: Path) -> None:
    target = tmp_path / "file.json"
    target.write_text("old", encoding="utf-8")

    write_text_file(target, "new")

    assert target.read_text(encoding="utf-8") == "new"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["file.json"]


def test_failed_export_keeps_the_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "file.json"
    target.write_text("old", encoding="utf-8")

    with pytest.raises(TypeError):
        write_text_file(target, 123)  # type: ignore[arg-type]
    assert target.read_text(encoding="utf-8") == "old"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["file.json"]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Café Été", "Café_Été.json"),
        ('a/b\\c:d*e?f"g<h>i|j', "a_b_c_d_e_f_g_h_i_j.json"),
        ("CON", "CON_export.json"),
        ("   ", "export.json"),
        ("日本語", "日本語.json"),
    ],
)
def test_suggested_file_names_are_safe_on_every_platform(name: str, expected: str) -> None:
    assert suggested_file_name(name, "json") == expected


def test_todays_goal_can_be_set_edited_and_completed(controller: MainController) -> None:
    assert controller.load_dashboard().todays_goal is None

    controller.set_todays_goal("  Record   voice — 第一話 ")
    goal = controller.load_dashboard().todays_goal
    assert goal is not None
    assert (goal.goal_date, goal.description, goal.is_completed) == (date.today().isoformat(), "Record voice — 第一話", False)

    controller.set_todays_goal_completed(True)
    controller.set_todays_goal("Record voice and mix")
    edited = controller.load_dashboard().todays_goal
    assert edited.id == goal.id  # edited in place, not duplicated
    assert edited.description == "Record voice and mix" and edited.is_completed is True

    controller.set_todays_goal_completed(False)
    assert controller.load_dashboard().todays_goal.is_completed is False


@pytest.mark.parametrize("bad", ["", "   ", "x" * 201])
def test_invalid_goals_are_rejected(controller: MainController, bad: str) -> None:
    with pytest.raises(ValueError):
        controller.set_todays_goal(bad)
    assert controller.load_dashboard().todays_goal is None


def test_completing_without_a_goal_is_reported(controller: MainController) -> None:
    with pytest.raises(LookupError):
        controller.set_todays_goal_completed(True)


def test_dead_code_removed_only_where_unused() -> None:
    # Removed: no caller anywhere (audit C-03/C-04).
    assert not hasattr(ProjectService, "get_dashboard_statistics")
    # Kept: v0.1 to v0.3 databases contain these statuses (see tests/fixtures/db),
    # so the dashboard still counts them.
    assert "In Progress" in (Path(__file__).parent / "fixtures" / "db" / "v0_1.sql").read_text(encoding="utf-8")
