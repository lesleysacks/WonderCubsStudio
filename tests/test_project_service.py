"""Tests for project creation."""
from __future__ import annotations

from pathlib import Path
import sqlite3

from src.database.schema import initialize_database
from src.database.project_repository import ProjectRepository
from src.services.project_service import ProjectService


def test_create_project_builds_folder_tree(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    initialize_database(database_file)

    service = ProjectService(ProjectRepository(database_file), projects_dir)
    project = service.create_project("001", "Leo Learns Colors", "Colors")

    project_folder = projects_dir / "001_Leo_Learns_Colors"
    assert project.title == "Leo Learns Colors"
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
