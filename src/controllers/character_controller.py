"""Controller for Character Workspace actions."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.models.character import Character
from src.services.character_service import CharacterService
from src.utils.logger import get_logger


class CharacterController:
    """Coordinate Character Workspace UI actions with CharacterService."""

    def __init__(self, service: CharacterService) -> None:
        self._service = service
        self._logger = get_logger(__name__)

    def on_new_character(self) -> Character:
        """Return a blank character draft for the UI."""
        self._logger.info("New character draft opened")
        return Character()

    def on_save_character(self, character: Character) -> Character:
        """Create or update a character through the service."""
        if self._service.character_exists(character.uuid):
            return self._service.update_character(character.uuid, character)
        return self._service.create_character(character)

    def on_delete_character(self, character_uuid: str) -> bool:
        """Delete a character through the service."""
        return self._service.delete_character(character_uuid)

    def on_duplicate_character(self, character_uuid: str) -> Character:
        """Duplicate a character with a fresh UUID and unique display name."""
        source = self._service.get_character(character_uuid)
        duplicate_name = self._build_duplicate_name(source.name)
        timestamp = self._current_timestamp()
        duplicate = replace(
            source,
            uuid=str(uuid4()),
            name=duplicate_name,
            created_at=timestamp,
            updated_at=timestamp,
        )
        return self._service.create_character(duplicate)

    def on_export_character(self, character_uuid: str) -> dict[str, Any]:
        """Export a character through the service."""
        return self._service.export_json(character_uuid)

    def on_search_changed(self, search_text: str) -> list[Character]:
        """Return filtered characters while the user types."""
        if not search_text.strip():
            return self._service.get_all_characters()
        return self._service.search_characters(search_text)

    def load_characters(self) -> list[Character]:
        """Return all characters for initial workspace loading."""
        return self._service.get_all_characters()

    def _build_duplicate_name(self, name: str) -> str:
        existing_names = {
            character.name.strip().casefold()
            for character in self._service.get_all_characters()
        }
        base_name = f"{name.strip()} Copy".strip()
        candidate = base_name
        index = 2
        while candidate.casefold() in existing_names:
            candidate = f"{base_name} {index}"
            index += 1
        return candidate

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
