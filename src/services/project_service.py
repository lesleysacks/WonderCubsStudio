"""Project lifecycle business service."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from pathlib import Path
import re
import shutil
import sqlite3
from uuid import uuid4

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

    STAGING_PREFIX = ".wcs-creating-"

    def __init__(
        self,
        repository: ProjectRepository,
        projects_dir: Path | Callable[[], Path],
        event_bus: EventBus | None = None,
    ) -> None:
        """``projects_dir`` is a folder, or a callable resolving it at use time
        (so the saved "Default Project Folder" setting applies immediately)."""
        self._repository = repository
        self._projects_dir = projects_dir
        self._event_bus = event_bus or EventBus()

    def create_project(
        self,
        title: str,
        lesson: str,
        status: str = DEFAULT_STATUS,
        on_create: Callable[[sqlite3.Connection, Project], None] | None = None,
    ) -> Project:
        """Create the project row, its folder scaffold and any linked records
        as one unit: either all of them exist afterwards or none do.

        ``on_create(connection, project)`` runs inside the same database
        transaction, for records that must be created with the project.
        """
        clean_title = title.strip()
        clean_lesson = lesson.strip()
        clean_status = ProjectStatus.parse(status).value
        projects_dir = self.get_projects_dir()
        clean_number = self._next_free_number(projects_dir)
        self._validate_project_data(clean_number, clean_title, clean_lesson)

        project_folder = projects_dir / f"{clean_number}_{self._slugify(clean_title)}"
        if project_folder.exists():
            raise FileExistsError(f"Project folder already exists: {project_folder}")

        timestamp = self._now()
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

        # Build the scaffold in a hidden staging folder first; it only becomes
        # the real project folder once every database write has succeeded.
        staging = projects_dir / f"{self.STAGING_PREFIX}{uuid4().hex}"
        moved_into_place = False
        try:
            self._create_project_folders(staging)
            self._write_project_readme(
                staging, clean_title, clean_lesson, clean_status, timestamp
            )
            with self._repository.transaction() as connection:
                project_id = self._repository.add(pending, connection)
                project = replace(pending, id=project_id)
                if on_create is not None:
                    on_create(connection, project)
                if project_folder.exists():
                    raise FileExistsError(f"Project folder already exists: {project_folder}")
                staging.rename(project_folder)
                moved_into_place = True
            # Leaving the block committed the transaction.
        except BaseException:
            if moved_into_place and project_folder.exists() and not staging.exists():
                # The commit itself failed after the folder was moved: undo it.
                project_folder.rename(staging)
            self._discard_staging(staging)
            raise
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

    def get_recent_activity(self, limit: int = 10) -> list[Project]:
        return self._repository.list_recent(limit)

    def get_next_project_number(self) -> str:
        return self._next_free_number(self.get_projects_dir(create=False))

    def get_projects_dir(self, create: bool = True) -> Path:
        """Resolve the folder new projects are created in."""
        source = self._projects_dir
        folder = Path(source() if callable(source) else source).expanduser()
        if create:
            try:
                folder.mkdir(parents=True, exist_ok=True)
            except OSError as error:
                raise OSError(f"Project folder is not available: {folder} ({error})") from error
            if not folder.is_dir():
                raise NotADirectoryError(f"Project folder is not a folder: {folder}")
        return folder

    def get_folder_preview(self, title: str) -> str:
        folder = self.get_projects_dir(create=False)
        return str(folder / f"{self._next_free_number(folder)}_{self._slugify(title.strip())}")

    def _next_free_number(self, projects_dir: Path) -> str:
        """Next database number, skipped past numbers already used by a folder.

        Folders can outlive their database rows (for example after restoring an
        older backup). Reusing their number would collide with the folder, so
        those numbers are skipped rather than failing every creation.
        """
        number = int(self._repository.get_next_video_number())
        used: set[int] = set()
        if projects_dir.is_dir():
            for entry in projects_dir.iterdir():
                prefix = entry.name.split("_", 1)[0]
                if prefix.isdigit():
                    used.add(int(prefix))
        while number in used:
            number += 1
        return f"{number:03d}"

    def _discard_staging(self, staging: Path) -> None:
        """Remove a staging scaffold this service created moments ago."""
        if staging.name.startswith(self.STAGING_PREFIX) and staging.is_dir():
            shutil.rmtree(staging, ignore_errors=True)

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
