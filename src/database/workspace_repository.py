"""Workspace context persistence layer."""
from __future__ import annotations

from pathlib import Path
import sqlite3

from src.database.connection import create_connection
from src.models.workspace import Workspace
from src.utils.logger import get_logger


class WorkspaceRepository:
    """Read and write workspace context records."""

    _COLUMNS = (
        "uuid",
        "project_name",
        "lesson",
        "topic",
        "language",
        "target_platform",
        "resolution",
        "aspect_ratio",
        "duration",
        "style",
        "current_scene",
        "status",
        "created_at",
        "updated_at",
    )

    def __init__(self, database_file: Path) -> None:
        self._database_file = database_file
        self._logger = get_logger(__name__)

    def create(self, workspace: Workspace) -> Workspace:
        """Insert a workspace and return the saved record."""
        query = """
        INSERT INTO Workspaces
            (uuid, project_name, lesson, topic, language, target_platform,
             resolution, aspect_ratio, duration, style, current_scene, status,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with create_connection(self._database_file) as connection:
                connection.execute(query, self._to_values(workspace))
                connection.commit()
        except sqlite3.Error:
            self._logger.exception("Failed to create workspace %s", workspace.uuid)
            raise

        self._logger.info("Workspace created: %s", workspace.uuid)
        return workspace

    def update(self, workspace: Workspace) -> bool:
        """Update a workspace by UUID."""
        query = """
        UPDATE Workspaces
        SET project_name = ?,
            lesson = ?,
            topic = ?,
            language = ?,
            target_platform = ?,
            resolution = ?,
            aspect_ratio = ?,
            duration = ?,
            style = ?,
            current_scene = ?,
            status = ?,
            created_at = ?,
            updated_at = ?
        WHERE uuid = ?
        """
        values = self._to_values(workspace)[1:] + (workspace.uuid,)
        try:
            with create_connection(self._database_file) as connection:
                cursor = connection.execute(query, values)
                connection.commit()
                updated = cursor.rowcount > 0
        except sqlite3.Error:
            self._logger.exception("Failed to update workspace %s", workspace.uuid)
            raise

        if updated:
            self._logger.info("Workspace updated: %s", workspace.uuid)
        return updated

    def delete(self, workspace_uuid: str) -> bool:
        """Delete a workspace by UUID."""
        query = "DELETE FROM Workspaces WHERE uuid = ?"
        try:
            with create_connection(self._database_file) as connection:
                cursor = connection.execute(query, (workspace_uuid,))
                connection.commit()
                deleted = cursor.rowcount > 0
        except sqlite3.Error:
            self._logger.exception("Failed to delete workspace %s", workspace_uuid)
            raise

        if deleted:
            self._logger.info("Workspace deleted: %s", workspace_uuid)
        return deleted

    def get_by_id(self, workspace_uuid: str) -> Workspace | None:
        """Return a workspace by UUID."""
        query = f"""
        SELECT {self._select_columns()}
        FROM Workspaces
        WHERE uuid = ?
        LIMIT 1
        """
        try:
            with create_connection(self._database_file) as connection:
                row = connection.execute(query, (workspace_uuid,)).fetchone()
        except sqlite3.Error:
            self._logger.exception("Failed to load workspace %s", workspace_uuid)
            raise
        return self._from_row(row) if row else None

    def get_all(self) -> list[Workspace]:
        """Return all workspaces ordered by update time."""
        query = f"""
        SELECT {self._select_columns()}
        FROM Workspaces
        ORDER BY datetime(updated_at) DESC, project_name COLLATE NOCASE ASC
        """
        try:
            with create_connection(self._database_file) as connection:
                rows = connection.execute(query).fetchall()
        except sqlite3.Error:
            self._logger.exception("Failed to load workspaces")
            raise
        return [self._from_row(row) for row in rows]

    def exists(self, workspace_uuid: str) -> bool:
        """Return True when a workspace UUID exists."""
        query = "SELECT 1 FROM Workspaces WHERE uuid = ? LIMIT 1"
        try:
            with create_connection(self._database_file) as connection:
                row = connection.execute(query, (workspace_uuid,)).fetchone()
        except sqlite3.Error:
            self._logger.exception("Failed to check workspace existence %s", workspace_uuid)
            raise
        return row is not None

    @classmethod
    def _select_columns(cls) -> str:
        return ", ".join(cls._COLUMNS)

    @classmethod
    def _to_values(cls, workspace: Workspace) -> tuple[str, ...]:
        return tuple(str(getattr(workspace, column)) for column in cls._COLUMNS)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Workspace:
        data = dict(row)
        data["duration"] = int(data["duration"])
        return Workspace(**data)
