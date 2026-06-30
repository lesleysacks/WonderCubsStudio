"""Dashboard business service."""
from __future__ import annotations

from datetime import date

from src.database.dashboard_repository import DashboardRepository
from src.models.dashboard import DashboardData, DailyGoal, ProjectStatistics
from src.models.project import Project
from src.utils.logger import get_logger


class DashboardService:
    """Provide dashboard-ready application data."""

    def __init__(self, repository: DashboardRepository) -> None:
        self._repository = repository
        self._logger = get_logger(__name__)

    def get_dashboard_data(self) -> DashboardData:
        """Return all data needed by the dashboard screen."""
        self._logger.info("Dashboard opened")
        statistics = self.get_statistics()
        latest_project = self.get_latest_project()
        todays_goal = self.get_todays_goal()
        return DashboardData(
            statistics=statistics,
            latest_project=latest_project,
            todays_goal=todays_goal,
        )

    def get_statistics(self) -> ProjectStatistics:
        """Load project statistics."""
        try:
            statistics = self._repository.get_statistics()
            self._logger.info("Statistics loaded")
            return statistics
        except Exception:
            self._logger.exception("Error loading statistics")
            raise

    def get_latest_project(self) -> Project | None:
        """Load the most recently created project."""
        try:
            return self._repository.get_latest_project()
        except Exception:
            self._logger.exception("Error loading latest project")
            raise

    def get_todays_goal(self) -> DailyGoal | None:
        """Load today's production goal."""
        try:
            goal = self._repository.get_goal_for_date(date.today().isoformat())
            self._logger.info("Goal loaded")
            return goal
        except Exception:
            self._logger.exception("Error loading today's goal")
            raise
