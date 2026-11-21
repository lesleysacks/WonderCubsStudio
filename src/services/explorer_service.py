"""Open folders in the operating system's file manager."""
from __future__ import annotations

from collections.abc import Callable, Sequence
import os
from pathlib import Path
import subprocess
import sys

Launcher = Callable[[Sequence[str]], object]


def _spawn(command: Sequence[str]) -> object:
    # Detached, no shell: the path is passed as a single argument.
    return subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


class ExplorerService:
    """Open a folder in Explorer (Windows), Finder (macOS) or the desktop's
    default file manager (Linux, via ``xdg-open``)."""

    def __init__(
        self,
        platform: str | None = None,
        launcher: Launcher | None = None,
        startfile: Callable[[str], None] | None = None,
    ) -> None:
        self._platform = platform or sys.platform
        self._launcher = launcher or _spawn
        self._startfile = startfile or getattr(os, "startfile", None)

    def open_folder(self, folder_path: str) -> None:
        """Open a project folder."""
        path = Path(folder_path)
        if not path.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Not a folder: {folder_path}")
        target = str(path.resolve())
        if self._platform.startswith("win"):
            if self._startfile is None:
                raise OSError("Opening folders is not supported on this system.")
            self._startfile(target)
            return
        command = ["open", target] if self._platform == "darwin" else ["xdg-open", target]
        try:
            self._launcher(command)
        except FileNotFoundError as error:
            raise OSError(
                f"Could not open the folder because '{command[0]}' is not available. "
                f"The folder is: {target}"
            ) from error
