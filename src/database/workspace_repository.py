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
        "project_id",
    )

    def __init__(self, database_file: Path) -> None:
        self._database_file = database_file
        self._logger = get_logger(__name__)

    def create(
        self, workspace: Workspace, connection: sqlite3.Connection | None = None
    ) -> Workspace:
        """Insert a workspace and return the saved record.

        When ``connection`` is given the insert joins the caller's transaction
        and the caller commits.
        """
        query = """
        INSERT INTO Workspaces
            (uuid, project_name, lesson, topic, language, target_platform,
             resolution, aspect_ratio, duration, style, current_scene, status,
             created_at, updated_at, project_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            if connection is not None:
                connection.execute(query, self._to_values(workspace))
            else:
                with create_connection(self._database_file) as own_connection:
                    own_connection.execute(query, self._to_values(workspace))
                    own_connection.commit()
        except sqlite3.Error:
            self._logger.exception("Failed to create workspace %s", workspace.uuid)
            raise

        self._logger.info("Workspace created: %s", workspace.uuid)
        return workspace

    def update(self, workspace: Workspace) -> bool:
        """Update a workspace by UUID. The project link is never changed here."""
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
        values = self._to_values(workspace)[1:-1] + (workspace.uuid,)
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

    def get_by_project_id(self, project_id: int) -> Workspace | None:
        """Return the workspace linked to a project, if any."""
        query = f"""
        SELECT {self._select_columns()}
        FROM Workspaces
        WHERE project_id = ?
        LIMIT 1
        """
        try:
            with create_connection(self._database_file) as connection:
                row = connection.execute(query, (project_id,)).fetchone()
        except sqlite3.Error:
            self._logger.exception("Failed to load workspace for project %s", project_id)
            raise
        return self._from_row(row) if row else None

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
    def _to_values(cls, workspace: Workspace) -> tuple[object, ...]:
        values: list[object] = [
            str(getattr(workspace, column)) for column in cls._COLUMNS[:-1]
        ]
        values.append(None if workspace.project_id is None else int(workspace.project_id))
        return tuple(values)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Workspace:
        data = dict(row)
        data["duration"] = int(data["duration"])
        if data.get("project_id") is not None:
            data["project_id"] = int(data["project_id"])
        return Workspace(**data)
