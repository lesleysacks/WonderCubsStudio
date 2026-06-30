"""Application settings model."""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class AppSettings:
    """User-editable application settings."""

    default_project_folder: str
    default_resolution: str
    default_fps: int
    author_name: str
    channel_name: str

    def to_dict(self) -> dict[str, object]:
        """Convert settings to a JSON-serializable dictionary."""
        return asdict(self)
