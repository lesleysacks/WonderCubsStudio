"""Windows Explorer integration."""
from __future__ import annotations

import os
from pathlib import Path


class ExplorerService:
    """Open folders in Windows Explorer."""

    @staticmethod
    def open_folder(folder_path: str) -> None:
        """Open a project folder."""
        path = Path(folder_path)
        if not path.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")
        os.startfile(path)  # type: ignore[attr-defined]
