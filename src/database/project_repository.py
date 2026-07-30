"""Project persistence layer."""
from __future__ import annotations

from pathlib import Path

from src.database.connection import create_connection
from src.models.project import Project


class ProjectRepository:
    """Read and write project records."""

    COLUMNS = (
        "id, video_number, title, lesson, status, created_at, folder_path, "
        "updated_at, published_at"
    )

    def __init__(self, database_file: Path) -> None:
        self._database_file = database_file

    def add(self, project: Project) -> int:
        query = """
        INSERT INTO Projects
            (video_number, title, lesson, status, created_at, updated_at,
             published_at, folder_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            project.video_number, project.title, project.lesson, project.status,
            project.created_at, project.updated_at, project.published_at,
            project.folder_path,
        )
        with create_connection(self._database_file) as connection:
            cursor = connection.execute(query, values)
            connection.commit()
            return int(cursor.lastrowid)

    def update_lifecycle(
        self, project_id: int, status: str, updated_at: str, published_at: str | None
    ) -> bool:
        """Persist lifecycle fields atomically."""
        with create_connection(self._database_file) as connection:
            cursor = connection.execute(
                """
                UPDATE Projects
                SET status = ?, updated_at = ?, published_at = ?
                WHERE id = ?
                """,
                (status, updated_at, published_at, project_id),
            )
            connection.commit()
            return cursor.rowcount == 1

    def get(self, project_id: int) -> Project | None:
        with create_connection(self._database_file) as connection:
            row = connection.execute(
                f"SELECT {self.COLUMNS} FROM Projects WHERE id = ?", (project_id,)
            ).fetchone()
        return Project(**dict(row)) if row else None

    def get_by_title(self, title: str) -> Project | None:
        with create_connection(self._database_file) as connection:
            row = connection.execute(
                f"SELECT {self.COLUMNS} FROM Projects "
                "WHERE title = ? ORDER BY id DESC LIMIT 1",
                (title,),
            ).fetchone()
        return Project(**dict(row)) if row else None

    def list_all(self) -> list[Project]:
        with create_connection(self._database_file) as connection:
            rows = connection.execute(
                f"SELECT {self.COLUMNS} FROM Projects ORDER BY video_number ASC"
            ).fetchall()
        return [Project(**dict(row)) for row in rows]

    def list_recent(self, limit: int = 10) -> list[Project]:
        with create_connection(self._database_file) as connection:
            rows = connection.execute(
                f"SELECT {self.COLUMNS} FROM Projects "
                "ORDER BY datetime(updated_at) DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Project(**dict(row)) for row in rows]

    def get_next_video_number(self) -> str:
        with create_connection(self._database_file) as connection:
            rows = connection.execute("SELECT video_number FROM Projects").fetchall()
        numbers = [
            int(str(row["video_number"]))
            for row in rows
            if str(row["video_number"]).isdigit()
        ]
        return f"{max(numbers, default=0) + 1:03d}"
