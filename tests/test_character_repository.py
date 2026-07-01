"""Tests for character persistence."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3

import pytest

from src.database.character_repository import CharacterRepository
from src.database.schema import initialize_database
from src.models.character import Character


def test_initialize_database_creates_characters_table_without_affecting_existing_tables(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)

    with sqlite3.connect(database_file) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "Characters" in tables
    assert "Projects" in tables
    assert "Goals" in tables


def test_character_repository_create_get_all_search_exists_update_and_delete(tmp_path: Path) -> None:
    database_file = tmp_path / "database.db"
    initialize_database(database_file)
    repository = CharacterRepository(database_file)

    leo = _make_character(name="Leo", species="Lion", personality="Kind and brave")
    mia = _make_character(name="Mia", species="Bear", personality="Curious problem solver")

    repository.create(mia)
    repository.create(leo)

    assert repository.exists(leo.uuid) is True
    assert repository.get_by_id(leo.uuid) == leo
    assert [character.name for character in repository.get_all()] == ["Leo", "Mia"]
    assert repository.search("brave") == [leo]
    assert repository.search("bear") == [mia]

    updated_leo = replace(leo, catchphrase="Let's learn together!", updated_at="2026-07-01 10:00:00")
    assert repository.update(updated_leo) is True
    assert repository.get_by_id(leo.uuid) == updated_leo

    assert repository.delete(leo.uuid) is True
    assert repository.exists(leo.uuid) is False
    assert repository.get_by_id(leo.uuid) is None
    assert repository.delete(leo.uuid) is False


def test_character_repository_raises_sqlite_errors(tmp_path: Path) -> None:
    database_file = tmp_path / "missing-schema.db"
    repository = CharacterRepository(database_file)

    with pytest.raises(sqlite3.Error):
        repository.create(_make_character())


def _make_character(
    name: str = "Leo",
    species: str = "Lion",
    personality: str = "Friendly teacher",
) -> Character:
    return Character(
        uuid=f"{name.lower()}-uuid",
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
        personality=personality,
        voice_style="Warm and playful",
        catchphrase="Wonder time!",
        description=f"{name} is a reusable WonderCubs character.",
        image_folder=f"assets/characters/{name.lower()}",
        created_at="2026-07-01 09:00:00",
        updated_at="2026-07-01 09:00:00",
    )
