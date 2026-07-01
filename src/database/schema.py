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

CREATE_CHARACTERS_TABLE = """
CREATE TABLE IF NOT EXISTS Characters (
    uuid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    gender TEXT NOT NULL,
    age_group TEXT NOT NULL,
    fur_color TEXT NOT NULL,
    mane_color TEXT NOT NULL,
    eye_color TEXT NOT NULL,
    shirt TEXT NOT NULL,
    pants TEXT NOT NULL,
    shoes TEXT NOT NULL,
    accessories TEXT NOT NULL,
    personality TEXT NOT NULL,
    voice_style TEXT NOT NULL,
    catchphrase TEXT NOT NULL,
    description TEXT NOT NULL,
    image_folder TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_CHARACTERS_NAME_INDEX = """
CREATE INDEX IF NOT EXISTS idx_characters_name ON Characters (name);
"""


def initialize_database(database_file: Path) -> None:
    """Create the application database and required tables."""
    database_file.parent.mkdir(parents=True, exist_ok=True)
    with create_connection(database_file) as connection:
        connection.execute(CREATE_PROJECTS_TABLE)
        connection.execute(CREATE_GOALS_TABLE)
        connection.execute(CREATE_GOALS_DATE_INDEX)
        connection.execute(CREATE_CHARACTERS_TABLE)
        connection.execute(CREATE_CHARACTERS_NAME_INDEX)
        connection.commit()
