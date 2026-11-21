"""Versioned, transactional schema migrations with pre-migration backups.

Rules for adding a migration:

* Append a new ``Migration`` with the next version number; never edit or
  reorder a migration that has shipped.
* A migration must be additive and must not delete or rewrite user values.
* It runs inside one transaction together with the version bump, so it either
  applies completely or not at all.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from src.database.backup import BackupError, create_backup
from src.utils.logger import get_logger

MigrationReport = dict[str, Any]
MigrationStep = Callable[[sqlite3.Connection], MigrationReport | None]

CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    app_version TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '{}'
);
"""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: MigrationStep


@dataclass(frozen=True)
class MigrationResult:
    from_version: int
    to_version: int
    backup_path: Path | None = None
    applied: tuple[int, ...] = ()
    reports: dict[int, MigrationReport] = field(default_factory=dict)


class MigrationError(RuntimeError):
    """A migration failed; the database was rolled back to ``current_version``."""

    def __init__(self, message: str, backup_path: Path | None, current_version: int) -> None:
        super().__init__(message)
        self.backup_path = backup_path
        self.current_version = current_version


class DatabaseTooNewError(MigrationError):
    """The database was written by a newer application version."""


def _registered_migrations() -> tuple[Migration, ...]:
    # Imported lazily so schema.py can import from this module without a cycle.
    from src.database import schema

    return schema.MIGRATIONS


def latest_version() -> int:
    return max((m.version for m in _registered_migrations()), default=0)


def get_schema_version(database_file: Path) -> int:
    connection = sqlite3.connect(database_file)
    try:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])
    finally:
        connection.close()


def _has_user_tables(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' LIMIT 1"
    ).fetchone()
    return row is not None


def migrate(
    database_file: Path,
    backup_dir: Path,
    app_version: str = "unknown",
    migrations: tuple[Migration, ...] | None = None,
) -> MigrationResult:
    """Bring ``database_file`` to the latest schema version.

    An existing database with pending migrations is backed up (and the backup
    verified) before anything is changed. If a step fails, that step is rolled
    back, earlier completed steps remain, and ``MigrationError`` reports the
    backup that restores the pre-upgrade state.
    """
    logger = get_logger(__name__)
    steps = tuple(sorted(migrations or _registered_migrations(), key=lambda m: m.version))
    target = max((m.version for m in steps), default=0)
    database_file.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_file, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        current = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if current > target:
            raise DatabaseTooNewError(
                f"Database schema version {current} is newer than this application "
                f"supports ({target}). Update WonderCubs Studio; the database was not changed.",
                backup_path=None,
                current_version=current,
            )
        pending = [m for m in steps if m.version > current]
        if not pending:
            return MigrationResult(from_version=current, to_version=current)

        backup_path: Path | None = None
        if _has_user_tables(connection):
            try:
                backup_path = create_backup(
                    database_file, backup_dir, f"pre-migration-v{current}-to-v{target}"
                )
            except BackupError as error:
                raise MigrationError(
                    f"Upgrade cancelled because a backup could not be created: {error}",
                    backup_path=None,
                    current_version=current,
                ) from error

        applied: list[int] = []
        reports: dict[int, MigrationReport] = {}
        start = current
        for migration in pending:
            try:
                connection.execute("BEGIN IMMEDIATE")
                report = migration.apply(connection) or {}
                connection.execute(CREATE_MIGRATIONS_TABLE)
                connection.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at, app_version, details) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        migration.version,
                        migration.name,
                        datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        app_version,
                        json.dumps(report, ensure_ascii=False, sort_keys=True),
                    ),
                )
                connection.execute(f"PRAGMA user_version = {int(migration.version)}")
                connection.execute("COMMIT")
            except Exception as error:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                logger.exception("Migration %s (%s) failed", migration.version, migration.name)
                raise MigrationError(
                    f"Database upgrade step {migration.version} ({migration.name}) failed and was "
                    f"rolled back: {error}",
                    backup_path=backup_path,
                    current_version=current,
                ) from error
            current = migration.version
            applied.append(migration.version)
            reports[migration.version] = report
            logger.info("Migration applied: %s %s", migration.version, migration.name)
        return MigrationResult(
            from_version=start,
            to_version=current,
            backup_path=backup_path,
            applied=tuple(applied),
            reports=reports,
        )
    finally:
        connection.close()
