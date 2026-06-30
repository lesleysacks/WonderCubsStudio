"""Database schema creation."""
from __future__ import annotations

from pathlib import Path

from src.database.connection import create_connection

CREATE_PROJECTS_TABLE = """
CREATE TABLE IF NOT EXISTS Projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    lesson TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    folder_path TEXT NOT NULL
);
"""

CREATE_GOALS_TABLE = """
CREATE TABLE IF NOT EXISTS Goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_date TEXT NOT NULL,
    description TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_GOALS_DATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_goals_goal_date ON Goals (goal_date);
"""


def initialize_database(database_file: Path) -> None:
    """Create the application database and required tables."""
    database_file.parent.mkdir(parents=True, exist_ok=True)
    with create_connection(database_file) as connection:
        connection.execute(CREATE_PROJECTS_TABLE)
        connection.execute(CREATE_GOALS_TABLE)
        connection.execute(CREATE_GOALS_DATE_INDEX)
        connection.commit()
