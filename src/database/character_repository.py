"""Character persistence layer."""
from __future__ import annotations

from pathlib import Path
import sqlite3

from src.database.connection import create_connection
from src.models.character import Character
from src.utils.logger import get_logger


class CharacterRepository:
    """Read and write character records."""

    _COLUMNS = (
        "uuid",
        "name",
        "species",
        "gender",
        "age_group",
        "fur_color",
        "mane_color",
        "eye_color",
        "shirt",
        "pants",
        "shoes",
        "accessories",
        "personality",
        "voice_style",
        "catchphrase",
        "description",
        "image_folder",
        "created_at",
        "updated_at",
    )

    def __init__(self, database_file: Path) -> None:
        self._database_file = database_file
        self._logger = get_logger(__name__)

    def create(self, character: Character) -> Character:
        """Insert a character and return the saved record."""
        query = """
        INSERT INTO Characters
            (uuid, name, species, gender, age_group, fur_color, mane_color,
             eye_color, shirt, pants, shoes, accessories, personality,
             voice_style, catchphrase, description, image_folder, created_at,
             updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with create_connection(self._database_file) as connection:
                connection.execute(query, self._to_values(character))
                connection.commit()
        except sqlite3.Error:
            self._logger.exception("Failed to create character %s", character.uuid)
            raise

        self._logger.info("Character created: %s", character.uuid)
        return character

    def update(self, character: Character) -> bool:
        """Update a character by UUID."""
        query = """
        UPDATE Characters
        SET name = ?,
            species = ?,
            gender = ?,
            age_group = ?,
            fur_color = ?,
            mane_color = ?,
            eye_color = ?,
            shirt = ?,
            pants = ?,
            shoes = ?,
            accessories = ?,
            personality = ?,
            voice_style = ?,
            catchphrase = ?,
            description = ?,
            image_folder = ?,
            created_at = ?,
            updated_at = ?
        WHERE uuid = ?
        """
        values = self._to_values(character)[1:] + (character.uuid,)
        try:
            with create_connection(self._database_file) as connection:
                cursor = connection.execute(query, values)
                connection.commit()
                updated = cursor.rowcount > 0
        except sqlite3.Error:
            self._logger.exception("Failed to update character %s", character.uuid)
            raise

        if updated:
            self._logger.info("Character updated: %s", character.uuid)
        return updated

    def delete(self, character_uuid: str) -> bool:
        """Delete a character by UUID."""
        query = "DELETE FROM Characters WHERE uuid = ?"
        try:
            with create_connection(self._database_file) as connection:
                cursor = connection.execute(query, (character_uuid,))
                connection.commit()
                deleted = cursor.rowcount > 0
        except sqlite3.Error:
            self._logger.exception("Failed to delete character %s", character_uuid)
            raise

        if deleted:
            self._logger.info("Character deleted: %s", character_uuid)
        return deleted

    def get_by_id(self, character_uuid: str) -> Character | None:
        """Return a character by UUID."""
        query = f"""
        SELECT {self._select_columns()}
        FROM Characters
        WHERE uuid = ?
        LIMIT 1
        """
        try:
            with create_connection(self._database_file) as connection:
                row = connection.execute(query, (character_uuid,)).fetchone()
        except sqlite3.Error:
            self._logger.exception("Failed to load character %s", character_uuid)
            raise
        return self._from_row(row) if row else None

    def get_all(self) -> list[Character]:
        """Return all characters ordered by name."""
        query = f"""
        SELECT {self._select_columns()}
        FROM Characters
        ORDER BY name COLLATE NOCASE ASC
        """
        try:
            with create_connection(self._database_file) as connection:
                rows = connection.execute(query).fetchall()
        except sqlite3.Error:
            self._logger.exception("Failed to load characters")
            raise
        return [self._from_row(row) for row in rows]

    def search(self, search_text: str) -> list[Character]:
        """Search characters by text fields."""
        query = f"""
        SELECT {self._select_columns()}
        FROM Characters
        WHERE name LIKE ?
           OR species LIKE ?
           OR personality LIKE ?
           OR voice_style LIKE ?
           OR catchphrase LIKE ?
           OR description LIKE ?
        ORDER BY name COLLATE NOCASE ASC
        """
        pattern = f"%{search_text.strip()}%"
        values = (pattern, pattern, pattern, pattern, pattern, pattern)
        try:
            with create_connection(self._database_file) as connection:
                rows = connection.execute(query, values).fetchall()
        except sqlite3.Error:
            self._logger.exception("Failed to search characters")
            raise
        return [self._from_row(row) for row in rows]

    def exists(self, character_uuid: str) -> bool:
        """Return True when a character UUID exists."""
        query = "SELECT 1 FROM Characters WHERE uuid = ? LIMIT 1"
        try:
            with create_connection(self._database_file) as connection:
                row = connection.execute(query, (character_uuid,)).fetchone()
        except sqlite3.Error:
            self._logger.exception("Failed to check character existence %s", character_uuid)
            raise
        return row is not None

    @classmethod
    def _select_columns(cls) -> str:
        return ", ".join(cls._COLUMNS)

    @classmethod
    def _to_values(cls, character: Character) -> tuple[str, ...]:
        return tuple(str(getattr(character, column)) for column in cls._COLUMNS)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Character:
        return Character(**dict(row))
