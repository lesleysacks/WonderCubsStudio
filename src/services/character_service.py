"""Character business logic service."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from src.database.character_repository import CharacterRepository
from src.models.character import Character
from src.utils.logger import get_logger


class CharacterValidationError(ValueError):
    """Raised when character data fails business validation."""


class CharacterNotFoundError(LookupError):
    """Raised when a character record cannot be found."""


class CharacterService:
    """Validate, transform, and coordinate character operations."""

    MAX_DESCRIPTION_LENGTH = 500

    def __init__(self, repository: CharacterRepository) -> None:
        self._repository = repository
        self._logger = get_logger(__name__)

    def create_character(self, character: Character) -> Character:
        """Validate and save a new character."""
        clean_character = self._prepare_character(character)
        self._validate_character(clean_character)
        self._validate_duplicate_name(clean_character.name)

        created = self._repository.create(clean_character)
        self._logger.info("Character created: %s", created.uuid)
        return created

    def update_character(self, character_uuid: str, character: Character) -> Character:
        """Validate and update an existing character."""
        if character.uuid != character_uuid:
            self._log_validation_failure("UUID cannot be modified.")
            raise CharacterValidationError("UUID cannot be modified.")

        existing_character = self.get_character(character_uuid)
        clean_character = self._prepare_character(
            replace(
                character,
                created_at=existing_character.created_at,
                updated_at=self._current_timestamp(),
            )
        )
        self._validate_character(clean_character)
        self._validate_duplicate_name(clean_character.name, exclude_uuid=character_uuid)

        if not self._repository.update(clean_character):
            raise CharacterNotFoundError(f"Character not found: {character_uuid}")

        self._logger.info("Character updated: %s", character_uuid)
        return clean_character

    def delete_character(self, character_uuid: str) -> bool:
        """Delete an existing character."""
        deleted = self._repository.delete(character_uuid)
        if not deleted:
            raise CharacterNotFoundError(f"Character not found: {character_uuid}")

        self._logger.info("Character deleted: %s", character_uuid)
        return deleted

    def get_character(self, character_uuid: str) -> Character:
        """Return a character by UUID."""
        character = self._repository.get_by_id(character_uuid)
        if character is None:
            raise CharacterNotFoundError(f"Character not found: {character_uuid}")
        return character

    def get_all_characters(self) -> list[Character]:
        """Return all characters."""
        return self._repository.get_all()

    def search_characters(self, search_text: str) -> list[Character]:
        """Search characters by text."""
        return self._repository.search(search_text)

    def character_exists(self, character_uuid: str) -> bool:
        """Return True when a character exists."""
        return self._repository.exists(character_uuid)

    def export_json(self, character_uuid: str) -> dict[str, Any]:
        """Return a structured JSON-ready character object."""
        character = self.get_character(character_uuid)
        payload: dict[str, Any] = {
            "identity": {
                "uuid": character.uuid,
                "name": character.name,
                "species": character.species,
                "gender": character.gender,
                "age_group": character.age_group,
                "description": character.description,
            },
            "appearance": {
                "fur_color": character.fur_color,
                "mane_color": character.mane_color,
                "eye_color": character.eye_color,
                "shirt": character.shirt,
                "pants": character.pants,
                "shoes": character.shoes,
                "accessories": character.accessories,
            },
            "personality": {
                "traits": character.personality,
                "catchphrase": character.catchphrase,
            },
            "voice": {
                "style": character.voice_style,
            },
            "images": {
                "folder": character.image_folder,
            },
        }
        self._logger.info("JSON exported: %s", character_uuid)
        return payload

    def build_prompt(self, character_uuid: str) -> str:
        """Build a reusable AI prompt for a character."""
        character = self.get_character(character_uuid)
        lines = [
            f"Character: {character.name}",
            f"Species: {character.species}",
            f"Gender: {character.gender}",
            f"Age group: {character.age_group}",
            "Appearance:",
            f"- Fur color: {character.fur_color}",
            f"- Mane color: {character.mane_color}",
            f"- Eye color: {character.eye_color}",
            f"- Shirt: {character.shirt}",
            f"- Pants: {character.pants}",
            f"- Shoes: {character.shoes}",
            f"- Accessories: {character.accessories}",
            "Personality:",
            f"- Traits: {character.personality}",
            f"- Catchphrase: {character.catchphrase}",
            "Voice:",
            f"- Style: {character.voice_style}",
            f"Description: {character.description}",
            "Use this character consistently for story, image, thumbnail, voice, and animation generation.",
        ]
        return "\n".join(line for line in lines if not line.endswith(": "))

    def _prepare_character(self, character: Character) -> Character:
        return replace(
            character,
            name=character.name.strip(),
            species=character.species.strip(),
            image_folder=character.image_folder.strip(),
        )

    def _validate_character(self, character: Character) -> None:
        if not character.name:
            self._log_validation_failure("Name is required.")
            raise CharacterValidationError("Name is required.")
        if not character.species:
            self._log_validation_failure("Species is required.")
            raise CharacterValidationError("Species is required.")
        if len(character.description) > self.MAX_DESCRIPTION_LENGTH:
            self._log_validation_failure("Description cannot exceed 500 characters.")
            raise CharacterValidationError("Description cannot exceed 500 characters.")
        if character.image_folder and not Path(character.image_folder).is_dir():
            self._log_validation_failure(f"Image folder does not exist: {character.image_folder}")
            raise CharacterValidationError(f"Image folder does not exist: {character.image_folder}")

    def _validate_duplicate_name(self, name: str, exclude_uuid: str | None = None) -> None:
        normalized_name = name.casefold()
        for existing_character in self._repository.get_all():
            if exclude_uuid and existing_character.uuid == exclude_uuid:
                continue
            if existing_character.name.strip().casefold() == normalized_name:
                self._log_validation_failure(f"Duplicate character name: {name}")
                raise CharacterValidationError(f"Duplicate character name: {name}")

    def _log_validation_failure(self, message: str) -> None:
        self._logger.warning("Validation failure: %s", message)

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
