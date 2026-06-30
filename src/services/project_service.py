"""Project creation and retrieval services."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from src.database.project_repository import ProjectRepository
from src.models.project import Project


class ProjectService:
    """Coordinate project database records and filesystem assets."""

    STATUS_IN_PROGRESS = "In Progress"
    PIPELINE_FOLDERS = (
        "Story",
        "Voice",
        "Prompts",
        "Images",
        "Animation",
        "Thumbnail",
        "SEO",
        "Final",
        "Upload",
        "Analytics",
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

    def __init__(self, repository: ProjectRepository, projects_dir: Path) -> None:
        self._repository = repository
        self._projects_dir = projects_dir

    def create_project(self, video_number: str, title: str, lesson: str) -> Project:
        """Create a project folder tree and save its database record."""
        clean_number = video_number.strip()
        clean_title = title.strip()
        clean_lesson = lesson.strip()
        self._validate_project_data(clean_number, clean_title, clean_lesson)

        folder_name = f"{clean_number}_{self._slugify(clean_title)}"
        project_folder = self._projects_dir / folder_name
        if project_folder.exists():
            raise FileExistsError(f"Project folder already exists: {project_folder}")

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._create_project_folders(project_folder)
        self._write_project_readme(project_folder, clean_title, clean_lesson, created_at)

        project = Project(
            id=None,
            video_number=clean_number,
            title=clean_title,
            lesson=clean_lesson,
            status=self.STATUS_IN_PROGRESS,
            created_at=created_at,
            folder_path=str(project_folder),
        )
        project_id = self._repository.add(project)
        return Project(project_id, clean_number, clean_title, clean_lesson, self.STATUS_IN_PROGRESS, created_at, str(project_folder))

    def list_projects(self) -> list[Project]:
        """Return all known projects."""
        return self._repository.list_all()

    def _create_project_folders(self, project_folder: Path) -> None:
        project_folder.mkdir(parents=True, exist_ok=False)
        for folder_name in self.PIPELINE_FOLDERS:
            folder = project_folder / folder_name
            folder.mkdir()
            for file_name, content in self.PLACEHOLDER_FILES.get(folder_name, {}).items():
                (folder / file_name).write_text(content, encoding="utf-8")

    def _write_project_readme(self, project_folder: Path, title: str, lesson: str, created_at: str) -> None:
        content = f"""# {title}

## Project Name

{title}

## Lesson

{lesson}

## Status

{self.STATUS_IN_PROGRESS}

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
    def _validate_project_data(video_number: str, title: str, lesson: str) -> None:
        if not video_number:
            raise ValueError("Video Number is required.")
        if not title:
            raise ValueError("Video Title is required.")
        if not lesson:
            raise ValueError("Lesson is required.")
