"""CustomTkinter user interface."""
from __future__ import annotations

import tkinter.messagebox as messagebox
from typing import Callable

import customtkinter as ctk

from src.controllers.main_controller import MainController
from src.models.project import Project
from src.models.settings import AppSettings
from src.utils.logger import get_logger


class WonderCubsApp(ctk.CTk):
    """Main application window."""

    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self._controller = controller
        self._logger = get_logger(__name__)
        self.title("WonderCubs Studio v0.1")
        self.geometry("720x540")
        self.minsize(640, 480)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self._build_home_screen()

    def _build_home_screen(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.grid(row=0, column=0, sticky="nsew", padx=32, pady=32)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="=================================", font=("Segoe UI", 18)).grid(row=0, column=0, pady=(30, 2))
        ctk.CTkLabel(frame, text="WonderCubs Studio", font=("Segoe UI", 30, "bold")).grid(row=1, column=0, pady=2)
        ctk.CTkLabel(frame, text="AI Production Pipeline", font=("Segoe UI", 18)).grid(row=2, column=0, pady=2)
        ctk.CTkLabel(frame, text="=================================", font=("Segoe UI", 18)).grid(row=3, column=0, pady=(2, 28))

        buttons: list[tuple[str, Callable[[], None]]] = [
            ("New Project", self._open_new_project_dialog),
            ("Open Project", self._open_project_picker),
            ("Video Queue", self._open_video_queue),
            ("Settings", self._open_settings),
            ("Exit", self.destroy),
        ]
        for index, (label, command) in enumerate(buttons, start=4):
            ctk.CTkButton(frame, text=label, command=command, width=220, height=38).grid(row=index, column=0, pady=7)

    def _open_new_project_dialog(self) -> None:
        NewProjectDialog(self, self._controller)

    def _open_project_picker(self) -> None:
        ProjectListWindow(self, self._controller, mode="open")

    def _open_video_queue(self) -> None:
        ProjectListWindow(self, self._controller, mode="queue")

    def _open_settings(self) -> None:
        SettingsWindow(self, self._controller)

    def show_error(self, title: str, error: Exception) -> None:
        """Log and show a friendly error message."""
        self._logger.exception(title)
        messagebox.showerror(title, str(error))


class NewProjectDialog(ctk.CTkToplevel):
    """Dialog for creating a project."""

    def __init__(self, parent: WonderCubsApp, controller: MainController) -> None:
        super().__init__(parent)
        self._parent = parent
        self._controller = controller
        self.title("New Project")
        self.geometry("420x330")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="New Project", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, pady=(22, 16))
        fields = (("Video Title", "Leo Learns Colors"), ("Lesson", "Colors"), ("Video Number", "001"))
        for row, (label, placeholder) in enumerate(fields, start=1):
            ctk.CTkLabel(self, text=label).grid(row=row * 2 - 1, column=0, sticky="w", padx=42)
            entry = ctk.CTkEntry(self, placeholder_text=placeholder, width=320)
            entry.grid(row=row * 2, column=0, pady=(2, 10))
            self._entries[label] = entry
        ctk.CTkButton(self, text="Create Project", command=self._create_project, width=180).grid(row=7, column=0, pady=(8, 8))
        ctk.CTkButton(self, text="Cancel", command=self.destroy, width=180, fg_color="gray").grid(row=8, column=0)

    def _create_project(self) -> None:
        try:
            project = self._controller.create_project(
                video_number=self._entries["Video Number"].get(),
                title=self._entries["Video Title"].get(),
                lesson=self._entries["Lesson"].get(),
            )
            messagebox.showinfo("Project Created", f"Created project: {project.title}")
            self.destroy()
        except Exception as error:
            self._parent.show_error("Could not create project", error)


class ProjectListWindow(ctk.CTkToplevel):
    """Project list for opening projects and viewing the queue."""

    def __init__(self, parent: WonderCubsApp, controller: MainController, mode: str) -> None:
        super().__init__(parent)
        self._parent = parent
        self._controller = controller
        self._mode = mode
        self.title("Open Project" if mode == "open" else "Video Queue")
        self.geometry("820x440")
        self.transient(parent)
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        title = "Open Project" if self._mode == "open" else "Video Queue"
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 22, "bold")).grid(row=0, column=0, pady=16)
        table = ctk.CTkScrollableFrame(self)
        table.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        headers = ("Video Number", "Title", "Lesson", "Status", "Created Date")
        for column, header in enumerate(headers):
            table.grid_columnconfigure(column, weight=1)
            ctk.CTkLabel(table, text=header, font=("Segoe UI", 13, "bold")).grid(row=0, column=column, padx=8, pady=8, sticky="w")
        try:
            projects = self._controller.list_projects()
            if not projects:
                ctk.CTkLabel(table, text="No projects found.").grid(row=1, column=0, padx=8, pady=20, sticky="w")
                return
            for row, project in enumerate(projects, start=1):
                values = (project.video_number, project.title, project.lesson, project.status, project.created_at)
                for column, value in enumerate(values):
                    label = ctk.CTkLabel(table, text=value, anchor="w")
                    label.grid(row=row, column=column, padx=8, pady=5, sticky="w")
                    if self._mode == "open":
                        label.bind("<Button-1>", lambda _event, selected=project: self._open_project(selected))
        except Exception as error:
            self._parent.show_error("Could not load projects", error)

    def _open_project(self, project: Project) -> None:
        try:
            self._controller.open_project_folder(project)
        except Exception as error:
            self._parent.show_error("Could not open project", error)


class SettingsWindow(ctk.CTkToplevel):
    """Settings editor."""

    def __init__(self, parent: WonderCubsApp, controller: MainController) -> None:
        super().__init__(parent)
        self._parent = parent
        self._controller = controller
        self._entries: dict[str, ctk.CTkEntry] = {}
        self.title("Settings")
        self.geometry("500x420")
        self.transient(parent)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        try:
            settings = self._controller.load_settings()
        except Exception as error:
            self._parent.show_error("Could not load settings", error)
            self.destroy()
            return
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, pady=(22, 16))
        fields = (
            ("Default Project Folder", settings.default_project_folder),
            ("Default Resolution", settings.default_resolution),
            ("Default FPS", str(settings.default_fps)),
            ("Author Name", settings.author_name),
            ("Channel Name", settings.channel_name),
        )
        for row, (label, value) in enumerate(fields, start=1):
            ctk.CTkLabel(self, text=label).grid(row=row * 2 - 1, column=0, sticky="w", padx=48)
            entry = ctk.CTkEntry(self, width=360)
            entry.insert(0, value)
            entry.grid(row=row * 2, column=0, pady=(2, 9))
            self._entries[label] = entry
        ctk.CTkButton(self, text="Save Settings", command=self._save, width=180).grid(row=11, column=0, pady=16)

    def _save(self) -> None:
        try:
            settings = AppSettings(
                default_project_folder=self._entries["Default Project Folder"].get().strip(),
                default_resolution=self._entries["Default Resolution"].get().strip(),
                default_fps=int(self._entries["Default FPS"].get().strip()),
                author_name=self._entries["Author Name"].get().strip(),
                channel_name=self._entries["Channel Name"].get().strip(),
            )
            self._controller.save_settings(settings)
            messagebox.showinfo("Settings Saved", "Settings saved successfully.")
            self.destroy()
        except Exception as error:
            self._parent.show_error("Could not save settings", error)
