"""Database schema creation."""
from __future__ import annotations

from pathlib import Path
import sqlite3

from src.database.connection import create_connection

CREATE_PROJECTS_TABLE = """
CREATE TABLE IF NOT EXISTS Projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    lesson TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TEXT,
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

CREATE_WORKSPACES_TABLE = """
CREATE TABLE IF NOT EXISTS Workspaces (
    uuid TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    lesson TEXT NOT NULL,
    topic TEXT NOT NULL,
    language TEXT NOT NULL,
    target_platform TEXT NOT NULL,
    resolution TEXT NOT NULL,
    aspect_ratio TEXT NOT NULL,
    duration INTEGER NOT NULL,
    style TEXT NOT NULL,
    current_scene TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_WORKSPACES_PROJECT_NAME_INDEX = """
CREATE INDEX IF NOT EXISTS idx_workspaces_project_name ON Workspaces (project_name);
"""

CREATE_PROMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS Prompts (
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    version INTEGER NOT NULL,
    description TEXT NOT NULL,
    template TEXT NOT NULL,
    variables TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    PRIMARY KEY (id, version)
);
"""

CREATE_PROMPTS_NAME_INDEX = """
CREATE INDEX IF NOT EXISTS idx_prompts_name ON Prompts (name COLLATE NOCASE);
"""

CREATE_PROMPTS_ACTIVE_VERSION_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_one_active_version
ON Prompts (id) WHERE active = 1;
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
        connection.execute(CREATE_WORKSPACES_TABLE)
        connection.execute(CREATE_WORKSPACES_PROJECT_NAME_INDEX)
        connection.execute(CREATE_PROMPTS_TABLE)
        connection.execute(CREATE_PROMPTS_NAME_INDEX)
        connection.execute(CREATE_PROMPTS_ACTIVE_VERSION_INDEX)
        _upgrade_projects_schema(connection)
        connection.commit()


def _upgrade_projects_schema(connection: sqlite3.Connection) -> None:
    """Idempotently add lifecycle fields while preserving existing rows."""
    columns = {
        str(row["name"])
        for row in connection.execute("PRAGMA table_info(Projects)").fetchall()
    }
    if "status" not in columns:
        connection.execute("ALTER TABLE Projects ADD COLUMN status TEXT DEFAULT 'Draft'")
    if "created_at" not in columns:
        connection.execute("ALTER TABLE Projects ADD COLUMN created_at TEXT")
    if "updated_at" not in columns:
        connection.execute("ALTER TABLE Projects ADD COLUMN updated_at TEXT")
    if "published_at" not in columns:
        connection.execute("ALTER TABLE Projects ADD COLUMN published_at TEXT")

    connection.execute(
        "UPDATE Projects SET status = 'Draft' WHERE status IS NULL OR TRIM(status) = ''"
    )
    connection.execute(
        """
        UPDATE Projects
        SET created_at = COALESCE(NULLIF(created_at, ''), CURRENT_TIMESTAMP)
        WHERE created_at IS NULL OR created_at = ''
        """
    )
    connection.execute(
        """
        UPDATE Projects
        SET updated_at = COALESCE(NULLIF(updated_at, ''), created_at, CURRENT_TIMESTAMP)
        WHERE updated_at IS NULL OR updated_at = ''
        """
    )
