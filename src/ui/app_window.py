"""CustomTkinter user interface."""
from __future__ import annotations

import tkinter.messagebox as messagebox
from typing import Callable

import customtkinter as ctk

from src.controllers.main_controller import MainController
from src.models.dashboard import DashboardData, ProjectStatistics
from src.models.project import Project
from src.models.settings import AppSettings
from src.utils.logger import get_logger


class WonderCubsApp(ctk.CTk):
    """Main application window."""

    SIDEBAR_WIDTH = 210

    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self._controller = controller
        self._logger = get_logger(__name__)
        self._content_frame: ctk.CTkFrame | None = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self.title("WonderCubs Studio v0.2")
        self.geometry("1120x720")
        self.minsize(940, 620)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._build_shell()
        self._show_dashboard()

    def _build_shell(self) -> None:
        self.grid_columnconfigure(0, minsize=self.SIDEBAR_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, corner_radius=0, fg_color="#111827")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="WonderCubs\nStudio",
            font=("Segoe UI", 24, "bold"),
            justify="left",
        ).grid(row=0, column=0, padx=22, pady=(28, 24), sticky="w")

        nav_items: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Dashboard", self._show_dashboard),
            ("Projects", self._open_project_picker),
            ("Characters", lambda: self._show_coming_soon("Characters")),
            ("Prompt Library", lambda: self._show_coming_soon("Prompt Library")),
            ("Analytics", lambda: self._show_coming_soon("Analytics")),
            ("Settings", self._open_settings),
        )
        for row, (label, command) in enumerate(nav_items, start=1):
            button = ctk.CTkButton(
                sidebar,
                text=label,
                command=command,
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#1f2937",
            )
            button.grid(row=row, column=0, sticky="ew", padx=16, pady=4)
            self._nav_buttons[label] = button

        self._content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0b1120")
        self._content_frame.grid(row=0, column=1, sticky="nsew")
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_rowconfigure(0, weight=1)

    def _clear_content(self) -> ctk.CTkFrame:
        if self._content_frame is None:
            raise RuntimeError("Application content frame has not been initialized.")
        for widget in self._content_frame.winfo_children():
            widget.destroy()
        return self._content_frame

    def _set_active_nav(self, active_label: str) -> None:
        for label, button in self._nav_buttons.items():
            if label == active_label:
                button.configure(fg_color="#2563eb", hover_color="#1d4ed8")
            else:
                button.configure(fg_color="transparent", hover_color="#1f2937")

    def _show_dashboard(self) -> None:
        self._set_active_nav("Dashboard")
        content = self._clear_content()
        try:
            dashboard = self._controller.load_dashboard()
        except Exception as error:
            self.show_error("Could not load dashboard", error)
            return

        page = ctk.CTkScrollableFrame(content, fg_color="#0b1120", corner_radius=0)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="dashboard")

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=4, sticky="ew", padx=28, pady=(26, 16))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=("Segoe UI", 32, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="AI Production Pipeline",
            font=("Segoe UI", 15),
            text_color="#94a3b8",
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._build_stat_cards(page, dashboard.statistics)
        self._build_goal_panel(page, dashboard)
        self._build_latest_project_panel(page, dashboard)
        self._build_quick_actions(page)
        self._build_project_summary(page, dashboard.statistics)

    def _build_stat_cards(self, parent: ctk.CTkFrame, statistics: ProjectStatistics) -> None:
        cards = (
            ("Total Projects", statistics.total_projects),
            ("Published Projects", statistics.published_projects),
            ("Projects In Progress", statistics.projects_in_progress),
            ("Draft Projects", statistics.draft_projects),
            ("Videos Uploaded", statistics.videos_uploaded),
        )
        for index, (label, value) in enumerate(cards):
            card = self._card(parent)
            card.grid(row=1, column=index % 4, sticky="nsew", padx=10, pady=10)
            if index == 4:
                card.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
            ctk.CTkLabel(card, text=label, text_color="#a8b3c7", anchor="w").pack(anchor="w", padx=18, pady=(18, 6))
            ctk.CTkLabel(card, text=str(value), font=("Segoe UI", 30, "bold"), anchor="w").pack(anchor="w", padx=18, pady=(0, 18))

    def _build_goal_panel(self, parent: ctk.CTkFrame, dashboard: DashboardData) -> None:
        panel = self._card(parent)
        panel.grid(row=2, column=1, columnspan=3, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(panel, text="Today's Goal", font=("Segoe UI", 20, "bold"), anchor="w").pack(anchor="w", padx=20, pady=(18, 10))
        if dashboard.todays_goal is None:
            text = "No goal set for today."
        else:
            checkbox = "☑" if dashboard.todays_goal.is_completed else "□"
            text = f"{checkbox} {dashboard.todays_goal.description}"
        ctk.CTkLabel(panel, text=text, text_color="#dbeafe", font=("Segoe UI", 16), anchor="w").pack(anchor="w", padx=20, pady=(0, 20))

    def _build_latest_project_panel(self, parent: ctk.CTkFrame, dashboard: DashboardData) -> None:
        panel = self._card(parent)
        panel.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(panel, text="Latest Project Created", font=("Segoe UI", 20, "bold"), anchor="w").pack(anchor="w", padx=20, pady=(18, 12))
        if dashboard.latest_project is None:
            ctk.CTkLabel(panel, text="No projects created yet.", text_color="#94a3b8").pack(anchor="w", padx=20, pady=(0, 20))
            return
        rows = (
            ("Video Number", dashboard.latest_project.video_number),
            ("Project Name", dashboard.latest_project.title),
            ("Lesson", dashboard.latest_project.lesson),
            ("Status", dashboard.latest_project.status),
            ("Created Date", dashboard.latest_project.created_at),
        )
        for label, value in rows:
            row = ctk.CTkFrame(panel, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=label, text_color="#94a3b8", width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w").pack(side="left", fill="x", expand=True)

    def _build_quick_actions(self, parent: ctk.CTkFrame) -> None:
        panel = self._card(parent)
        panel.grid(row=3, column=2, columnspan=2, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(panel, text="Quick Actions", font=("Segoe UI", 20, "bold"), anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 12))
        panel.grid_columnconfigure((0, 1), weight=1)
        actions: tuple[tuple[str, Callable[[], None]], ...] = (
            ("New Project", self._open_new_project_dialog),
            ("Continue Project", self._open_project_picker),
            ("Character Manager", lambda: self._show_coming_soon("Character Manager")),
            ("Prompt Library", lambda: self._show_coming_soon("Prompt Library")),
            ("Analytics", lambda: self._show_coming_soon("Analytics")),
            ("Settings", self._open_settings),
        )
        for index, (label, command) in enumerate(actions, start=1):
            ctk.CTkButton(
                panel,
                text=label,
                command=command,
                height=52,
                corner_radius=10,
                font=("Segoe UI", 14, "bold"),
            ).grid(row=((index + 1) // 2), column=(index - 1) % 2, sticky="ew", padx=10, pady=8)

    def _build_project_summary(self, parent: ctk.CTkFrame, statistics: ProjectStatistics) -> None:
        panel = self._card(parent)
        panel.grid(row=4, column=0, columnspan=4, sticky="nsew", padx=10, pady=(10, 28))
        ctk.CTkLabel(panel, text="Project Summary", font=("Segoe UI", 20, "bold"), anchor="w").grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(18, 14))
        panel.grid_columnconfigure((0, 1, 2, 3), weight=1)
        summaries = (
            ("Total Projects", statistics.total_projects),
            ("Completed", statistics.completed_projects),
            ("In Progress", statistics.projects_in_progress),
            ("Draft", statistics.draft_projects),
        )
        for column, (label, value) in enumerate(summaries):
            ctk.CTkLabel(panel, text=str(value), font=("Segoe UI", 24, "bold")).grid(row=1, column=column, pady=(0, 2))
            ctk.CTkLabel(panel, text=label, text_color="#94a3b8").grid(row=2, column=column, pady=(0, 18))

    @staticmethod
    def _card(parent: ctk.CTkFrame) -> ctk.CTkFrame:
        return ctk.CTkFrame(parent, corner_radius=16, fg_color="#172033")

    def _show_coming_soon(self, title: str) -> None:
        self._set_active_nav(title if title in self._nav_buttons else "Dashboard")
        content = self._clear_content()
        frame = ctk.CTkFrame(content, corner_radius=16, fg_color="#172033")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(frame, text=title, font=("Segoe UI", 28, "bold")).pack(padx=70, pady=(42, 8))
        ctk.CTkLabel(frame, text="Coming Soon", font=("Segoe UI", 18), text_color="#94a3b8").pack(padx=70, pady=(0, 42))
        messagebox.showinfo(title, "Coming Soon")

    def _open_new_project_dialog(self) -> None:
        NewProjectDialog(self, self._controller, on_project_created=self._show_dashboard)

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

    def __init__(
        self,
        parent: WonderCubsApp,
        controller: MainController,
        on_project_created: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self._controller = controller
        self._on_project_created = on_project_created
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
            if self._on_project_created is not None:
                self._on_project_created()
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
