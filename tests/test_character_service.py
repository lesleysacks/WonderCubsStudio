"""Tests for character business logic."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.database.character_repository import CharacterRepository
from src.database.schema import initialize_database
from src.models.character import Character
from src.services.character_service import CharacterService, CharacterValidationError


def test_create_valid_character(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    character = _make_character(tmp_path, name=" Leo ")

    created = service.create_character(character)

    assert created.name == "Leo"
    assert service.character_exists(created.uuid) is True
    assert service.get_character(created.uuid) == created


def test_create_character_requires_name(tmp_path: Path) -> None:
    service = _make_service(tmp_path)

    with pytest.raises(CharacterValidationError, match="Name is required"):
        service.create_character(_make_character(tmp_path, name="   "))


def test_create_character_requires_species(tmp_path: Path) -> None:
    service = _make_service(tmp_path)

    with pytest.raises(CharacterValidationError, match="Species is required"):
        service.create_character(_make_character(tmp_path, species=""))


def test_create_character_rejects_duplicate_name(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    service.create_character(_make_character(tmp_path, uuid="leo-1", name="Leo"))

    with pytest.raises(CharacterValidationError, match="Duplicate character name"):
        service.create_character(_make_character(tmp_path, uuid="leo-2", name=" leo "))


def test_create_character_rejects_long_description(tmp_path: Path) -> None:
    service = _make_service(tmp_path)

    with pytest.raises(CharacterValidationError, match="Description cannot exceed 500 characters"):
        service.create_character(_make_character(tmp_path, description="x" * 501))


def test_update_character_rejects_uuid_changes(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    character = service.create_character(_make_character(tmp_path, uuid="leo-1"))
    changed_uuid = replace(character, uuid="leo-2")

    with pytest.raises(CharacterValidationError, match="UUID cannot be modified"):
        service.update_character(character.uuid, changed_uuid)


def test_export_json_returns_structured_character_payload(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    character = service.create_character(_make_character(tmp_path))

    payload = service.export_json(character.uuid)

    assert payload["identity"]["name"] == "Leo"
    assert payload["identity"]["species"] == "Lion"
    assert payload["appearance"]["fur_color"] == "Golden"
    assert payload["personality"]["catchphrase"] == "Wonder time!"
    assert payload["voice"]["style"] == "Warm and playful"
    assert payload["images"]["folder"] == character.image_folder


def test_build_prompt_returns_reusable_character_description(tmp_path: Path) -> None:
    service = _make_service(tmp_path)
    character = service.create_character(_make_character(tmp_path))

    prompt = service.build_prompt(character.uuid)

    assert "Character: Leo" in prompt
    assert "Species: Lion" in prompt
    assert "Fur color: Golden" in prompt
    assert "Catchphrase: Wonder time!" in prompt
    assert "story, image, thumbnail, voice, and animation generation" in prompt


def _make_service(tmp_path: Path) -> CharacterService:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)
    return CharacterService(CharacterRepository(database_file))


def _make_character(
    tmp_path: Path,
    uuid: str = "leo-uuid",
    name: str = "Leo",
    species: str = "Lion",
    description: str = "Leo is a reusable WonderCubs character.",
) -> Character:
    image_folder = tmp_path / "assets" / "characters" / name.strip().lower()
    image_folder.mkdir(parents=True, exist_ok=True)
    return Character(
        uuid=uuid,
        name=name,
        species=species,
        gender="Male",
        age_group="Cub",
        fur_color="Golden",
        mane_color="Brown",
        eye_color="Amber",
        shirt="Blue T-shirt",
        pants="Red shorts",
        shoes="White sneakers",
        accessories="Backpack",
        personality="Friendly teacher",
        voice_style="Warm and playful",
        catchphrase="Wonder time!",
        description=description,
        image_folder=str(image_folder),
        created_at="2026-07-01 09:00:00",
        updated_at="2026-07-01 09:00:00",
    )
