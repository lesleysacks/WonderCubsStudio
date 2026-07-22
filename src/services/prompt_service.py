"""Prompt Engine business logic."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json
import re
from typing import Mapping
from uuid import uuid4

from src.database.prompt_repository import PromptRepository
from src.models.character import Character
from src.models.prompt import Prompt
from src.models.workspace import Workspace
from src.services.character_service import CharacterService
from src.services.workspace_service import WorkspaceService
from src.utils.logger import get_logger


class PromptValidationError(ValueError):
    """Raised when a prompt fails business validation."""


class PromptNotFoundError(LookupError):
    """Raised when a prompt or version cannot be found."""


class PromptService:
    """Validate, version, render, and export reusable prompt templates."""

    CATEGORIES = {"Story", "Image", "Voice", "Thumbnail", "SEO", "Custom"}
    PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Z][A-Z0-9_]*)\s*}}")
    MALFORMED_PLACEHOLDER_PATTERN = re.compile(r"{{(.*?)}}")
    MAX_NAME_LENGTH = 120

    def __init__(
        self,
        repository: PromptRepository,
        workspace_service: WorkspaceService | None = None,
        character_service: CharacterService | None = None,
    ) -> None:
        self._repository = repository
        self._workspace_service = workspace_service
        self._character_service = character_service
        self._logger = get_logger(__name__)

    def create_prompt(self, prompt: Prompt) -> Prompt:
        clean = self._prepare_prompt(replace(prompt, version=1, active=True))
        self.validate_prompt(clean)
        created = self._repository.create(clean)
        self._logger.info("Prompt created: %s", created.id)
        return created

    def update_prompt(self, prompt_id: str, prompt: Prompt) -> Prompt:
        """Create the next immutable version instead of overwriting a prompt."""
        current = self.get_prompt(prompt_id)
        if prompt.id != prompt_id:
            raise PromptValidationError("Prompt ID cannot be modified.")
        candidate = self._prepare_prompt(replace(
            prompt, version=current.version + 1, created_at=current.created_at,
            updated_at=self._current_timestamp(), active=True,
        ))
        self.validate_prompt(candidate)
        self._repository.deactivate_all(prompt_id)
        try:
            created = self._repository.create(candidate)
        except Exception:
            # Restore the previous usable version if insertion fails.
            self._repository.activate_version(prompt_id, current.version)
            raise
        self._logger.info("Prompt version created: %s v%s", prompt_id, created.version)
        return created

    def save_prompt(self, prompt: Prompt) -> Prompt:
        return self.update_prompt(prompt.id, prompt) if self._repository.exists(prompt.id) else self.create_prompt(prompt)

    def delete_prompt(self, prompt_id: str) -> bool:
        if not self._repository.delete(prompt_id):
            raise PromptNotFoundError(f"Prompt not found: {prompt_id}")
        return True

    def get_prompt(self, prompt_id: str, version: int | None = None) -> Prompt:
        prompt = self._repository.get_by_id(prompt_id, version)
        if prompt is None:
            suffix = f" version {version}" if version is not None else ""
            raise PromptNotFoundError(f"Prompt not found: {prompt_id}{suffix}")
        return prompt

    def get_all_prompts(self) -> list[Prompt]:
        return self._repository.get_all_active()

    def get_versions(self, prompt_id: str) -> list[Prompt]:
        versions = self._repository.get_versions(prompt_id)
        if not versions:
            raise PromptNotFoundError(f"Prompt not found: {prompt_id}")
        return versions

    def search_prompts(self, search_text: str) -> list[Prompt]:
        return self._repository.search(search_text)

    def duplicate_prompt(self, prompt_id: str) -> Prompt:
        source = self.get_prompt(prompt_id)
        duplicate = replace(source, id=str(uuid4()), name=self._duplicate_name(source.name), version=1,
                            created_at=self._current_timestamp(), updated_at=self._current_timestamp(), active=True)
        return self.create_prompt(duplicate)

    def activate_version(self, prompt_id: str, version: int) -> Prompt:
        self.get_prompt(prompt_id, version)
        self._repository.deactivate_all(prompt_id)
        if not self._repository.activate_version(prompt_id, version):
            raise PromptNotFoundError(f"Prompt not found: {prompt_id} version {version}")
        return self.get_prompt(prompt_id)

    def validate_prompt(self, prompt: Prompt) -> bool:
        if not prompt.name:
            raise PromptValidationError("Name is required.")
        if len(prompt.name) > self.MAX_NAME_LENGTH:
            raise PromptValidationError("Name cannot exceed 120 characters.")
        if prompt.category not in self.CATEGORIES:
            raise PromptValidationError("Category is invalid.")
        if not prompt.template:
            raise PromptValidationError("Template is required.")
        self.validate_placeholders(prompt.template, prompt.variables)
        return True

    def validate_placeholders(self, template: str, variables: tuple[str, ...] | list[str] = ()) -> tuple[str, ...]:
        """Ensure placeholder syntax is valid and declared variables match the template."""
        found = tuple(dict.fromkeys(self.PLACEHOLDER_PATTERN.findall(template)))
        malformed = [match.group(1) for match in self.MALFORMED_PLACEHOLDER_PATTERN.finditer(template)
                     if not self.PLACEHOLDER_PATTERN.fullmatch(match.group(0))]
        if malformed or "{{" in self.PLACEHOLDER_PATTERN.sub("", template) or "}}" in self.PLACEHOLDER_PATTERN.sub("", template):
            raise PromptValidationError("Template contains an invalid placeholder.")
        declared = tuple(variable.strip().upper() for variable in variables if variable.strip())
        if declared and set(declared) != set(found):
            raise PromptValidationError("Declared variables must match template placeholders.")
        return found

    def replace_variables(self, template: str, values: Mapping[str, object]) -> str:
        placeholders = self.validate_placeholders(template)
        normalized = {str(key).upper(): str(value) for key, value in values.items() if value is not None}
        missing = [placeholder for placeholder in placeholders if not normalized.get(placeholder, "").strip()]
        if missing:
            raise PromptValidationError(f"Missing values for: {', '.join(missing)}")
        return self.PLACEHOLDER_PATTERN.sub(lambda match: normalized[match.group(1)], template)

    def preview_prompt(self, prompt_id: str, values: Mapping[str, object] | None = None,
                       workspace_uuid: str | None = None, character_uuid: str | None = None) -> str:
        return self.build_prompt(prompt_id, values, workspace_uuid, character_uuid)

    def build_prompt(self, prompt_id: str, values: Mapping[str, object] | None = None,
                     workspace_uuid: str | None = None, character_uuid: str | None = None) -> str:
        prompt = self.get_prompt(prompt_id)
        context = self._build_context(workspace_uuid, character_uuid)
        context.update({str(key).upper(): value for key, value in (values or {}).items()})
        return self.replace_variables(prompt.template, context)

    def export_prompt(self, prompt_id: str, export_format: str = "json", values: Mapping[str, object] | None = None,
                      workspace_uuid: str | None = None, character_uuid: str | None = None) -> str:
        prompt = self.get_prompt(prompt_id)
        rendered = self.build_prompt(prompt_id, values, workspace_uuid, character_uuid)
        export_format = export_format.lower()
        if export_format == "json":
            return json.dumps({"prompt": self._as_dict(prompt), "rendered_prompt": rendered}, indent=2)
        if export_format == "txt":
            return rendered
        if export_format in {"md", "markdown"}:
            return f"# {prompt.name}\n\n**Category:** {prompt.category}  \n**Version:** {prompt.version}\n\n{rendered}\n"
        raise PromptValidationError("Export format must be JSON, TXT, or Markdown.")

    def _build_context(self, workspace_uuid: str | None, character_uuid: str | None) -> dict[str, object]:
        context: dict[str, object] = {}
        workspace: Workspace | None = None
        if self._workspace_service is not None:
            try:
                workspace = self._workspace_service.load_workspace(workspace_uuid) if workspace_uuid else self._workspace_service.get_active_workspace()
            except LookupError:
                workspace = None
        if workspace is not None:
            context.update({"PROJECT_NAME": workspace.project_name, "LESSON": workspace.lesson,
                            "STYLE": workspace.style, "LANGUAGE": workspace.language,
                            "SCENE_NUMBER": workspace.current_scene, "BACKGROUND": workspace.topic})
        if character_uuid and self._character_service is not None:
            character: Character = self._character_service.get_character(character_uuid)
            context.update({"CHARACTER_NAME": character.name, "VOICE_STYLE": character.voice_style,
                            "AGE_GROUP": character.age_group})
        return context

    def _prepare_prompt(self, prompt: Prompt) -> Prompt:
        variables = self.validate_placeholders(prompt.template, prompt.variables)
        return replace(prompt, name=prompt.name.strip(), category=prompt.category.strip(),
                       description=prompt.description.strip(), template=prompt.template.strip(), variables=variables)

    def _duplicate_name(self, name: str) -> str:
        names = {prompt.name.casefold() for prompt in self.get_all_prompts()}
        base, candidate, index = f"{name} Copy", f"{name} Copy", 2
        while candidate.casefold() in names:
            candidate = f"{base} {index}"
            index += 1
        return candidate

    @staticmethod
    def _as_dict(prompt: Prompt) -> dict[str, object]:
        return {"id": prompt.id, "name": prompt.name, "category": prompt.category, "version": prompt.version,
                "description": prompt.description, "template": prompt.template, "variables": list(prompt.variables),
                "created_at": prompt.created_at, "updated_at": prompt.updated_at, "active": prompt.active}

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
