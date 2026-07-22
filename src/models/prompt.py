"""Prompt Engine domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


def _current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class Prompt:
    """A versioned, reusable structured prompt template."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    category: str = "Custom"
    version: int = 1
    description: str = ""
    template: str = ""
    variables: tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_current_timestamp)
    updated_at: str = field(default_factory=_current_timestamp)
    active: bool = True
