"""Helpers for loading historical database fixtures in tests."""
from __future__ import annotations

from pathlib import Path
import sqlite3

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "db"
HISTORICAL_FIXTURES = ("v0_1", "v0_2", "v0_3_sprint_3_4", "v0_3_sprint_3_5", "v0_3_release")


def load_fixture(name: str, database_file: Path) -> Path:
    """Create ``database_file`` from a historical SQL dump (never a shared file)."""
    database_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_file)
    try:
        connection.executescript((FIXTURE_DIR / f"{name}.sql").read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()
    return database_file


def snapshot(database_file: Path) -> dict[str, tuple[tuple[str, ...], list[tuple[object, ...]]]]:
    """Return every user table's columns and rows, for before/after comparison."""
    connection = sqlite3.connect(database_file)
    try:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' AND name != 'schema_migrations' ORDER BY name"
            )
        ]
        result = {}
        for table in tables:
            columns = tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})"))
            rows = connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
            result[table] = (columns, rows)
        return result
    finally:
        connection.close()


def assert_original_values_preserved(before: dict, after: dict) -> None:
    """Every original table, column and value must survive unchanged."""
    for table, (columns, rows) in before.items():
        assert table in after, f"table {table} disappeared"
        new_columns, new_rows = after[table]
        assert len(new_rows) == len(rows), f"{table}: row count changed"
        indexes = [new_columns.index(column) for column in columns]
        projected = [tuple(row[i] for i in indexes) for row in new_rows]
        assert projected == rows, f"{table}: values changed"
