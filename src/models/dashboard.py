"""Dashboard data models."""
from __future__ import annotations

from dataclasses import dataclass

from src.models.project import Project


@dataclass(frozen=True)
class ProjectStatistics:
    """Aggregated project statistics for the dashboard."""

    total_projects: int
    published_projects: int
    projects_in_progress: int
    draft_projects: int
    videos_uploaded: int
    completed_projects: int


@dataclass(frozen=True)
class DailyGoal:
    """A production goal for a specific date."""

    id: int | None
    goal_date: str
    description: str
    is_completed: bool


@dataclass(frozen=True)
class DashboardData:
    """All data required to render the dashboard."""

    statistics: ProjectStatistics
    latest_project: Project | None
    todays_goal: DailyGoal | None
