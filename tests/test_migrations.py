"""Schema versioning, backups, restore and data preservation (M0.5.2)."""
from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest

from src.database import backup as backup_module
from src.database.backup import BackupError, create_backup, list_backups, restore_backup, verify_database
from src.database.migrations import (
    DatabaseTooNewError,
    Migration,
    MigrationError,
    get_schema_version,
    latest_version,
    migrate,
)
from src.database.schema import MIGRATIONS, backup_dir_for, initialize_database
from tests.db_fixtures import (
    HISTORICAL_FIXTURES,
    assert_original_values_preserved,
    load_fixture,
    snapshot,
)


def _applied(database: Path) -> list[tuple[int, str]]:
    connection = sqlite3.connect(database)
    try:
        return connection.execute("SELECT version, name FROM schema_migrations ORDER BY version").fetchall()
    finally:
        connection.close()


def test_fresh_database_is_created_at_latest_version_without_backup(tmp_path: Path) -> None:
    database = tmp_path / "data" / "database.db"

    result = initialize_database(database)

    assert get_schema_version(database) == latest_version() == MIGRATIONS[-1].version
    assert result.backup_path is None
    assert [version for version, _ in _applied(database)] == [m.version for m in MIGRATIONS]
    assert list_backups(backup_dir_for(database)) == []


@pytest.mark.parametrize("fixture", HISTORICAL_FIXTURES)
def test_historical_database_upgrades_with_verified_backup_and_no_data_loss(
    tmp_path: Path, fixture: str
) -> None:
    database = load_fixture(fixture, tmp_path / "data" / "database.db")
    before = snapshot(database)

    result = initialize_database(database, app_version="test")

    assert result.from_version == 0
    assert result.to_version == latest_version()
    assert get_schema_version(database) == latest_version()
    assert result.backup_path is not None and result.backup_path.is_file()
    verify_database(result.backup_path)
    # The backup is an exact copy of the pre-upgrade database.
    assert snapshot(result.backup_path) == before
    assert_original_values_preserved(before, snapshot(database))


@pytest.mark.parametrize("fixture", HISTORICAL_FIXTURES)
def test_upgrade_is_idempotent(tmp_path: Path, fixture: str) -> None:
    database = load_fixture(fixture, tmp_path / "database.db")
    initialize_database(database)
    after_first = snapshot(database)
    backups = list_backups(backup_dir_for(database))

    result = initialize_database(database)

    assert result.applied == ()
    assert result.backup_path is None
    assert snapshot(database) == after_first
    assert list_backups(backup_dir_for(database)) == backups


def test_failed_migration_rolls_back_and_reports_backup(tmp_path: Path) -> None:
    database = load_fixture("v0_3_release", tmp_path / "database.db")
    before = snapshot(database)

    def half_done_then_fail(connection: sqlite3.Connection) -> None:
        connection.execute("ALTER TABLE Projects ADD COLUMN should_not_survive TEXT")
        connection.execute("UPDATE Projects SET title = 'CORRUPTED'")
        raise RuntimeError("simulated crash")

    broken = (Migration(1, "baseline", lambda c: {}), Migration(2, "broken", half_done_then_fail))

    with pytest.raises(MigrationError) as raised:
        migrate(database, tmp_path / "backups", migrations=broken)

    error = raised.value
    assert error.backup_path is not None and error.backup_path.is_file()
    assert error.current_version == 1  # step 1 committed before step 2 failed
    # Step 1 committed, step 2 rolled back completely.
    assert get_schema_version(database) == 1
    after = snapshot(database)
    assert "should_not_survive" not in after["Projects"][0]
    assert_original_values_preserved(before, after)
    assert snapshot(error.backup_path) == before


def test_recovery_path_restores_pre_upgrade_state_after_failure(tmp_path: Path) -> None:
    database = load_fixture("v0_2", tmp_path / "database.db")
    before = snapshot(database)
    steps = (Migration(1, "ok", lambda c: {}), Migration(2, "bad", _add_column_then_fail))
    with pytest.raises(MigrationError) as raised:
        migrate(database, tmp_path / "backups", migrations=steps)
    assert get_schema_version(database) == 1

    safety = restore_backup(raised.value.backup_path, database, tmp_path / "backups")

    assert get_schema_version(database) == 0
    assert snapshot(database) == before
    assert safety is not None and get_schema_version(safety) == 1  # restore is undoable


def _add_column_then_fail(connection: sqlite3.Connection) -> None:
    connection.execute("ALTER TABLE Goals ADD COLUMN extra TEXT")
    raise ValueError("boom")


def test_upgrade_is_cancelled_when_backup_cannot_be_made(tmp_path: Path, monkeypatch) -> None:
    database = load_fixture("v0_3_release", tmp_path / "database.db")
    before = snapshot(database)

    def refuse(*_args, **_kwargs):
        raise BackupError("disk full")

    monkeypatch.setattr("src.database.migrations.create_backup", refuse)

    with pytest.raises(MigrationError, match="backup could not be created"):
        initialize_database(database)
    assert get_schema_version(database) == 0
    assert snapshot(database) == before


def test_newer_database_is_refused_unchanged(tmp_path: Path) -> None:
    database = tmp_path / "database.db"
    initialize_database(database)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA user_version = 999")
    connection.close()
    raw = database.read_bytes()

    with pytest.raises(DatabaseTooNewError):
        initialize_database(database)
    assert database.read_bytes() == raw


def test_backup_and_restore_work_with_spaces_and_non_ascii_paths(tmp_path: Path) -> None:
    folder = tmp_path / "Mes Données" / "日本語 #1 100%"
    database = load_fixture("v0_3_release", folder / "database.db")
    before = snapshot(database)

    backup_path = create_backup(database, folder / "backups", "manual")
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM Projects")
    connection.commit()
    connection.close()
    restore_backup(backup_path, database, folder / "backups")

    assert snapshot(database) == before
    assert len(list_backups(folder / "backups")) == 2  # manual + pre-restore


def test_restore_refuses_a_corrupt_backup_and_keeps_current_database(tmp_path: Path) -> None:
    database = load_fixture("v0_2", tmp_path / "database.db")
    before = snapshot(database)
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"this is not a database" * 100)

    with pytest.raises(BackupError):
        restore_backup(corrupt, database, tmp_path / "backups")
    assert snapshot(database) == before


def test_failed_backup_leaves_no_partial_file(tmp_path: Path, monkeypatch) -> None:
    database = load_fixture("v0_1", tmp_path / "database.db")

    def fail_verify(_path: Path) -> None:
        raise BackupError("verification failed")

    monkeypatch.setattr(backup_module, "verify_database", fail_verify)
    with pytest.raises(BackupError):
        create_backup(database, tmp_path / "backups", "x")
    assert list((tmp_path / "backups").iterdir()) == []
