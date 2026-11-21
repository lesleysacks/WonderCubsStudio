"""Application entry point for WonderCubs Studio."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.utils.app_paths import AppPaths
from src.utils.logger import configure_logging, get_logger

APP_VERSION = "0.3.0"
INSTALL_DIR = Path(__file__).resolve().parent


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="WonderCubs Studio")
    parser.add_argument("--list-backups", action="store_true", help="list database backups and exit")
    parser.add_argument(
        "--restore-backup", metavar="FILE", type=Path,
        help="restore the database from a backup file and exit (the current database is backed up first)",
    )
    return parser.parse_args(argv)


def _show_startup_error(title: str, message: str) -> None:
    print(f"{title}\n{message}", file=sys.stderr)
    try:
        import tkinter
        import tkinter.messagebox as messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:  # No display or Tk: the stderr message above stands.
        pass


def _run_backup_command(args: argparse.Namespace, paths: AppPaths) -> int:
    from src.database.backup import BackupError, list_backups, restore_backup

    if args.list_backups:
        backups = list_backups(paths.backups_dir)
        print("\n".join(str(path) for path in backups) or f"No backups in {paths.backups_dir}")
        return 0
    try:
        safety = restore_backup(args.restore_backup, paths.database_file, paths.backups_dir)
    except BackupError as error:
        print(f"Restore failed: {error}", file=sys.stderr)
        return 1
    print(f"Restored {paths.database_file} from {args.restore_backup}")
    if safety is not None:
        print(f"The previous database was kept at {safety}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Start the desktop application."""
    args = _parse_args(argv)
    paths = AppPaths.for_current_user(INSTALL_DIR)
    paths.ensure_directories()
    configure_logging(paths.logs_dir / "app.log")
    logger = get_logger(__name__)

    if args.list_backups or args.restore_backup:
        return _run_backup_command(args, paths)

    from src.database.migrations import MigrationError
    from src.database.schema import initialize_database
    from src.services.legacy_data_service import import_legacy_data
    from src.services.settings_service import SettingsService

    try:
        logger.info("Starting WonderCubs Studio v%s; data folder: %s", APP_VERSION, paths.root)
        imported = import_legacy_data(INSTALL_DIR, paths)
        logger.info("Legacy data check: %s", imported.status)

        settings_service = SettingsService(paths.config_file, paths.projects_dir)
        settings_service.ensure_config()
        initialize_database(paths.database_file, APP_VERSION)
    except MigrationError as error:
        logger.exception("Database upgrade failed")
        recovery = (
            f"\n\nYour data before the upgrade is saved in:\n{error.backup_path}\n\n"
            f"To restore it, run:\npython app.py --restore-backup \"{error.backup_path}\""
            if error.backup_path else ""
        )
        _show_startup_error("WonderCubs Studio could not open its database", f"{error}{recovery}")
        return 2
    except Exception:
        logger.exception("Fatal startup error")
        return 1

    try:
        from src.controllers.main_controller import MainController
        from src.ui.app_window import WonderCubsApp

        controller = MainController(paths, settings_service)
        app = WonderCubsApp(controller)
        app.mainloop()
        logger.info("WonderCubs Studio closed")
        return 0
    except Exception:
        logger.exception("Fatal startup error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
