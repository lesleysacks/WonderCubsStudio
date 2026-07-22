"""Project persistence layer."""
from __future__ import annotations

from pathlib import Path

from src.database.connection import create_connection
from src.models.project import Project


class ProjectRepository:
    """Read and write project records."""

    def __init__(self, database_file: Path) -> None:
        self._database_file = database_file

    def add(self, project: Project) -> int:
        """Insert a project and return its database ID."""
        query = """
        INSERT INTO Projects
            (video_number, title, lesson, status, created_at, folder_path)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            project.video_number,
            project.title,
            project.lesson,
            project.status,
            project.created_at,
            project.folder_path,
        )
        with create_connection(self._database_file) as connection:
            cursor = connection.execute(query, values)
            connection.commit()
            return int(cursor.lastrowid)

    def list_all(self) -> list[Project]:
        """Return all projects ordered by video number."""
        query = """
        SELECT id, video_number, title, lesson, status, created_at, folder_path
        FROM Projects
        ORDER BY video_number ASC
        """
        with create_connection(self._database_file) as connection:
            rows = connection.execute(query).fetchall()
        return [Project(**dict(row)) for row in rows]

    def get_next_video_number(self) -> str:
        """Return the next zero-padded project number from persisted projects."""
        with create_connection(self._database_file) as connection:
            rows = connection.execute("SELECT video_number FROM Projects").fetchall()

        numeric_numbers = [
            int(str(row["video_number"]))
            for row in rows
            if str(row["video_number"]).isdigit()
        ]
        next_number = max(numeric_numbers, default=0) + 1
        return f"{next_number:03d}"
