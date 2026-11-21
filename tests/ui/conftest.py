"""Fixtures for UI tests that drive the real CustomTkinter windows.

UI tests need Tk and a display. Where either is missing they are skipped,
unless WONDERCUBS_REQUIRE_UI_TESTS=1 (set in CI), which turns a skip into a
failure so a broken UI environment cannot pass silently.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import gc
from functools import lru_cache
import os
from pathlib import Path
from typing import Any

import pytest

REQUIRE = os.environ.get("WONDERCUBS_REQUIRE_UI_TESTS") == "1"


def _unavailable(reason: str) -> None:
    if REQUIRE:
        pytest.fail(f"UI tests are required but cannot run: {reason}")
    pytest.skip(f"UI tests skipped: {reason}")


@dataclass
class UiHarness:
    app: Any
    controller: Any
    paths: Any
    messages: list[tuple[str, str, str]] = field(default_factory=list)
    errors: list[Any] = field(default_factory=list)
    opened_folders: list[str] = field(default_factory=list)

    def pump(self) -> None:
        self.app.update_idletasks()
        self.app.update()

    def content(self) -> Any:
        children = self.app._content_frame.winfo_children()
        return children[0] if children else None

    def message_errors(self) -> list[tuple[str, str, str]]:
        return [m for m in self.messages if m[0] == "error"]


@lru_cache(maxsize=1)
def _ui_unavailable_reason() -> str | None:
    """Probe once per session: every Tk() is a new Tcl interpreter, and on
    Windows creating many in one process can fail ('tcl_findLibrary')."""
    try:
        import tkinter
    except ImportError as error:
        return f"tkinter is not installed ({error})"
    try:
        probe = tkinter.Tk()
        probe.destroy()
    except tkinter.TclError as error:
        return f"no display ({error})"
    finally:
        gc.collect()
    try:
        import customtkinter  # noqa: F401
    except ImportError as error:
        return f"customtkinter is not installed ({error})"
    return None


@pytest.fixture
def ui(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    reason = _ui_unavailable_reason()
    if reason is not None:
        _unavailable(reason)
    import tkinter
    import tkinter.messagebox as messagebox

    from src.controllers.main_controller import MainController
    from src.database.schema import initialize_database
    from src.services.settings_service import SettingsService
    from src.ui.app_window import WonderCubsApp
    from src.utils.app_paths import AppPaths

    harness_messages: list[tuple[str, str, str]] = []
    for name in ("showinfo", "showwarning", "showerror"):
        kind = name.replace("show", "")
        monkeypatch.setattr(
            messagebox, name,
            lambda title="", message="", _kind=kind, **_kw: harness_messages.append((_kind, title, message)),
        )
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)

    paths = AppPaths(
        base_path=tmp_path / "install",
        data_root=tmp_path / "user data",
        default_projects_root=tmp_path / "Documents" / "Projects ñ",
    )
    paths.ensure_directories()
    settings = SettingsService(paths.config_file, paths.projects_dir)
    settings.ensure_config()
    initialize_database(paths.database_file)
    controller = MainController(paths, settings)
    opened: list[str] = []
    monkeypatch.setattr(controller._explorer_service, "open_folder", opened.append)

    app = WonderCubsApp(controller)
    harness = UiHarness(app, controller, paths, harness_messages, opened_folders=opened)
    app.report_callback_exception = lambda *exc: harness.errors.append(exc)
    harness.pump()
    try:
        yield harness
    finally:
        for window in list(app.winfo_children()):
            try:
                window.destroy()
            except tkinter.TclError:
                pass
        app.destroy()
        del app, harness
        gc.collect()  # release the Tcl interpreter before the next test
