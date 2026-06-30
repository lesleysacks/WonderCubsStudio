"""SQLite connection helpers."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator
import sqlite3


@contextmanager
def create_connection(database_file: Path) -> Iterator[sqlite3.Connection]:
    """Create a SQLite connection and close it after use."""
    connection = sqlite3.connect(database_file)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
