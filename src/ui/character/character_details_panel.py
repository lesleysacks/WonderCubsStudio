"""Character details editing panel."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.models.character import Character


class CharacterDetailsPanel(ctk.CTkFrame):
    """Edit character identity, appearance, voice, and personality fields."""

    FIELD_NAMES = (
        "name",
        "species",
        "gender",
        "age_group",
        "fur_color",
        "mane_color",
        "eye_color",
        "shirt",
        "pants",
        "shoes",
        "accessories",
        "voice_style",
        "personality",
        "catchphrase",
    )

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_save: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(parent, corner_radius=10, fg_color="#172033")
        self._current_character = Character()
        self._entries: dict[str, ctk.CTkEntry] = {}
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Character Details", font=("Segoe UI", 20, "bold"), anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(16, 10)
        )

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=14, pady=(0, 10))
        form.grid_columnconfigure((0, 1), weight=1)

        for index, field_name in enumerate(self.FIELD_NAMES):
            column = index % 2
            row = (index // 2) * 2
            label = field_name.replace("_", " ").title()
            ctk.CTkLabel(form, text=label, anchor="w", text_color="#cbd5e1").grid(
                row=row, column=column, sticky="w", padx=6, pady=(7, 2)
            )
            entry = ctk.CTkEntry(form)
            entry.grid(row=row + 1, column=column, sticky="ew", padx=6, pady=(0, 5))
            self._entries[field_name] = entry

        description_row = ((len(self.FIELD_NAMES) + 1) // 2) * 2
        ctk.CTkLabel(form, text="Description", anchor="w", text_color="#cbd5e1").grid(
            row=description_row, column=0, columnspan=2, sticky="w", padx=6, pady=(8, 2)
        )
        self._description = ctk.CTkTextbox(form, height=110)
        self._description.grid(row=description_row + 1, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 8))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 16))
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(buttons, text="Save", command=on_save, height=38).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(buttons, text="Cancel", command=on_cancel, height=38, fg_color="#475569", hover_color="#334155").grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

    def set_character(self, character: Character) -> None:
        """Populate the form with a character."""
        self._current_character = character
        for field_name, entry in self._entries.items():
            entry.delete(0, "end")
            entry.insert(0, getattr(character, field_name))
        self._description.delete("1.0", "end")
        self._description.insert("1.0", character.description)

    def get_character(self, image_folder: str) -> Character:
        """Build a Character from the form while preserving metadata."""
        values = {field_name: entry.get() for field_name, entry in self._entries.items()}
        return Character(
            uuid=self._current_character.uuid,
            name=values["name"],
            species=values["species"],
            gender=values["gender"],
            age_group=values["age_group"],
            fur_color=values["fur_color"],
            mane_color=values["mane_color"],
            eye_color=values["eye_color"],
            shirt=values["shirt"],
            pants=values["pants"],
            shoes=values["shoes"],
            accessories=values["accessories"],
            personality=values["personality"],
            voice_style=values["voice_style"],
            catchphrase=values["catchphrase"],
            description=self._description.get("1.0", "end").strip(),
            image_folder=image_folder,
            created_at=self._current_character.created_at,
            updated_at=self._current_character.updated_at,
        )
