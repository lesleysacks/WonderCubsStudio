"""Tests for dashboard data loading."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from src.database.connection import create_connection
from src.database.dashboard_repository import DashboardRepository
from src.database.schema import initialize_database
from src.models.project import Project
from src.services.dashboard_service import DashboardService


def test_dashboard_service_returns_zero_values_without_data(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)

    service = DashboardService(DashboardRepository(database_file))
    dashboard = service.get_dashboard_data()

    assert dashboard.statistics.total_projects == 0
    assert dashboard.statistics.published_projects == 0
    assert dashboard.statistics.projects_in_progress == 0
    assert dashboard.statistics.draft_projects == 0
    assert dashboard.statistics.videos_uploaded == 0
    assert dashboard.statistics.completed_projects == 0
    assert dashboard.latest_project is None
    assert dashboard.todays_goal is None


def test_dashboard_service_loads_statistics_latest_project_and_goal(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)
    _insert_project(database_file, "001", "Leo Learns Colors", "Colors", "Draft", "2026-06-01 08:00:00")
    _insert_project(database_file, "002", "Leo Learns Shapes", "Shapes", "In Progress", "2026-06-02 08:00:00")
    _insert_project(database_file, "003", "Leo Learns Numbers", "Numbers", "Published", "2026-06-03 08:00:00")
    _insert_project(database_file, "004", "Leo Shares Kindness", "Kindness", "Uploaded", "2026-06-04 08:00:00")
    _insert_goal(database_file, "Finish Video 004")

    service = DashboardService(DashboardRepository(database_file))
    dashboard = service.get_dashboard_data()

    assert dashboard.statistics.total_projects == 4
    assert dashboard.statistics.published_projects == 1
    assert dashboard.statistics.projects_in_progress == 1
    assert dashboard.statistics.draft_projects == 1
    assert dashboard.statistics.videos_uploaded == 1
    assert dashboard.statistics.completed_projects == 2
    assert isinstance(dashboard.latest_project, Project)
    assert dashboard.latest_project.video_number == "004"
    assert dashboard.todays_goal is not None
    assert dashboard.todays_goal.description == "Finish Video 004"
    assert dashboard.todays_goal.is_completed is False


def _insert_project(
    database_file: Path,
    video_number: str,
    title: str,
    lesson: str,
    status: str,
    created_at: str,
) -> None:
    with create_connection(database_file) as connection:
        connection.execute(
            """
            INSERT INTO Projects
                (video_number, title, lesson, status, created_at, folder_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (video_number, title, lesson, status, created_at, f"projects/{video_number}"),
        )
        connection.commit()


def _insert_goal(database_file: Path, description: str) -> None:
    with create_connection(database_file) as connection:
        connection.execute(
            """
            INSERT INTO Goals (goal_date, description, is_completed)
            VALUES (?, ?, ?)
            """,
            (date.today().isoformat(), description, 0),
        )
        connection.commit()
