"""Prompt Engine regression and unit tests."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.controllers.prompt_controller import PromptController
from src.database.prompt_repository import PromptRepository
from src.database.schema import initialize_database
from src.database.workspace_repository import WorkspaceRepository
from src.database.character_repository import CharacterRepository
from src.models.character import Character
from src.models.prompt import Prompt
from src.models.workspace import Workspace
from src.services.character_service import CharacterService
from src.services.prompt_service import PromptService, PromptValidationError
from src.services.workspace_service import WorkspaceService


def test_prompt_crud_and_search(tmp_path: Path) -> None:
    service = _service(tmp_path)
    created = service.create_prompt(_prompt(name="Colour Story", category="Story"))

    assert service.get_prompt(created.id).variables == ("PROJECT_NAME", "LESSON")
    assert [item.id for item in service.search_prompts("colour")] == [created.id]
    assert service.delete_prompt(created.id) is True
    assert service.get_all_prompts() == []


@pytest.mark.parametrize("prompt, message", [
    (_prompt(name="", template="Hello"), "Name is required"),
    (_prompt(category="Wrong"), "Category is invalid"),
    (_prompt(template=""), "Template is required"),
    (_prompt(template="Hello {{project_name}}"), "invalid placeholder"),
    (_prompt(variables=("LESSON",)), "Declared variables must match"),
])
def test_prompt_validation(tmp_path: Path, prompt: Prompt, message: str) -> None:
    with pytest.raises(PromptValidationError, match=message):
        _service(tmp_path).create_prompt(prompt)


def test_variable_replacement_preview_and_exports(tmp_path: Path) -> None:
    service = _service(tmp_path)
    prompt = service.create_prompt(_prompt(template="{{PROJECT_NAME}} teaches {{LESSON}}."))

    preview = service.preview_prompt(prompt.id, {"PROJECT_NAME": "WonderCubs", "LESSON": "Colours"})

    assert preview == "WonderCubs teaches Colours."
    assert "rendered_prompt" in service.export_prompt(prompt.id, "json", {"PROJECT_NAME": "WonderCubs", "LESSON": "Colours"})
    assert service.export_prompt(prompt.id, "txt", {"PROJECT_NAME": "WonderCubs", "LESSON": "Colours"}) == preview
    assert "# Colour Story" in service.export_prompt(prompt.id, "markdown", {"PROJECT_NAME": "WonderCubs", "LESSON": "Colours"})


def test_prompt_builds_values_from_workspace_and_character_context(tmp_path: Path) -> None:
    database_file = tmp_path / "context.db"
    initialize_database(database_file)
    workspaces = WorkspaceService(WorkspaceRepository(database_file))
    characters = CharacterService(CharacterRepository(database_file))
    workspace = workspaces.create_workspace(Workspace(
        uuid="workspace", project_name="WonderCubs", lesson="Colours", topic="Playroom",
        language="English", style="Watercolour", current_scene="3",
    ))
    character = characters.create_character(Character(uuid="character", name="Leo", species="Lion", age_group="Cub", voice_style="Warm"))
    service = PromptService(PromptRepository(database_file), workspaces, characters)
    prompt = service.create_prompt(_prompt(template="{{PROJECT_NAME}} {{CHARACTER_NAME}} {{SCENE_NUMBER}} {{BACKGROUND}}"))

    assert service.build_prompt(prompt.id, workspace_uuid=workspace.uuid, character_uuid=character.uuid) == "WonderCubs Leo 3 Playroom"


def test_edits_create_immutable_versions_and_activation(tmp_path: Path) -> None:
    service = _service(tmp_path)
    original = service.create_prompt(_prompt())
    version_two = service.update_prompt(original.id, replace(original, template="New {{PROJECT_NAME}} {{LESSON}}"))

    assert original.version == 1
    assert version_two.version == 2
    assert service.get_prompt(original.id).version == 2
    assert service.get_prompt(original.id, 1).active is False
    active = service.activate_version(original.id, 1)
    assert active.version == 1
    assert service.get_prompt(original.id, 2).active is False


def test_duplicate_creates_new_prompt_family(tmp_path: Path) -> None:
    service = _service(tmp_path)
    original = service.create_prompt(_prompt())
    duplicate = service.duplicate_prompt(original.id)
    assert duplicate.id != original.id
    assert duplicate.version == 1
    assert duplicate.name == "Colour Story Copy"


def test_controller_actions_delegate_to_service(tmp_path: Path) -> None:
    controller = PromptController(_service(tmp_path))
    saved = controller.on_save_prompt(_prompt())
    version_two = controller.on_save_prompt(replace(saved, description="Edited"))
    assert controller.on_search_changed("colour")[0].version == 2
    assert controller.on_activate_version(saved.id, 1).version == 1
    assert controller.on_delete_prompt(saved.id) is True


def _service(tmp_path: Path) -> PromptService:
    database_file = tmp_path / "prompts.db"
    initialize_database(database_file)
    return PromptService(PromptRepository(database_file))


def _prompt(name: str = "Colour Story", category: str = "Story", template: str = "Create {{PROJECT_NAME}} lesson {{LESSON}}.", variables: tuple[str, ...] = ()) -> Prompt:
    return Prompt(id="prompt-id", name=name, category=category, description="A lesson prompt", template=template,
                  variables=variables, created_at="2026-07-22 10:00:00", updated_at="2026-07-22 10:00:00")
