"""Prompt persistence layer."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from src.database.connection import create_connection
from src.models.prompt import Prompt
from src.utils.logger import get_logger


class PromptRepository:
    """Read and write prompt records without applying business rules."""

    _COLUMNS = ("id", "name", "category", "version", "description", "template",
                "variables", "created_at", "updated_at", "active")

    def __init__(self, database_file: Path) -> None:
        self._database_file = database_file
        self._logger = get_logger(__name__)

    def create(self, prompt: Prompt) -> Prompt:
        query = """INSERT INTO Prompts
        (id, name, category, version, description, template, variables, created_at, updated_at, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        with create_connection(self._database_file) as connection:
            connection.execute(query, self._to_values(prompt))
            connection.commit()
        return prompt

    def update(self, prompt: Prompt) -> bool:
        """Update one persisted version; version policy belongs to PromptService."""
        query = """UPDATE Prompts SET name = ?, category = ?, description = ?, template = ?,
        variables = ?, created_at = ?, updated_at = ?, active = ? WHERE id = ? AND version = ?"""
        values = (
            prompt.name, prompt.category, prompt.description, prompt.template,
            json.dumps(list(prompt.variables)), prompt.created_at, prompt.updated_at,
            int(prompt.active), prompt.id, prompt.version,
        )
        with create_connection(self._database_file) as connection:
            cursor = connection.execute(query, values)
            connection.commit()
        return cursor.rowcount > 0

    def get_by_id(self, prompt_id: str, version: int | None = None) -> Prompt | None:
        query = f"SELECT {self._select_columns()} FROM Prompts WHERE id = ?"
        values: tuple[object, ...] = (prompt_id,)
        if version is None:
            query += " AND active = 1"
        else:
            query += " AND version = ?"
            values += (version,)
        query += " LIMIT 1"
        with create_connection(self._database_file) as connection:
            row = connection.execute(query, values).fetchone()
        return self._from_row(row) if row else None

    def get_versions(self, prompt_id: str) -> list[Prompt]:
        query = f"SELECT {self._select_columns()} FROM Prompts WHERE id = ? ORDER BY version DESC"
        with create_connection(self._database_file) as connection:
            rows = connection.execute(query, (prompt_id,)).fetchall()
        return [self._from_row(row) for row in rows]

    def get_all_active(self) -> list[Prompt]:
        query = f"SELECT {self._select_columns()} FROM Prompts WHERE active = 1 ORDER BY name COLLATE NOCASE"
        with create_connection(self._database_file) as connection:
            rows = connection.execute(query).fetchall()
        return [self._from_row(row) for row in rows]

    def search(self, search_text: str) -> list[Prompt]:
        query = f"""SELECT {self._select_columns()} FROM Prompts
        WHERE active = 1 AND (name LIKE ? OR category LIKE ? OR description LIKE ? OR template LIKE ?)
        ORDER BY name COLLATE NOCASE"""
        pattern = f"%{search_text.strip()}%"
        with create_connection(self._database_file) as connection:
            rows = connection.execute(query, (pattern, pattern, pattern, pattern)).fetchall()
        return [self._from_row(row) for row in rows]

    def deactivate_all(self, prompt_id: str) -> None:
        with create_connection(self._database_file) as connection:
            connection.execute("UPDATE Prompts SET active = 0 WHERE id = ?", (prompt_id,))
            connection.commit()

    def activate_version(self, prompt_id: str, version: int) -> bool:
        with create_connection(self._database_file) as connection:
            cursor = connection.execute(
                "UPDATE Prompts SET active = 1 WHERE id = ? AND version = ?", (prompt_id, version)
            )
            connection.commit()
        return cursor.rowcount > 0

    def delete(self, prompt_id: str, version: int | None = None) -> bool:
        query, values = ("DELETE FROM Prompts WHERE id = ?", (prompt_id,))
        if version is not None:
            query += " AND version = ?"
            values += (version,)
        with create_connection(self._database_file) as connection:
            cursor = connection.execute(query, values)
            connection.commit()
        return cursor.rowcount > 0

    def exists(self, prompt_id: str) -> bool:
        with create_connection(self._database_file) as connection:
            return connection.execute("SELECT 1 FROM Prompts WHERE id = ? LIMIT 1", (prompt_id,)).fetchone() is not None

    @classmethod
    def _select_columns(cls) -> str:
        return ", ".join(cls._COLUMNS)

    @staticmethod
    def _to_values(prompt: Prompt) -> tuple[object, ...]:
        return (prompt.id, prompt.name, prompt.category, prompt.version, prompt.description,
                prompt.template, json.dumps(list(prompt.variables)), prompt.created_at,
                prompt.updated_at, int(prompt.active))

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Prompt:
        values = dict(row)
        values["variables"] = tuple(json.loads(values["variables"]))
        values["active"] = bool(values["active"])
        return Prompt(**values)
