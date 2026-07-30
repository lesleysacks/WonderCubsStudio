"""Project lifecycle domain model."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProjectStatus(str, Enum):
    """Official project lifecycle values persisted by the application."""

    DRAFT = "Draft"
    IN_PRODUCTION = "In Production"
    REVIEW = "Review"
    READY_TO_PUBLISH = "Ready to Publish"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(status.value for status in cls)

    @classmethod
    def parse(cls, value: str | "ProjectStatus") -> "ProjectStatus":
        if isinstance(value, cls):
            return value
        try:
            return cls(value.strip())
        except (AttributeError, ValueError) as error:
            raise ValueError(f"Invalid project status: {value!r}") from error


@dataclass(frozen=True)
class Project:
    """A WonderCubs video project."""

    id: int | None
    video_number: str
    title: str
    lesson: str
    status: str
    created_at: str
    folder_path: str
    updated_at: str = ""
    published_at: str | None = None
