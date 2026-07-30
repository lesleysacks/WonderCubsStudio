"""Regression tests for project lifecycle and dashboard synchronization."""
from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from src.database.dashboard_repository import DashboardRepository
from src.database.project_repository import ProjectRepository
from src.database.schema import initialize_database
from src.models.project import ProjectStatus
from src.services.dashboard_service import DashboardService
from src.services.project_service import ProjectService
from src.utils.event_bus import EventBus


def _service(
    tmp_path: Path, event_bus: EventBus | None = None
) -> tuple[ProjectService, Path]:
    database = tmp_path / "database.db"
    projects = tmp_path / "projects"
    projects.mkdir()
    initialize_database(database)
    return ProjectService(ProjectRepository(database), projects, event_bus), database


def test_legacy_project_without_status_migrates_safely(tmp_path: Path) -> None:
    database = tmp_path / "legacy.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE Projects (
                id INTEGER PRIMARY KEY, video_number TEXT, title TEXT, lesson TEXT,
                status TEXT, created_at TEXT, folder_path TEXT
            )
            """
        )
        connection.execute(
            "INSERT INTO Projects VALUES (1, '007', 'Legacy', 'Reading', NULL, "
            "'2025-01-01 10:00:00', 'projects/007')"
        )
    initialize_database(database)
    project = ProjectRepository(database).get(1)
    assert project is not None
    assert project.status == ProjectStatus.DRAFT.value
    assert project.updated_at == project.created_at
    initialize_database(database)  # Repeatable upgrade.


def test_lifecycle_updates_timestamps_and_preserves_first_publish_time(
    tmp_path: Path,
) -> None:
    service, _ = _service(tmp_path)
    project = service.create_project("Lifecycle", "Testing")
    for status in (
        "In Production", "Review", "Ready to Publish", "Published"
    ):
        project = service.change_status(int(project.id), status)
        assert project.status == status
    first_published_at = project.published_at
    assert first_published_at
    project = service.change_status(int(project.id), "Published")
    assert project.published_at == first_published_at
    assert service.change_status(int(project.id), "Archived").status == "Archived"


def test_failed_save_emits_no_event_and_dashboard_stays_database_backed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bus = EventBus()
    service, database = _service(tmp_path, bus)
    project = service.create_project("Failure", "Atomicity")
    events: list[dict[str, object]] = []
    bus.subscribe("project_updated", events.append)
    before = DashboardService(DashboardRepository(database), service).get_statistics()

    def fail(*_args: object) -> bool:
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(service._repository, "update_lifecycle", fail)
    with pytest.raises(sqlite3.OperationalError):
        service.change_status(int(project.id), "Published")

    after = DashboardService(DashboardRepository(database), service).get_statistics()
    assert events == []
    assert after == before


def test_dashboard_totals_recent_activity_and_next_number(tmp_path: Path) -> None:
    service, database = _service(tmp_path)
    first = service.create_project("First", "One")
    service.change_status(int(first.id), "In Production")
    second = service.create_project("Second", "Two")
    service.change_status(int(second.id), "Archived")
    third = service.create_project("Third", "Three")
    service.change_status(int(third.id), "Published")

    dashboard = DashboardService(
        DashboardRepository(database), service
    ).get_dashboard_data()
    assert dashboard.statistics.total_projects == 3
    assert dashboard.statistics.in_production_projects == 1
    assert dashboard.statistics.archived_projects == 1
    assert dashboard.statistics.active_production_count == 1
    assert dashboard.next_video_number == "004"
    assert [item.id for item in dashboard.recent_activity] == [
        third.id, second.id, first.id
    ]


def test_event_subscription_is_idempotent_and_refreshes_after_success(
    tmp_path: Path,
) -> None:
    bus = EventBus()
    service, database = _service(tmp_path, bus)
    project = service.create_project("Events", "Refresh")
    dashboard = DashboardService(DashboardRepository(database), service)
    refreshes: list[int] = []

    def refresh(_payload: dict[str, object]) -> None:
        refreshes.append(dashboard.get_statistics().published_projects)

    bus.subscribe("project_updated", refresh)
    bus.subscribe("project_updated", refresh)
    service.change_status(int(project.id), "Published")
    assert refreshes == [1]
    bus.unsubscribe("project_updated", refresh)
    service.change_status(int(project.id), "Archived")
    assert refreshes == [1]


def test_invalid_lifecycle_value_is_rejected(tmp_path: Path) -> None:
    service, _ = _service(tmp_path)
    project = service.create_project("Validation", "Statuses")
    with pytest.raises(ValueError, match="Invalid project status"):
        service.change_status(int(project.id), "Complete")
