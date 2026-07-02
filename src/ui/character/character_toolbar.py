"""Top toolbar for the Character Workspace."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk


class CharacterToolbar(ctk.CTkFrame):
    """Render workspace-level character actions."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_new: Callable[[], None],
        on_save: Callable[[], None],
        on_duplicate: Callable[[], None],
        on_export: Callable[[], None],
        on_refresh: Callable[[], None],
    ) -> None:
        super().__init__(parent, corner_radius=0, fg_color="#111827")
        self.grid_columnconfigure(5, weight=1)
        actions = (
            ("New Character", on_new),
            ("Save", on_save),
            ("Duplicate", on_duplicate),
            ("Export JSON", on_export),
            ("Refresh", on_refresh),
        )
        for column, (label, command) in enumerate(actions):
            ctk.CTkButton(
                self,
                text=label,
                command=command,
                height=36,
                corner_radius=8,
                font=("Segoe UI", 13, "bold"),
            ).grid(row=0, column=column, padx=(12 if column == 0 else 4, 4), pady=12)
