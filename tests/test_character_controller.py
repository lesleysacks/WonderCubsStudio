"""Smoke tests for Character Workspace controller actions."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from src.controllers.character_controller import CharacterController
from src.models.character import Character


def test_character_loads_correctly() -> None:
    service = FakeCharacterService([_make_character()])
    controller = CharacterController(service)  # type: ignore[arg-type]

    characters = controller.load_characters()

    assert [character.name for character in characters] == ["Leo"]


def test_save_button_flow_calls_character_service() -> None:
    service = FakeCharacterService()
    controller = CharacterController(service)  # type: ignore[arg-type]

    character = _make_character()
    saved = controller.on_save_character(character)
    updated = controller.on_save_character(replace(saved, species="Tiger"))

    assert service.created == [character.uuid]
    assert service.updated == [character.uuid]
    assert updated.species == "Tiger"


def test_search_updates_character_list() -> None:
    service = FakeCharacterService([
        _make_character(name="Leo", species="Lion"),
        _make_character(uuid="mia-uuid", name="Mia", species="Bear"),
    ])
    controller = CharacterController(service)  # type: ignore[arg-type]

    assert [character.name for character in controller.on_search_changed("bear")] == ["Mia"]
    assert [character.name for character in controller.on_search_changed("")] == ["Leo", "Mia"]


def test_duplicate_creates_new_character() -> None:
    service = FakeCharacterService([_make_character()])
    controller = CharacterController(service)  # type: ignore[arg-type]

    duplicate = controller.on_duplicate_character("leo-uuid")

    assert duplicate.uuid != "leo-uuid"
    assert duplicate.name == "Leo Copy"
    assert service.created == [duplicate.uuid]


def test_delete_removes_character() -> None:
    service = FakeCharacterService([_make_character()])
    controller = CharacterController(service)  # type: ignore[arg-type]

    assert controller.on_delete_character("leo-uuid") is True

    assert service.deleted == ["leo-uuid"]
    assert service.get_all_characters() == []


def test_export_json_button_flow_calls_character_service() -> None:
    service = FakeCharacterService([_make_character()])
    controller = CharacterController(service)  # type: ignore[arg-type]

    payload = controller.on_export_character("leo-uuid")

    assert payload["identity"]["name"] == "Leo"
    assert service.exported == ["leo-uuid"]


class FakeCharacterService:
    """Small service fake for UI action smoke tests."""

    def __init__(self, characters: list[Character] | None = None) -> None:
        self._characters = {character.uuid: character for character in characters or []}
        self.created: list[str] = []
        self.updated: list[str] = []
        self.deleted: list[str] = []
        self.exported: list[str] = []

    def character_exists(self, character_uuid: str) -> bool:
        return character_uuid in self._characters

    def create_character(self, character: Character) -> Character:
        self.created.append(character.uuid)
        self._characters[character.uuid] = character
        return character

    def update_character(self, character_uuid: str, character: Character) -> Character:
        self.updated.append(character_uuid)
        self._characters[character_uuid] = character
        return character

    def delete_character(self, character_uuid: str) -> bool:
        self.deleted.append(character_uuid)
        del self._characters[character_uuid]
        return True

    def get_character(self, character_uuid: str) -> Character:
        return self._characters[character_uuid]

    def get_all_characters(self) -> list[Character]:
        return sorted(self._characters.values(), key=lambda character: character.name)

    def search_characters(self, search_text: str) -> list[Character]:
        search_value = search_text.casefold()
        return [
            character
            for character in self.get_all_characters()
            if search_value in character.name.casefold() or search_value in character.species.casefold()
        ]

    def export_json(self, character_uuid: str) -> dict[str, Any]:
        self.exported.append(character_uuid)
        character = self._characters[character_uuid]
        return {"identity": {"uuid": character.uuid, "name": character.name}}


def _make_character(
    uuid: str = "leo-uuid",
    name: str = "Leo",
    species: str = "Lion",
) -> Character:
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
        description=f"{name} is a reusable WonderCubs character.",
        image_folder="",
        created_at="2026-07-01 09:00:00",
        updated_at="2026-07-01 09:00:00",
    )
