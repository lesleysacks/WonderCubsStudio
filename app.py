"""Application entry point for WonderCubs Studio."""
from __future__ import annotations

from pathlib import Path
import sys

from src.controllers.main_controller import MainController
from src.database.schema import initialize_database
from src.services.settings_service import SettingsService
from src.ui.app_window import WonderCubsApp
from src.utils.app_paths import AppPaths
from src.utils.logger import configure_logging, get_logger


def main() -> int:
    """Start the desktop application."""
    base_path = Path(__file__).resolve().parent
    paths = AppPaths(base_path=base_path)

    try:
        paths.ensure_directories()
        configure_logging(paths.logs_dir / "app.log")
        logger = get_logger(__name__)
        logger.info("Starting WonderCubs Studio v0.2")

        settings_service = SettingsService(paths.config_file, paths.projects_dir)
        settings_service.ensure_config()
        initialize_database(paths.database_file)

        controller = MainController(paths, settings_service)
        app = WonderCubsApp(controller)
        app.mainloop()
        logger.info("WonderCubs Studio closed")
        return 0
    except Exception:
        logger = get_logger(__name__)
        logger.exception("Fatal startup error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
