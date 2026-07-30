"""Project lifecycle business service."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from src.database.project_repository import ProjectRepository
from src.models.project import Project, ProjectStatus
from src.utils.event_bus import EventBus


class ProjectService:
    """Own project lifecycle rules and coordinate persisted project assets."""

    DEFAULT_STATUS = ProjectStatus.DRAFT.value
    VALID_STATUSES = ProjectStatus.values()
    ACTIVE_STATUSES = (
        ProjectStatus.IN_PRODUCTION.value,
        ProjectStatus.REVIEW.value,
        ProjectStatus.READY_TO_PUBLISH.value,
    )
    PIPELINE_FOLDERS = (
        "Story", "Voice", "Prompts", "Images", "Animation", "Thumbnail",
        "SEO", "Final", "Upload", "Analytics",
    )
    PLACEHOLDER_FILES = {
        "Story": {"story.txt": "Story draft placeholder.\n"},
        "Voice": {"voice_script.txt": "Voice script placeholder.\n"},
        "Prompts": {"scene_prompts.txt": "Scene prompts placeholder.\n"},
        "Images": {"notes.txt": "Image production notes placeholder.\n"},
        "Animation": {"notes.txt": "Animation notes placeholder.\n"},
        "Thumbnail": {"thumbnail_prompt.txt": "Thumbnail prompt placeholder.\n"},
        "SEO": {"seo.txt": "SEO title, description, and tags placeholder.\n"},
        "Final": {"notes.txt": "Final render notes placeholder.\n"},
        "Upload": {"notes.txt": "Upload checklist placeholder.\n"},
        "Analytics": {"notes.txt": "Analytics notes placeholder.\n"},
    }

    def __init__(
        self,
        repository: ProjectRepository,
        projects_dir: Path,
        event_bus: EventBus | None = None,
    ) -> None:
        self._repository = repository
        self._projects_dir = projects_dir
        self._event_bus = event_bus or EventBus()

    def create_project(
        self, title: str, lesson: str, status: str = DEFAULT_STATUS
    ) -> Project:
        clean_number = self.get_next_project_number()
        clean_title = title.strip()
        clean_lesson = lesson.strip()
        clean_status = ProjectStatus.parse(status).value
        self._validate_project_data(clean_number, clean_title, clean_lesson)

        project_folder = self._projects_dir / (
            f"{clean_number}_{self._slugify(clean_title)}"
        )
        if project_folder.exists():
            raise FileExistsError(f"Project folder already exists: {project_folder}")

        timestamp = self._now()
        self._create_project_folders(project_folder)
        self._write_project_readme(
            project_folder, clean_title, clean_lesson, clean_status, timestamp
        )
        published_at = (
            timestamp if clean_status == ProjectStatus.PUBLISHED.value else None
        )
        pending = Project(
            id=None,
            video_number=clean_number,
            title=clean_title,
            lesson=clean_lesson,
            status=clean_status,
            created_at=timestamp,
            folder_path=str(project_folder),
            updated_at=timestamp,
            published_at=published_at,
        )
        try:
            project_id = self._repository.add(pending)
        except Exception:
            # Database remains authoritative. Folder cleanup is deliberately
            # conservative so user-authored files are never removed.
            raise
        project = Project(**{**pending.__dict__, "id": project_id})
        self._publish_updated(project, "created")
        return project

    def change_status(self, project_id: int, status: str) -> Project:
        """Validate and persist a lifecycle change before emitting an event."""
        target = ProjectStatus.parse(status)
        current = self._repository.get(project_id)
        if current is None:
            raise LookupError(f"Project {project_id} was not found.")

        updated_at = self._now()
        published_at = current.published_at
        if target is ProjectStatus.PUBLISHED and not published_at:
            published_at = updated_at
        if not self._repository.update_lifecycle(
            project_id, target.value, updated_at, published_at
        ):
            raise RuntimeError(f"Project {project_id} could not be saved.")

        saved = self._repository.get(project_id)
        if saved is None:
            raise RuntimeError(f"Project {project_id} disappeared after saving.")
        self._publish_updated(saved, "status_changed")
        return saved

    def change_status_by_title(self, title: str, status: str) -> Project | None:
        """Update the project linked to an existing workspace, when present."""
        project = self._repository.get_by_title(title.strip())
        if project is None:
            return None
        return self.change_status(int(project.id), status)

    def get_dashboard_statistics(self) -> dict[str, int]:
        """Calculate lifecycle totals from current persisted records."""
        projects = self.list_projects()
        counts = {status: 0 for status in self.VALID_STATUSES}
        for project in projects:
            status = project.status if project.status in counts else self.DEFAULT_STATUS
            counts[status] += 1
        counts["Total Projects"] = len(projects)
        counts["Active Production Count"] = sum(
            counts[status] for status in self.ACTIVE_STATUSES
        )
        return counts

    def get_recent_activity(self, limit: int = 10) -> list[Project]:
        return self._repository.list_recent(limit)

    def get_next_project_number(self) -> str:
        return self._repository.get_next_video_number()

    def get_folder_preview(self, title: str) -> str:
        return str(
            self._projects_dir
            / f"{self.get_next_project_number()}_{self._slugify(title.strip())}"
        )

    def list_projects(self) -> list[Project]:
        return self._repository.list_all()

    def _publish_updated(self, project: Project, action: str) -> None:
        self._event_bus.publish(
            "project_updated",
            {
                "project_id": project.id,
                "workspace_id": None,
                "status": project.status,
                "action": action,
            },
        )

    def _create_project_folders(self, project_folder: Path) -> None:
        project_folder.mkdir(parents=True, exist_ok=False)
        for folder_name in self.PIPELINE_FOLDERS:
            folder = project_folder / folder_name
            folder.mkdir()
            for file_name, content in self.PLACEHOLDER_FILES.get(
                folder_name, {}
            ).items():
                (folder / file_name).write_text(content, encoding="utf-8")

    @staticmethod
    def _write_project_readme(
        project_folder: Path,
        title: str,
        lesson: str,
        status: str,
        created_at: str,
    ) -> None:
        content = f"""# {title}

## Project Name

{title}

## Lesson

{lesson}

## Status

{status}

## Date Created

{created_at}

## Pipeline

- Story
- Voice
- Images
- Animation
- Thumbnail
- SEO
- Upload
"""
        (project_folder / "README.md").write_text(content, encoding="utf-8")

    @staticmethod
    def _slugify(value: str) -> str:
        value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
        return value.strip("_") or "Untitled"

    @staticmethod
    def _validate_project_data(
        video_number: str, title: str, lesson: str
    ) -> None:
        if not video_number:
            raise ValueError("Video Number is required.")
        if not title:
            raise ValueError("Video Title is required.")
        if not lesson:
            raise ValueError("Lesson is required.")

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
