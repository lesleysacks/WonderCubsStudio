"""Controller for Prompt Engine UI actions."""
from __future__ import annotations

from typing import Mapping

from src.models.prompt import Prompt
from src.services.prompt_service import PromptService


class PromptController:
    """Coordinate prompt UI actions with PromptService."""

    def __init__(self, service: PromptService) -> None:
        self._service = service

    def on_new_prompt(self) -> Prompt:
        return Prompt()

    def on_save_prompt(self, prompt: Prompt) -> Prompt:
        return self._service.save_prompt(prompt)

    def on_delete_prompt(self, prompt_id: str) -> bool:
        return self._service.delete_prompt(prompt_id)

    def on_duplicate_prompt(self, prompt_id: str) -> Prompt:
        return self._service.duplicate_prompt(prompt_id)

    def on_search_changed(self, search_text: str) -> list[Prompt]:
        return self._service.get_all_prompts() if not search_text.strip() else self._service.search_prompts(search_text)

    def on_preview_prompt(self, prompt_id: str, values: Mapping[str, object] | None = None,
                          workspace_uuid: str | None = None, character_uuid: str | None = None) -> str:
        return self._service.preview_prompt(prompt_id, values, workspace_uuid, character_uuid)

    def on_activate_version(self, prompt_id: str, version: int) -> Prompt:
        return self._service.activate_version(prompt_id, version)

    def on_export_prompt(self, prompt_id: str, export_format: str, values: Mapping[str, object] | None = None,
                         workspace_uuid: str | None = None, character_uuid: str | None = None) -> str:
        return self._service.export_prompt(prompt_id, export_format, values, workspace_uuid, character_uuid)

    def load_prompts(self) -> list[Prompt]:
        return self._service.get_all_prompts()

    def load_versions(self, prompt_id: str) -> list[Prompt]:
        return self._service.get_versions(prompt_id)
