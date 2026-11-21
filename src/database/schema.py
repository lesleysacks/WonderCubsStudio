"""Database schema definition and upgrade entry point."""
from __future__ import annotations

from pathlib import Path
import sqlite3

from src.database.migrations import Migration, MigrationResult, migrate

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


def _migration_001_baseline(connection: sqlite3.Connection) -> dict[str, object]:
    """Bring any pre-versioning database (v0.1 to v0.3) to the v0.3 schema.

    Every statement is idempotent, so this is safe for databases that already
    have some or all tables.
    """
    for statement in (
        CREATE_PROJECTS_TABLE,
        CREATE_GOALS_TABLE,
        CREATE_GOALS_DATE_INDEX,
        CREATE_CHARACTERS_TABLE,
        CREATE_CHARACTERS_NAME_INDEX,
        CREATE_WORKSPACES_TABLE,
        CREATE_WORKSPACES_PROJECT_NAME_INDEX,
        CREATE_PROMPTS_TABLE,
        CREATE_PROMPTS_NAME_INDEX,
        CREATE_PROMPTS_ACTIVE_VERSION_INDEX,
    ):
        connection.execute(statement)
    _upgrade_projects_schema(connection)
    return {}


def _upgrade_projects_schema(connection: sqlite3.Connection) -> None:
    """Idempotently add lifecycle fields while preserving existing rows."""
    columns = {
        str(row[1])
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


def _migration_002_link_workspaces_to_projects(connection: sqlite3.Connection) -> dict[str, object]:
    """Add ``Workspaces.project_id`` and link existing rows only where certain.

    Before this migration a workspace found "its" project by title, which is
    neither unique nor stable (audit D-01/D-02). Links are inferred only from
    unambiguous evidence; anything else is left unlinked and listed in the
    migration report. No existing value is changed.
    """
    columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(Workspaces)")}
    if "project_id" not in columns:
        connection.execute(
            "ALTER TABLE Workspaces ADD COLUMN project_id INTEGER REFERENCES Projects(id)"
        )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_workspaces_project_id "
        "ON Workspaces (project_id) WHERE project_id IS NOT NULL"
    )

    projects = [
        (int(row[0]), str(row[1]).strip(), str(row[2] or ""), str(row[3]).strip())
        for row in connection.execute(
            "SELECT id, title, created_at, lesson FROM Projects ORDER BY id"
        )
    ]
    workspaces = [
        (str(row[0]), str(row[1]).strip(), str(row[2] or ""), str(row[3]).strip())
        for row in connection.execute(
            "SELECT uuid, project_name, created_at, lesson FROM Workspaces "
            "WHERE project_id IS NULL ORDER BY created_at, uuid"
        )
    ]
    taken = {
        int(row[0])
        for row in connection.execute(
            "SELECT project_id FROM Workspaces WHERE project_id IS NOT NULL"
        )
    }
    links: dict[str, tuple[int, str]] = {}

    def free(project_id: int) -> bool:
        return project_id not in taken and all(pid != project_id for pid, _ in links.values())

    # Pass 1: exactly one project and one workspace share the title.
    for uuid, name, _created, _lesson in workspaces:
        same_title = [p for p in projects if p[1] == name]
        same_name_workspaces = [w for w in workspaces if w[1] == name]
        if len(same_title) == 1 and len(same_name_workspaces) == 1 and free(same_title[0][0]):
            links[uuid] = (same_title[0][0], "unique title")

    # Pass 2: v0.3 created project and workspace together, in the same second,
    # copying the lesson. A unique (created_at, lesson) match is conclusive even
    # when titles are duplicated or the workspace was renamed afterwards.
    for uuid, _name, created, lesson in workspaces:
        if uuid in links or not created:
            continue
        matches = [p for p in projects if p[2] == created and p[3] == lesson and free(p[0])]
        rivals = [w for w in workspaces if w[0] not in links and w[2] == created and w[3] == lesson]
        if len(matches) == 1 and len(rivals) == 1:
            links[uuid] = (matches[0][0], "created with project")

    for uuid, (project_id, _reason) in links.items():
        connection.execute(
            "UPDATE Workspaces SET project_id = ? WHERE uuid = ?", (project_id, uuid)
        )

    unlinked = []
    for uuid, name, _created, _lesson in workspaces:
        if uuid in links:
            continue
        candidates = [p for p in projects if p[1] == name]
        reason = (
            "no project has this title"
            if not candidates
            else f"ambiguous: {len(candidates)} projects share this title"
            if len(candidates) > 1
            else "title matches a project that already has a workspace"
        )
        unlinked.append({"uuid": uuid, "project_name": name, "reason": reason})
    return {
        "linked": [
            {"uuid": uuid, "project_id": pid, "evidence": reason}
            for uuid, (pid, reason) in sorted(links.items())
        ],
        "unlinked_workspaces": unlinked,
    }


MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "baseline_v0_3_schema", _migration_001_baseline),
    Migration(2, "link_workspaces_to_projects", _migration_002_link_workspaces_to_projects),
)


def backup_dir_for(database_file: Path) -> Path:
    """Default location for automatic backups of ``database_file``."""
    return database_file.parent / "backups"


def initialize_database(database_file: Path, app_version: str = "unknown") -> MigrationResult:
    """Create the application database or upgrade it to the latest schema."""
    database_file.parent.mkdir(parents=True, exist_ok=True)
    return migrate(database_file, backup_dir_for(database_file), app_version)
