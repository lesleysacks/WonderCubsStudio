"""Project model."""
from __future__ import annotations

from dataclasses import dataclass


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
