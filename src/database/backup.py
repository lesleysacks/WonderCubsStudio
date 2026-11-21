"""Verified SQLite database backups and restore."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sqlite3

from src.utils.logger import get_logger

BACKUP_SUFFIX = ".db"
_LABEL_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class BackupError(RuntimeError):
    """Raised when a backup cannot be created, verified or restored."""


def _read_only_uri(database_file: Path) -> str:
    # as_uri() percent-encodes spaces, '#', '%' and non-ASCII characters.
    return database_file.resolve().as_uri() + "?mode=ro"


def _copy_database(source: Path, destination: Path) -> None:
    """Copy a database with SQLite's online backup API (consistent snapshot)."""
    source_connection = sqlite3.connect(_read_only_uri(source), uri=True)
    try:
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
    finally:
        source_connection.close()


def verify_database(database_file: Path) -> None:
    """Raise BackupError unless the file is a readable, intact SQLite database."""
    try:
        connection = sqlite3.connect(_read_only_uri(database_file), uri=True)
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise BackupError(f"Not a readable database: {database_file} ({error})") from error
    if result is None or result[0] != "ok":
        raise BackupError(f"Integrity check failed for {database_file}: {result}")


def create_backup(database_file: Path, backup_dir: Path, label: str) -> Path:
    """Create and verify a timestamped copy of ``database_file`` in ``backup_dir``."""
    if not database_file.is_file():
        raise BackupError(f"Database not found: {database_file}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    clean_label = _LABEL_PATTERN.sub("-", label).strip("-") or "backup"
    backup_path = backup_dir / f"{database_file.stem}-{stamp}-{clean_label}{BACKUP_SUFFIX}"
    partial = backup_path.with_name(backup_path.name + ".partial")
    try:
        _copy_database(database_file, partial)
        verify_database(partial)
        os.replace(partial, backup_path)
    except (sqlite3.Error, OSError, BackupError) as error:
        partial.unlink(missing_ok=True)
        raise BackupError(f"Could not back up {database_file}: {error}") from error
    get_logger(__name__).info("Database backup created: %s", backup_path)
    return backup_path


def list_backups(backup_dir: Path) -> list[Path]:
    """Return backups, newest first."""
    if not backup_dir.is_dir():
        return []
    return sorted(
        (path for path in backup_dir.iterdir() if path.suffix == BACKUP_SUFFIX),
        key=lambda path: path.name,
        reverse=True,
    )


def restore_backup(backup_path: Path, database_file: Path, backup_dir: Path) -> Path | None:
    """Replace ``database_file`` with a verified backup.

    The current database (if any) is itself backed up first, so a restore can
    always be undone. Returns the path of that safety backup.
    """
    verify_database(backup_path)
    safety_backup = None
    if database_file.exists():
        safety_backup = create_backup(database_file, backup_dir, "pre-restore")
    database_file.parent.mkdir(parents=True, exist_ok=True)
    staged = database_file.with_name(database_file.name + ".restoring")
    try:
        _copy_database(backup_path, staged)
        verify_database(staged)
        os.replace(staged, database_file)
    except (sqlite3.Error, OSError, BackupError) as error:
        staged.unlink(missing_ok=True)
        raise BackupError(f"Could not restore {backup_path}: {error}") from error
    get_logger(__name__).info("Database restored from %s", backup_path)
    return safety_backup
