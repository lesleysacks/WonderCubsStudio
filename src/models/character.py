"""Character model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


def _current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class Character:
    """A reusable WonderCubs character profile."""

    uuid: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    species: str = ""
    gender: str = ""
    age_group: str = ""
    fur_color: str = ""
    mane_color: str = ""
    eye_color: str = ""
    shirt: str = ""
    pants: str = ""
    shoes: str = ""
    accessories: str = ""
    personality: str = ""
    voice_style: str = ""
    catchphrase: str = ""
    description: str = ""
    image_folder: str = ""
    created_at: str = field(default_factory=_current_timestamp)
    updated_at: str = field(default_factory=_current_timestamp)
