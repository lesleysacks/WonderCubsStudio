"""Dashboard data models."""
from __future__ import annotations

from dataclasses import dataclass

from src.models.project import Project


@dataclass(frozen=True)
class ProjectStatistics:
    total_projects: int = 0
    draft_projects: int = 0
    in_production_projects: int = 0
    review_projects: int = 0
    ready_to_publish_projects: int = 0
    published_projects: int = 0
    archived_projects: int = 0
    active_production_count: int = 0
    # Retained for compatibility with pre-lifecycle dashboard consumers.
    projects_in_progress: int = 0
    videos_uploaded: int = 0
    completed_projects: int = 0


@dataclass(frozen=True)
class DailyGoal:
    id: int | None
    goal_date: str
    description: str
    is_completed: bool


@dataclass(frozen=True)
class DashboardData:
    statistics: ProjectStatistics
    latest_project: Project | None
    todays_goal: DailyGoal | None
    next_video_number: str = "001"
    recent_activity: tuple[Project, ...] = ()
