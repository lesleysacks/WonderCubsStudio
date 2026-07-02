"""Character list panel."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.models.character import Character


class CharacterListPanel(ctk.CTkFrame):
    """Search and select characters."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_search: Callable[[str], None],
        on_select: Callable[[Character], None],
        on_add: Callable[[], None],
        on_duplicate: Callable[[], None],
        on_delete: Callable[[], None],
    ) -> None:
        super().__init__(parent, corner_radius=10, fg_color="#172033")
        self._on_search = on_search
        self._on_select = on_select
        self._characters: list[Character] = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Characters", font=("Segoe UI", 20, "bold"), anchor="w").grid(
            row=0, column=0, sticky="ew", padx=16, pady=(16, 8)
        )
        self._search_entry = ctk.CTkEntry(self, placeholder_text="Search characters")
        self._search_entry.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._search_entry.bind("<KeyRelease>", self._handle_search)

        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="#0f172a", corner_radius=8)
        self._list_frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 12))
        self._list_frame.grid_columnconfigure(0, weight=1)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))
        actions.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(actions, text="Add", command=on_add, height=34).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(actions, text="Duplicate", command=on_duplicate, height=34).grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkButton(actions, text="Delete", command=on_delete, height=34, fg_color="#b91c1c", hover_color="#991b1b").grid(
            row=0, column=2, sticky="ew", padx=(4, 0)
        )

    def set_characters(self, characters: list[Character], selected_uuid: str | None = None) -> None:
        """Render the current character list."""
        self._characters = characters
        for widget in self._list_frame.winfo_children():
            widget.destroy()
        if not characters:
            ctk.CTkLabel(self._list_frame, text="No characters found.", text_color="#94a3b8").grid(
                row=0, column=0, sticky="w", padx=12, pady=12
            )
            return
        for row, character in enumerate(characters):
            selected = character.uuid == selected_uuid
            button = ctk.CTkButton(
                self._list_frame,
                text=f"{character.name}\n{character.species}",
                command=lambda selected_character=character: self._on_select(selected_character),
                anchor="w",
                height=54,
                corner_radius=8,
                fg_color="#2563eb" if selected else "transparent",
                hover_color="#1f2937",
            )
            button.grid(row=row, column=0, sticky="ew", padx=6, pady=4)

    def _handle_search(self, _event: object) -> None:
        self._on_search(self._search_entry.get())
