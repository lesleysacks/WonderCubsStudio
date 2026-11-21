"""Regression tests for audit finding D-03 (non-atomic project creation)."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3

import pytest

from src.controllers.main_controller import MainController
from src.database.connection import transaction
from src.database.project_repository import ProjectRepository
from src.database.schema import initialize_database
from src.services.project_service import ProjectService
from src.services.settings_service import SettingsService
from src.services.workspace_service import WorkspaceService, WorkspaceValidationError
from src.utils.app_paths import AppPaths


def _controller(tmp_path: Path) -> tuple[MainController, AppPaths]:
    paths = AppPaths(tmp_path)
    paths.ensure_directories()
    initialize_database(paths.database_file)
    return MainController(paths, SettingsService(paths.config_file, paths.projects_dir)), paths


def _counts(database: Path) -> tuple[int, int]:
    connection = sqlite3.connect(database)
    try:
        projects = connection.execute("SELECT COUNT(*) FROM Projects").fetchone()[0]
        workspaces = connection.execute("SELECT COUNT(*) FROM Workspaces").fetchone()[0]
        return projects, workspaces
    finally:
        connection.close()


def _folder_names(folder: Path) -> list[str]:
    return sorted(entry.name for entry in folder.iterdir())


def test_workspace_failure_rolls_back_project_row_and_folder(tmp_path: Path, monkeypatch) -> None:
    controller, paths = _controller(tmp_path)
    events: list[dict] = []
    controller.subscribe("project_updated", events.append)

    def fail(self, workspace, connection=None):
        raise WorkspaceValidationError("simulated workspace failure")

    monkeypatch.setattr(WorkspaceService, "create_workspace", fail)
    with pytest.raises(WorkspaceValidationError):
        controller.create_project("Leo Learns Colors", "Colors")

    assert _counts(paths.database_file) == (0, 0)
    assert _folder_names(paths.projects_dir) == []
    assert events == []
    assert controller.get_next_project_number() == "001"
    assert controller.get_workspace_controller().get_active_workspace() is None


def test_successful_creation_writes_project_workspace_and_folder_together(tmp_path: Path) -> None:
    controller, paths = _controller(tmp_path)

    project = controller.create_project("Leo Learns Colors", "Colors")

    assert _counts(paths.database_file) == (1, 1)
    assert _folder_names(paths.projects_dir) == ["001_Leo_Learns_Colors"]
    assert (Path(project.folder_path) / "Story" / "story.txt").is_file()
    active = controller.get_workspace_controller().get_active_workspace()
    assert active is not None and active.project_id == project.id


def test_database_insert_failure_leaves_no_folder(tmp_path: Path, monkeypatch) -> None:
    controller, paths = _controller(tmp_path)

    def fail(self, project, connection=None):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(ProjectRepository, "add", fail)
    with pytest.raises(sqlite3.OperationalError):
        controller.create_project("Leo", "Colors")

    assert _counts(paths.database_file) == (0, 0)
    assert _folder_names(paths.projects_dir) == []


def test_commit_failure_after_folder_rename_is_fully_undone(tmp_path: Path, monkeypatch) -> None:
    controller, paths = _controller(tmp_path)

    @contextmanager
    def commit_fails(self):
        with transaction(paths.database_file) as connection:
            yield connection
            connection.rollback()
            raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(ProjectRepository, "transaction", commit_fails)
    with pytest.raises(sqlite3.OperationalError, match="locked"):
        controller.create_project("Leo", "Colors")

    assert _counts(paths.database_file) == (0, 0)
    assert _folder_names(paths.projects_dir) == []


def test_folder_appearing_mid_creation_is_left_untouched(tmp_path: Path) -> None:
    paths = AppPaths(tmp_path)
    paths.ensure_directories()
    initialize_database(paths.database_file)
    service = ProjectService(ProjectRepository(paths.database_file), paths.projects_dir)
    user_folder = paths.projects_dir / "001_Leo"

    def user_creates_folder(_connection, _project) -> None:
        user_folder.mkdir()
        (user_folder / "my notes.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(FileExistsError):
        service.create_project("Leo", "Colors", on_create=user_creates_folder)

    assert service.list_projects() == []
    assert _folder_names(paths.projects_dir) == ["001_Leo"]
    assert (user_folder / "my notes.txt").read_text(encoding="utf-8") == "keep me"


def test_recovery_after_database_loss_skips_numbers_used_by_existing_folders(tmp_path: Path) -> None:
    controller, paths = _controller(tmp_path)
    first = controller.create_project("Z", "Lesson")
    paths.database_file.unlink()
    initialize_database(paths.database_file)
    controller = MainController(paths, SettingsService(paths.config_file, paths.projects_dir))

    assert controller.get_next_project_number() == "002"
    second = controller.create_project("Z", "Lesson")

    assert second.video_number == "002"
    assert Path(first.folder_path).is_dir()  # the earlier folder is never touched
    assert _folder_names(paths.projects_dir) == ["001_Z", "002_Z"]


def test_unrelated_user_folders_are_preserved_on_failure(tmp_path: Path, monkeypatch) -> None:
    controller, paths = _controller(tmp_path)
    keep = paths.projects_dir / "Client Work"
    keep.mkdir()
    (keep / "brief.docx").write_bytes(b"\x00binary")

    def fail(self, workspace, connection=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(WorkspaceService, "create_workspace", fail)
    with pytest.raises(RuntimeError):
        controller.create_project("Leo", "Colors")

    assert _folder_names(paths.projects_dir) == ["Client Work"]
    assert (keep / "brief.docx").read_bytes() == b"\x00binary"
