"""SQLite connection helpers."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator
import sqlite3


def _open(database_file: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_file)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def create_connection(database_file: Path) -> Iterator[sqlite3.Connection]:
    """Create a SQLite connection and close it after use.

    Callers own commits; anything not committed is discarded on close.
    """
    connection = _open(database_file)
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def transaction(database_file: Path) -> Iterator[sqlite3.Connection]:
    """Run a block as one atomic unit: commit on success, roll back on error."""
    connection = _open(database_file)
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            yield connection
        except BaseException:
            connection.rollback()
            raise
        connection.commit()
    finally:
        connection.close()
