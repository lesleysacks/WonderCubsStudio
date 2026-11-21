"""UI-level tests: real windows, real widgets, real database (M0.5.5)."""
from __future__ import annotations

import json
from pathlib import Path

from src.models.character import Character
from src.models.prompt import Prompt


def _projects(ui) -> dict[str, str]:
    return {p.video_number: p.status for p in ui.controller.list_projects()}


def _toplevels(ui, cls_name: str):
    return [w for w in ui.app.winfo_children() if type(w).__name__ == cls_name]


def test_every_screen_opens_without_errors(ui) -> None:
    for show in (
        ui.app._show_dashboard,
        ui.app._show_workspace,
        ui.app._show_characters,
        ui.app._show_prompts,
        ui.app._open_settings,
        ui.app._open_project_picker,
        ui.app._show_dashboard,
    ):
        show()
        ui.pump()
    assert ui.errors == []
    assert ui.message_errors() == []


def test_new_project_dialog_creates_project_workspace_and_folder(ui) -> None:
    ui.app._open_new_project_dialog()
    ui.pump()
    dialog = _toplevels(ui, "NewProjectDialog")[0]
    dialog._entries["Video Title"].insert(0, "Café Été")
    dialog._entries["Lesson"].insert(0, "Seasons")
    dialog._update_folder_preview()
    preview = dialog._folder_preview.get()

    dialog._create_project()
    ui.pump()

    project = ui.controller.list_projects()[0]
    assert project.folder_path == preview
    assert Path(project.folder_path).is_dir()
    assert ui.opened_folders == [project.folder_path]
    active = ui.controller.get_workspace_controller().get_active_workspace()
    assert active.project_id == project.id
    assert ui.errors == [] and ui.message_errors() == []


def test_workspace_screen_status_change_updates_only_its_project(ui) -> None:
    first = ui.controller.create_project("Intro", "Hello")
    ui.controller.create_project("Intro", "Goodbye")
    ui.app._show_workspace()
    ui.pump()
    window = ui.content()
    target = next(w for w in window._workspaces if w.project_id == first.id)
    window._select_workspace(target)
    window._option_menus["status"].set("Review")

    window._save_workspace()
    ui.pump()

    assert _projects(ui) == {"001": "Review", "002": "Draft"}
    assert ui.message_errors() == []


def test_goal_can_be_set_and_completed_from_the_dashboard(ui) -> None:
    ui.app._edit_goal("Finish storyboard — 第一話")
    ui.pump()
    assert ui.controller.load_dashboard().todays_goal.description == "Finish storyboard — 第一話"

    ui.app._set_goal_completed(True)
    ui.pump()
    assert ui.controller.load_dashboard().todays_goal.is_completed is True
    assert ui.errors == [] and ui.message_errors() == []


def test_invalid_goal_shows_an_error_and_saves_nothing(ui) -> None:
    ui.app._edit_goal("   ")
    ui.pump()
    assert ui.controller.load_dashboard().todays_goal is None
    assert [m[1] for m in ui.message_errors()] == ["Could not save goal"]


def test_character_export_button_writes_a_file(ui, tmp_path: Path, monkeypatch) -> None:
    character = ui.controller.get_character_controller().on_save_character(Character(name="Zoë", species="Fox"))
    target = tmp_path / "out dir ü" / "zoë.json"
    target.parent.mkdir()
    suggested: list[str] = []
    monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **kw: (suggested.append(kw["initialfile"]), str(target))[1])
    ui.app._show_characters()
    ui.pump()
    window = ui.content()
    window._select_character(character)

    window._export_character()

    assert suggested == ["Zoë.json"]
    assert json.loads(target.read_text(encoding="utf-8"))["identity"]["name"] == "Zoë"
    assert ui.messages[-1][0] == "info" and str(target) in ui.messages[-1][2]


def test_cancelled_export_writes_nothing(ui, tmp_path: Path, monkeypatch) -> None:
    ui.controller.create_project("Leo", "Colors")
    monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **kw: "")
    ui.app._show_workspace()
    ui.pump()

    ui.content()._export_context()

    assert ui.messages == []
    assert not list(tmp_path.glob("*.json"))


def test_workspace_and_prompt_export_buttons_write_files(ui, tmp_path: Path, monkeypatch) -> None:
    ui.controller.create_project("Leo", "Colors")
    prompt = ui.controller.get_prompt_controller().on_save_prompt(
        Prompt(name="Opener", category="Story", template="Project {{PROJECT_NAME}}")
    )
    workspace_file, prompt_file = tmp_path / "context.json", tmp_path / "opener.md"
    targets = iter([str(workspace_file), str(prompt_file)])
    monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **kw: next(targets))

    ui.app._show_workspace()
    ui.pump()
    ui.content()._export_context()
    ui.app._show_prompts()
    ui.pump()
    prompts = ui.content()
    prompts._select(prompt)
    prompts._export_format.set("markdown")
    prompts._export()

    assert json.loads(workspace_file.read_text(encoding="utf-8"))["workspace"]["project_name"] == "Leo"
    assert "Project Leo" in prompt_file.read_text(encoding="utf-8")
    assert ui.message_errors() == []


def test_settings_window_changes_where_the_next_project_goes(ui, tmp_path: Path) -> None:
    custom = tmp_path / "Shared Drive" / "日本 Projects"
    ui.app._open_settings()
    ui.pump()
    settings = _toplevels(ui, "SettingsWindow")[0]
    entry = settings._entries["Default Project Folder"]
    entry.delete(0, "end")
    entry.insert(0, str(custom))

    settings._save()
    ui.pump()
    project = ui.controller.create_project("Leo", "Colors")

    assert Path(project.folder_path).parent == custom
    assert ui.message_errors() == []


def test_dashboard_still_refreshes_after_a_project_change(ui) -> None:
    project = ui.controller.create_project("Leo", "Colors")
    ui.app._show_dashboard()
    ui.pump()

    ui.controller.change_project_status(project.id, "Published")
    ui.pump()

    labels = [w.cget("text") for w in _all_widgets(ui.app) if type(w).__name__ == "CTkLabel"]
    assert any("Leo · Published" in str(text) for text in labels)
    assert ui.errors == []


def _all_widgets(widget):
    for child in widget.winfo_children():
        yield child
        yield from _all_widgets(child)
