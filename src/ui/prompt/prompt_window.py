"""Prompt Library workspace."""
from __future__ import annotations

import tkinter.messagebox as messagebox
from typing import Any

import customtkinter as ctk

from src.controllers.prompt_controller import PromptController
from src.models.prompt import Prompt
from src.services.prompt_service import PromptNotFoundError, PromptValidationError
from src.ui.prompt.prompt_toolbar import PromptToolbar


class PromptWindow(ctk.CTkFrame):
    """Create, version, preview, export, and search reusable prompt templates."""

    def __init__(self, parent: ctk.CTkFrame, controller: PromptController) -> None:
        super().__init__(parent, fg_color="#0b1120", corner_radius=0)
        self._controller, self._prompts, self._selected = controller, [], None
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        self.refresh()

    def _build(self) -> None:
        PromptToolbar(self, self._new, self._save, self._duplicate, self._preview, self._export).grid(
            row=0, column=0, columnspan=3, sticky="ew")
        left = ctk.CTkFrame(self, fg_color="#172033")
        left.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=16)
        self._search = ctk.CTkEntry(left, placeholder_text="Search prompts")
        self._search.pack(fill="x", padx=10, pady=10)
        self._search.bind("<KeyRelease>", lambda _event: self._search_changed())
        self._list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        ctk.CTkButton(left, text="Delete", fg_color="#991b1b", command=self._delete).pack(fill="x", padx=10, pady=10)

        editor = ctk.CTkFrame(self, fg_color="#172033")
        editor.grid(row=1, column=1, sticky="nsew", padx=8, pady=16)
        editor.grid_columnconfigure(1, weight=1)
        self._name = self._field(editor, "Name", 0)
        self._category = ctk.CTkComboBox(editor, values=["Story", "Image", "Voice", "Thumbnail", "SEO", "Custom"])
        self._category.set("Custom")
        self._category.grid(row=1, column=1, sticky="ew", padx=12, pady=7)
        ctk.CTkLabel(editor, text="Category").grid(row=1, column=0, sticky="w", padx=12)
        self._description = self._field(editor, "Description", 2)
        ctk.CTkLabel(editor, text="Template").grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 0))
        self._template = ctk.CTkTextbox(editor, height=330)
        self._template.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=12, pady=(4, 12))
        editor.grid_rowconfigure(4, weight=1)

        preview = ctk.CTkFrame(self, fg_color="#172033")
        preview.grid(row=1, column=2, sticky="nsew", padx=(8, 16), pady=16)
        ctk.CTkLabel(preview, text="Live Preview", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=12, pady=12)
        self._preview_text = ctk.CTkTextbox(preview)
        self._preview_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._character_uuid = ctk.CTkEntry(preview, placeholder_text="Character UUID (optional)")
        self._character_uuid.pack(fill="x", padx=12, pady=(0, 8))
        self._export_format = ctk.CTkOptionMenu(preview, values=["json", "txt", "markdown"])
        self._export_format.set("json")
        self._export_format.pack(fill="x", padx=12, pady=(0, 8))
        self._versions = ctk.CTkOptionMenu(preview, values=["No versions"], command=self._activate_version)
        self._versions.pack(fill="x", padx=12, pady=(0, 12))

    def _field(self, parent: ctk.CTkFrame, label: str, row: int) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label).grid(row=row, column=0, sticky="w", padx=12)
        entry = ctk.CTkEntry(parent)
        entry.grid(row=row, column=1, sticky="ew", padx=12, pady=7)
        return entry

    def refresh(self) -> None:
        self._prompts = self._controller.load_prompts()
        self._render_list()

    def _render_list(self) -> None:
        for child in self._list.winfo_children(): child.destroy()
        for prompt in self._prompts:
            ctk.CTkButton(self._list, text=f"{prompt.name}\n{prompt.category} · v{prompt.version}", anchor="w",
                          fg_color="#2563eb" if self._selected and prompt.id == self._selected.id else "transparent",
                          command=lambda item=prompt: self._select(item)).pack(fill="x", pady=3)

    def _new(self) -> None:
        self._selected = self._controller.on_new_prompt()
        self._set_editor(self._selected)
        self._preview_text.delete("1.0", "end")

    def _select(self, prompt: Prompt) -> None:
        self._selected = prompt
        self._set_editor(prompt)
        self._load_versions(prompt)
        self._preview()
        self._render_list()

    def _set_editor(self, prompt: Prompt) -> None:
        for entry, value in ((self._name, prompt.name), (self._description, prompt.description)):
            entry.delete(0, "end"); entry.insert(0, value)
        self._category.set(prompt.category)
        self._template.delete("1.0", "end"); self._template.insert("1.0", prompt.template)

    def _draft(self) -> Prompt:
        base = self._selected or self._controller.on_new_prompt()
        return Prompt(id=base.id, name=self._name.get(), category=self._category.get(), description=self._description.get(),
                      template=self._template.get("1.0", "end-1c"), variables=(),
                      created_at=base.created_at, updated_at=base.updated_at)

    def _save(self) -> None:
        try:
            self._selected = self._controller.on_save_prompt(self._draft())
            self.refresh(); self._select(self._selected)
        except (PromptValidationError, PromptNotFoundError) as error: messagebox.showerror("Prompt Error", str(error))

    def _preview(self) -> None:
        if not self._selected: return
        try:
            rendered = self._controller.on_preview_prompt(
                self._selected.id, character_uuid=self._character_uuid.get().strip() or None
            )
            self._preview_text.delete("1.0", "end"); self._preview_text.insert("1.0", rendered)
        except (PromptValidationError, LookupError) as error:
            self._preview_text.delete("1.0", "end"); self._preview_text.insert("1.0", f"Preview needs values: {error}")

    def _duplicate(self) -> None:
        if self._selected:
            self._selected = self._controller.on_duplicate_prompt(self._selected.id); self.refresh(); self._select(self._selected)

    def _delete(self) -> None:
        if self._selected and messagebox.askyesno("Delete Prompt", f"Delete all versions of {self._selected.name}?"):
            self._controller.on_delete_prompt(self._selected.id); self._selected = None; self._new(); self.refresh()

    def _export(self) -> None:
        if self._selected:
            try:
                export_format = self._export_format.get()
                messagebox.showinfo(
                    f"Prompt Export ({export_format.upper()})",
                    self._controller.on_export_prompt(
                        self._selected.id, export_format,
                        character_uuid=self._character_uuid.get().strip() or None,
                    ),
                )
            except (PromptValidationError, LookupError) as error: messagebox.showerror("Prompt Error", str(error))

    def _search_changed(self) -> None:
        self._prompts = self._controller.on_search_changed(self._search.get()); self._render_list()

    def _load_versions(self, prompt: Prompt) -> None:
        versions = self._controller.load_versions(prompt.id)
        labels = [f"Version {item.version}" for item in versions]
        self._versions.configure(values=labels); self._versions.set(f"Version {prompt.version}")

    def _activate_version(self, label: str) -> None:
        if self._selected and label.startswith("Version "):
            self._selected = self._controller.on_activate_version(self._selected.id, int(label.split()[-1])); self.refresh(); self._select(self._selected)
