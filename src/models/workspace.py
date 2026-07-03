"""Workspace context model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


def _current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class Workspace:
    """The active production project context consumed by future agents."""

    uuid: str = field(default_factory=lambda: str(uuid4()))
    project_name: str = ""
    lesson: str = ""
    topic: str = ""
    language: str = "English"
    target_platform: str = "YouTube"
    resolution: str = "1920x1080"
    aspect_ratio: str = "16:9"
    duration: int = 60
    style: str = ""
    current_scene: str = ""
    status: str = "Draft"
    created_at: str = field(default_factory=_current_timestamp)
    updated_at: str = field(default_factory=_current_timestamp)
