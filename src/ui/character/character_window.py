"""Character Workspace frame."""
from __future__ import annotations

import json
from pathlib import Path
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

import customtkinter as ctk

from src.controllers.character_controller import CharacterController
from src.models.character import Character
from src.services.character_service import CharacterNotFoundError, CharacterValidationError
from src.ui.character.character_details_panel import CharacterDetailsPanel
from src.ui.character.character_list_panel import CharacterListPanel
from src.ui.character.character_preview_panel import CharacterPreviewPanel
from src.ui.character.character_toolbar import CharacterToolbar


class CharacterWindow(ctk.CTkFrame):
    """Modular Character Workspace."""

    def __init__(self, parent: ctk.CTkFrame, controller: CharacterController) -> None:
        super().__init__(parent, corner_radius=0, fg_color="#0b1120")
        self._controller = controller
        self._characters: list[Character] = []
        self._selected_character: Character | None = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        self.refresh()

    def refresh(self) -> None:
        """Reload characters from the controller."""
        try:
            self._characters = self._controller.load_characters()
            selected_uuid = self._selected_character.uuid if self._selected_character else None
            self._list_panel.set_characters(self._characters, selected_uuid)
            if self._selected_character is None and self._characters:
                self._select_character(self._characters[0])
        except Exception as error:
            self._show_error("Could not load characters", error)

    def _build(self) -> None:
        self._toolbar = CharacterToolbar(
            self,
            on_new=self._new_character,
            on_save=self._save_character,
            on_duplicate=self._duplicate_character,
            on_export=self._export_character,
            on_refresh=self.refresh,
        )
        self._toolbar.grid(row=0, column=0, sticky="ew")

        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        workspace.grid_columnconfigure(0, weight=1, minsize=230)
        workspace.grid_columnconfigure(1, weight=3, minsize=420)
        workspace.grid_columnconfigure(2, weight=1, minsize=260)
        workspace.grid_rowconfigure(0, weight=1)

        self._list_panel = CharacterListPanel(
            workspace,
            on_search=self._search_characters,
            on_select=self._select_character,
            on_add=self._new_character,
            on_duplicate=self._duplicate_character,
            on_delete=self._delete_character,
        )
        self._list_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self._details_panel = CharacterDetailsPanel(
            workspace,
            on_save=self._save_character,
            on_cancel=self._cancel_edit,
        )
        self._details_panel.grid(row=0, column=1, sticky="nsew", padx=6)

        self._preview_panel = CharacterPreviewPanel(workspace, on_browse=self._browse_image)
        self._preview_panel.grid(row=0, column=2, sticky="nsew", padx=(12, 0))

    def _new_character(self) -> None:
        character = self._controller.on_new_character()
        self._selected_character = character
        self._details_panel.set_character(character)
        self._preview_panel.set_image_folder(character.image_folder)
        self._list_panel.set_characters(self._characters)

    def _select_character(self, character: Character) -> None:
        self._selected_character = character
        self._details_panel.set_character(character)
        self._preview_panel.set_image_folder(character.image_folder)
        self._list_panel.set_characters(self._characters, character.uuid)

    def _save_character(self) -> None:
        try:
            character = self._details_panel.get_character(self._preview_panel.get_image_folder())
            saved = self._controller.on_save_character(character)
            self._selected_character = saved
            self.refresh()
            messagebox.showinfo("Character Saved", f"Saved character: {saved.name}")
        except (CharacterValidationError, CharacterNotFoundError) as error:
            messagebox.showerror("Character Error", str(error))
        except Exception as error:
            self._show_error("Could not save character", error)

    def _delete_character(self) -> None:
        if self._selected_character is None:
            messagebox.showinfo("Delete Character", "Select a character to delete.")
            return
        if not messagebox.askyesno("Delete Character", f"Delete {self._selected_character.name}?"):
            return
        try:
            self._controller.on_delete_character(self._selected_character.uuid)
            self._selected_character = None
            self._new_character()
            self.refresh()
        except (CharacterValidationError, CharacterNotFoundError) as error:
            messagebox.showerror("Character Error", str(error))
        except Exception as error:
            self._show_error("Could not delete character", error)

    def _duplicate_character(self) -> None:
        if self._selected_character is None:
            messagebox.showinfo("Duplicate Character", "Select a character to duplicate.")
            return
        try:
            duplicated = self._controller.on_duplicate_character(self._selected_character.uuid)
            self._selected_character = duplicated
            self.refresh()
            self._select_character(duplicated)
        except (CharacterValidationError, CharacterNotFoundError) as error:
            messagebox.showerror("Character Error", str(error))
        except Exception as error:
            self._show_error("Could not duplicate character", error)

    def _export_character(self) -> None:
        if self._selected_character is None:
            messagebox.showinfo("Export JSON", "Select a character to export.")
            return
        try:
            payload = self._controller.on_export_character(self._selected_character.uuid)
            messagebox.showinfo("Export JSON", json.dumps(payload, indent=2))
        except (CharacterValidationError, CharacterNotFoundError) as error:
            messagebox.showerror("Character Error", str(error))
        except Exception as error:
            self._show_error("Could not export character", error)

    def _search_characters(self, search_text: str) -> None:
        try:
            self._characters = self._controller.on_search_changed(search_text)
            selected_uuid = self._selected_character.uuid if self._selected_character else None
            self._list_panel.set_characters(self._characters, selected_uuid)
        except Exception as error:
            self._show_error("Could not search characters", error)

    def _cancel_edit(self) -> None:
        if self._selected_character is not None:
            self._details_panel.set_character(self._selected_character)
            self._preview_panel.set_image_folder(self._selected_character.image_folder)

    def _browse_image(self, _file_name: str) -> None:
        path = filedialog.askopenfilename(
            title="Select character image",
            filetypes=(("PNG images", "*.png"), ("All files", "*.*")),
        )
        if not path:
            return
        self._preview_panel.set_image_folder(str(Path(path).parent))

    @staticmethod
    def _show_error(title: str, error: Exception) -> None:
        messagebox.showerror(title, str(error))
