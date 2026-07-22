"""Prompt Engine toolbar component."""
from __future__ import annotations

from collections.abc import Callable
import customtkinter as ctk


class PromptToolbar(ctk.CTkFrame):
    """Actions shared by the Prompt Library."""

    def __init__(self, parent: ctk.CTkFrame, on_new: Callable[[], None], on_save: Callable[[], None],
                 on_duplicate: Callable[[], None], on_preview: Callable[[], None], on_export: Callable[[], None]) -> None:
        super().__init__(parent, fg_color="#111827", corner_radius=0)
        for label, command in (("New", on_new), ("Save New Version", on_save), ("Duplicate", on_duplicate),
                               ("Preview", on_preview), ("Export", on_export)):
            ctk.CTkButton(self, text=label, command=command, width=125).pack(side="left", padx=7, pady=10)
