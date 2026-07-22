"""Tests for project creation."""
from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from src.database.schema import initialize_database
from src.database.project_repository import ProjectRepository
from src.controllers.main_controller import MainController
from src.services.project_service import ProjectService
from src.services.settings_service import SettingsService
from src.utils.app_paths import AppPaths


def test_create_project_builds_folder_tree(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    initialize_database(database_file)

    service = ProjectService(ProjectRepository(database_file), projects_dir)
    project = service.create_project("Leo Learns Colors", "Colors")

    project_folder = projects_dir / "001_Leo_Learns_Colors"
    assert project.title == "Leo Learns Colors"
    assert project.video_number == "001"
    assert project.status == "Draft"
    assert project_folder.exists()
    assert (project_folder / "Story" / "story.txt").exists()
    assert (project_folder / "Voice" / "voice_script.txt").exists()
    assert (project_folder / "Prompts" / "scene_prompts.txt").exists()
    assert (project_folder / "Thumbnail" / "thumbnail_prompt.txt").exists()
    assert (project_folder / "SEO" / "seo.txt").exists()
    assert (project_folder / "README.md").exists()

    with sqlite3.connect(database_file) as connection:
        count = connection.execute("SELECT COUNT(*) FROM Projects").fetchone()[0]
    assert count == 1


def test_project_number_is_derived_from_existing_database_projects(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    initialize_database(database_file)
    service = ProjectService(ProjectRepository(database_file), projects_dir)

    first = service.create_project("First Lesson", "Colors")
    second = service.create_project("Second Lesson", "Shapes")

    assert first.video_number == "001"
    assert second.video_number == "002"
    assert service.get_next_project_number() == "003"


def test_folder_preview_updates_with_title_and_next_number(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    initialize_database(database_file)
    service = ProjectService(ProjectRepository(database_file), projects_dir)

    assert service.get_folder_preview("Leo Learns Colors!") == str(projects_dir / "001_Leo_Learns_Colors")
    service.create_project("Leo Learns Colors", "Colors")
    assert service.get_folder_preview("Mia Learns Shapes") == str(projects_dir / "002_Mia_Learns_Shapes")


def test_project_status_is_validated_persisted_and_written_to_readme(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    initialize_database(database_file)
    service = ProjectService(ProjectRepository(database_file), projects_dir)

    project = service.create_project("Leo Reviews Colors", "Colors", "Review")

    assert project.status == "Review"
    assert "## Status\n\nReview" in (Path(project.folder_path) / "README.md").read_text(encoding="utf-8")
    assert service.list_projects()[0].status == "Review"
    with pytest.raises(ValueError, match="status"):
        service.create_project("Invalid Status", "Colors", "Complete")


def test_project_creation_activates_its_workspace(tmp_path: Path) -> None:
    paths = AppPaths(tmp_path)
    paths.ensure_directories()
    initialize_database(paths.database_file)
    controller = MainController(paths, SettingsService(paths.config_file, paths.projects_dir))

    project = controller.create_project("Leo Learns Colors", "Colors", "Ready to Publish")

    workspace = controller.get_workspace_controller().get_active_workspace()
    assert workspace is not None
    assert workspace.project_name == project.title
    assert workspace.lesson == project.lesson
    assert workspace.status == project.status
