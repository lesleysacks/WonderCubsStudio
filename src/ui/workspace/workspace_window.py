"""Workspace Context Engine frame."""
from __future__ import annotations

from dataclasses import replace
import json
import tkinter.messagebox as messagebox

import customtkinter as ctk

from src.controllers.workspace_controller import WorkspaceController
from src.models.workspace import Workspace


class WorkspaceWindow(ctk.CTkFrame):
    """Modular Workspace Context UI."""

    ASPECT_RATIOS = ("16:9", "9:16", "1:1", "4:3")
    STATUS_VALUES = ("Draft", "In Progress", "Ready", "Published")

    def __init__(self, parent: ctk.CTkFrame, controller: WorkspaceController) -> None:
        super().__init__(parent, corner_radius=0, fg_color="#0b1120")
        self._controller = controller
        self._workspaces: list[Workspace] = []
        self._selected_workspace: Workspace | None = None
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._option_menus: dict[str, ctk.CTkOptionMenu] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        self.refresh()

    def refresh(self) -> None:
        """Reload workspaces from the controller."""
        try:
            self._workspaces = self._controller.load_workspaces()
            self._render_workspace_list()
            active_workspace = self._controller.get_active_workspace()
            if active_workspace is not None:
                self._select_workspace(active_workspace)
            elif self._selected_workspace is None and self._workspaces:
                self._select_workspace(self._workspaces[0])
            elif self._selected_workspace is None:
                self._new_workspace()
        except Exception as error:
            self._show_error("Could not load workspaces", error)

    def _build(self) -> None:
        toolbar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=0)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            toolbar,
            text="Workspace Context",
            font=("Segoe UI", 22, "bold"),
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")
        actions = (
            ("New", self._new_workspace),
            ("Save", self._save_workspace),
            ("Switch", self._switch_workspace),
            ("Export", self._export_context),
            ("Delete", self._delete_workspace),
            ("Refresh", self.refresh),
        )
        for column, (label, command) in enumerate(actions, start=1):
            ctk.CTkButton(toolbar, text=label, command=command, width=84).grid(
                row=0,
                column=column,
                padx=(0, 10),
                pady=12,
            )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=18)
        body.grid_columnconfigure(0, weight=1, minsize=260)
        body.grid_columnconfigure(1, weight=3, minsize=520)
        body.grid_rowconfigure(0, weight=1)

        self._list_frame = ctk.CTkScrollableFrame(body, fg_color="#172033", corner_radius=8)
        self._list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        ctk.CTkLabel(
            self._list_frame,
            text="Projects",
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, padx=16, pady=(16, 10), sticky="w")

        form = ctk.CTkScrollableFrame(body, fg_color="#172033", corner_radius=8)
        form.grid(row=0, column=1, sticky="nsew")
        form.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            form,
            text="Active Production Context",
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 16), sticky="w")

        fields = (
            ("Project Name", "project_name"),
            ("Lesson", "lesson"),
            ("Topic", "topic"),
            ("Language", "language"),
            ("Target Platform", "target_platform"),
            ("Resolution", "resolution"),
            ("Duration", "duration"),
            ("Style", "style"),
            ("Current Scene", "current_scene"),
        )
        for row, (label, key) in enumerate(fields, start=1):
            ctk.CTkLabel(form, text=label, text_color="#cbd5e1").grid(
                row=row,
                column=0,
                padx=(20, 12),
                pady=7,
                sticky="w",
            )
            entry = ctk.CTkEntry(form)
            entry.grid(row=row, column=1, padx=(0, 20), pady=7, sticky="ew")
            self._entries[key] = entry

        option_start = len(fields) + 1
        ctk.CTkLabel(form, text="Aspect Ratio", text_color="#cbd5e1").grid(
            row=option_start,
            column=0,
            padx=(20, 12),
            pady=7,
            sticky="w",
        )
        aspect_menu = ctk.CTkOptionMenu(form, values=list(self.ASPECT_RATIOS))
        aspect_menu.grid(row=option_start, column=1, padx=(0, 20), pady=7, sticky="ew")
        self._option_menus["aspect_ratio"] = aspect_menu

        ctk.CTkLabel(form, text="Status", text_color="#cbd5e1").grid(
            row=option_start + 1,
            column=0,
            padx=(20, 12),
            pady=7,
            sticky="w",
        )
        status_menu = ctk.CTkOptionMenu(form, values=list(self.STATUS_VALUES))
        status_menu.grid(row=option_start + 1, column=1, padx=(0, 20), pady=7, sticky="ew")
        self._option_menus["status"] = status_menu

    def _render_workspace_list(self) -> None:
        for widget in self._list_frame.winfo_children()[1:]:
            widget.destroy()
        if not self._workspaces:
            ctk.CTkLabel(
                self._list_frame,
                text="No workspaces yet.",
                text_color="#94a3b8",
            ).grid(row=1, column=0, padx=16, pady=10, sticky="w")
            return
        selected_uuid = self._selected_workspace.uuid if self._selected_workspace else ""
        for row, workspace in enumerate(self._workspaces, start=1):
            button = ctk.CTkButton(
                self._list_frame,
                text=f"{workspace.project_name}\n{workspace.lesson}",
                anchor="w",
                height=54,
                corner_radius=8,
                fg_color="#2563eb" if workspace.uuid == selected_uuid else "#1f2937",
                hover_color="#1d4ed8",
                command=lambda selected=workspace: self._select_workspace(selected),
            )
            button.grid(row=row, column=0, sticky="ew", padx=12, pady=5)

    def _new_workspace(self) -> None:
        workspace = self._controller.on_new_workspace()
        self._selected_workspace = workspace
        self._set_form(workspace)
        self._render_workspace_list()

    def _select_workspace(self, workspace: Workspace) -> None:
        try:
            selected = self._controller.on_open_workspace(workspace.uuid)
            self._selected_workspace = selected
            self._set_form(selected)
            self._render_workspace_list()
        except Exception as error:
            self._show_error("Could not open workspace", error)

    def _save_workspace(self) -> None:
        try:
            workspace = self._get_form_workspace()
            saved = self._controller.on_save_workspace(workspace)
            self._selected_workspace = saved
            self.refresh()
            messagebox.showinfo("Workspace Saved", f"Saved workspace: {saved.project_name}")
        except Exception as error:
            messagebox.showerror("Workspace Error", str(error))

    def _switch_workspace(self) -> None:
        if self._selected_workspace is None:
            messagebox.showinfo("Switch Workspace", "Select a workspace to switch to.")
            return
        try:
            switched = self._controller.on_switch_workspace(self._selected_workspace.uuid)
            self._selected_workspace = switched
            self._set_form(switched)
            messagebox.showinfo("Workspace Switched", f"Active workspace: {switched.project_name}")
        except Exception as error:
            self._show_error("Could not switch workspace", error)

    def _delete_workspace(self) -> None:
        if self._selected_workspace is None:
            messagebox.showinfo("Delete Workspace", "Select a workspace to delete.")
            return
        if not messagebox.askyesno("Delete Workspace", f"Delete {self._selected_workspace.project_name}?"):
            return
        try:
            self._controller.on_delete_workspace(self._selected_workspace.uuid)
            self._selected_workspace = None
            self.refresh()
        except Exception as error:
            self._show_error("Could not delete workspace", error)

    def _export_context(self) -> None:
        if self._selected_workspace is None:
            messagebox.showinfo("Export Context", "Select a workspace to export.")
            return
        try:
            payload = self._controller.on_export_context(self._selected_workspace.uuid)
            messagebox.showinfo("Workspace Context JSON", json.dumps(payload, indent=2))
        except Exception as error:
            self._show_error("Could not export context", error)

    def _set_form(self, workspace: Workspace) -> None:
        values = {
            "project_name": workspace.project_name,
            "lesson": workspace.lesson,
            "topic": workspace.topic,
            "language": workspace.language,
            "target_platform": workspace.target_platform,
            "resolution": workspace.resolution,
            "duration": str(workspace.duration),
            "style": workspace.style,
            "current_scene": workspace.current_scene,
        }
        for key, value in values.items():
            self._entries[key].delete(0, "end")
            self._entries[key].insert(0, value)
        self._option_menus["aspect_ratio"].set(workspace.aspect_ratio)
        self._option_menus["status"].set(workspace.status)

    def _get_form_workspace(self) -> Workspace:
        source = self._selected_workspace or self._controller.on_new_workspace()
        duration_text = self._entries["duration"].get().strip()
        duration = int(duration_text) if duration_text else 0
        return replace(
            source,
            project_name=self._entries["project_name"].get(),
            lesson=self._entries["lesson"].get(),
            topic=self._entries["topic"].get(),
            language=self._entries["language"].get(),
            target_platform=self._entries["target_platform"].get(),
            resolution=self._entries["resolution"].get(),
            aspect_ratio=self._option_menus["aspect_ratio"].get(),
            duration=duration,
            style=self._entries["style"].get(),
            current_scene=self._entries["current_scene"].get(),
            status=self._option_menus["status"].get(),
        )

    @staticmethod
    def _show_error(title: str, error: Exception) -> None:
        messagebox.showerror(title, str(error))
