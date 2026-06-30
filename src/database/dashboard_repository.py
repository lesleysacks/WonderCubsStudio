"""Dashboard persistence layer."""
from __future__ import annotations

from pathlib import Path
import sqlite3

from src.database.connection import create_connection
from src.models.dashboard import DailyGoal, ProjectStatistics
from src.models.project import Project
from src.utils.logger import get_logger


class DashboardRepository:
    """Read dashboard data from SQLite."""

    COMPLETED_STATUSES = ("Completed", "Published", "Uploaded")

    def __init__(self, database_file: Path) -> None:
        self._database_file = database_file
        self._logger = get_logger(__name__)

    def get_statistics(self) -> ProjectStatistics:
        """Return dashboard project statistics."""
        try:
            with create_connection(self._database_file) as connection:
                rows = connection.execute(
                    "SELECT status, COUNT(*) AS total FROM Projects GROUP BY status"
                ).fetchall()
        except sqlite3.Error:
            self._logger.exception("Failed to load dashboard statistics")
            raise

        counts = {str(row["status"]): int(row["total"]) for row in rows}
        total_projects = sum(counts.values())
        published = counts.get("Published", 0)
        uploaded = counts.get("Uploaded", 0)
        completed = sum(counts.get(status, 0) for status in self.COMPLETED_STATUSES)

        return ProjectStatistics(
            total_projects=total_projects,
            published_projects=published,
            projects_in_progress=counts.get("In Progress", 0),
            draft_projects=counts.get("Draft", 0),
            videos_uploaded=uploaded,
            completed_projects=completed,
        )

    def get_latest_project(self) -> Project | None:
        """Return the newest project by creation date."""
        query = """
        SELECT id, video_number, title, lesson, status, created_at, folder_path
        FROM Projects
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """
        try:
            with create_connection(self._database_file) as connection:
                row = connection.execute(query).fetchone()
        except sqlite3.Error:
            self._logger.exception("Failed to load latest project")
            raise
        return Project(**dict(row)) if row else None

    def get_goal_for_date(self, goal_date: str) -> DailyGoal | None:
        """Return the production goal for a date."""
        query = """
        SELECT id, goal_date, description, is_completed
        FROM Goals
        WHERE goal_date = ?
        ORDER BY id DESC
        LIMIT 1
        """
        try:
            with create_connection(self._database_file) as connection:
                row = connection.execute(query, (goal_date,)).fetchone()
        except sqlite3.Error:
            self._logger.exception("Failed to load today's goal")
            raise
        if row is None:
            return None
        return DailyGoal(
            id=int(row["id"]),
            goal_date=str(row["goal_date"]),
            description=str(row["description"]),
            is_completed=bool(row["is_completed"]),
        )
