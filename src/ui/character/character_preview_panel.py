"""Character image preview panel."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import tkinter as tk

import customtkinter as ctk


class CharacterPreviewPanel(ctk.CTkFrame):
    """Show required character image placeholders and browse actions."""

    IMAGE_FILES = ("Front.png", "Side.png", "Back.png", "Portrait.png")

    def __init__(self, parent: ctk.CTkFrame, on_browse: Callable[[str], None]) -> None:
        super().__init__(parent, corner_radius=10, fg_color="#172033")
        self._on_browse = on_browse
        self._image_folder = ""
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._images: dict[str, tk.PhotoImage] = {}
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Character Preview", font=("Segoe UI", 20, "bold"), anchor="w").grid(
            row=0, column=0, sticky="ew", padx=16, pady=(16, 10)
        )
        ctk.CTkLabel(self, text="Image Folder", anchor="w", text_color="#cbd5e1").grid(
            row=1, column=0, sticky="w", padx=16, pady=(0, 2)
        )
        self._folder_label = ctk.CTkLabel(self, text="No folder selected", anchor="w", text_color="#94a3b8", wraplength=220)
        self._folder_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        for row, file_name in enumerate(self.IMAGE_FILES, start=3):
            item = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=8)
            item.grid(row=row, column=0, sticky="ew", padx=14, pady=6)
            item.grid_columnconfigure(0, weight=1)
            label = ctk.CTkLabel(item, text=f"{file_name}\nMissing", height=96, anchor="center", text_color="#94a3b8")
            label.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
            ctk.CTkButton(item, text="Browse", command=lambda selected=file_name: self._on_browse(selected), height=30).grid(
                row=1, column=0, sticky="ew", padx=8, pady=(0, 8)
            )
            self._labels[file_name] = label

    def set_image_folder(self, image_folder: str) -> None:
        """Load previews from an image folder."""
        self._image_folder = image_folder
        self._folder_label.configure(text=image_folder or "No folder selected")
        self._images.clear()
        folder = Path(image_folder) if image_folder else None
        for file_name, label in self._labels.items():
            image_path = folder / file_name if folder else None
            if image_path and image_path.is_file():
                try:
                    image = tk.PhotoImage(file=str(image_path))
                    self._images[file_name] = image
                    label.configure(text="", image=image)
                except tk.TclError:
                    label.configure(text=f"{file_name}\nFound", image=None, text_color="#dbeafe")
            else:
                label.configure(text=f"{file_name}\nMissing", image=None, text_color="#94a3b8")

    def get_image_folder(self) -> str:
        """Return the selected image folder."""
        return self._image_folder
