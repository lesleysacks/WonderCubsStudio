"""Regenerate the historical database fixtures from the repository history.

Each fixture is created by running the *original* ``initialize_database`` of a
historical commit (its own schema.py and connection.py, fetched with
``git show``), then inserting representative data with SQL matching that
schema. The result is dumped to a plain-SQL file so it can be reviewed.

Usage (from the repository root):
    python tests/fixtures/db/build_fixtures.py
"""
from __future__ import annotations

import importlib
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

# (fixture name, commit, description)
COMMITS = (
    ("v0_1", "0190936", "Initial release v0.1: Projects only"),
    ("v0_2", "cbecf37", "Release v0.2.0: + Goals"),
    ("v0_3_sprint_3_4", "6c95a42", "Sprint 3.4: + Characters, manually created Workspaces"),
    ("v0_3_sprint_3_5", "3da6db4", "Sprint 3.5: + Prompts (pre-lifecycle Projects)"),
    ("v0_3_release", "7aa2f8b", "v0.3 hardening: lifecycle columns, auto-created workspaces"),
)

CHAR_COLS = ("uuid name species gender age_group fur_color mane_color eye_color shirt pants "
             "shoes accessories personality voice_style catchphrase description image_folder "
             "created_at updated_at").split()


def _git_show(commit: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
                          check=True, capture_output=True, text=True).stdout


def _historical_initialize(commit: str, database: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        package = Path(tmp) / "src" / "database"
        package.mkdir(parents=True)
        (Path(tmp) / "src" / "__init__.py").write_text("")
        (package / "__init__.py").write_text("")
        for name in ("schema.py", "connection.py"):
            (package / name).write_text(_git_show(commit, f"src/database/{name}"))
        sys.path.insert(0, tmp)
        try:
            for module in [m for m in sys.modules if m == "src" or m.startswith("src.")]:
                del sys.modules[module]
            importlib.import_module("src.database.schema").initialize_database(database)
        finally:
            sys.path.remove(tmp)
            for module in [m for m in sys.modules if m == "src" or m.startswith("src.")]:
                del sys.modules[module]


def _tables(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def _project(con, number, title, lesson, status, created, folder, updated=None):
    cols = _columns(con, "Projects")
    row = {"video_number": number, "title": title, "lesson": lesson, "status": status,
           "created_at": created, "folder_path": folder}
    if "updated_at" in cols:
        row["updated_at"] = updated or created
        row["published_at"] = created if status == "Published" else None
    con.execute(f"INSERT INTO Projects ({', '.join(row)}) VALUES ({', '.join('?' * len(row))})",
                tuple(row.values()))


def _workspace(con, uuid, name, lesson, status, created, updated=None, platform="YouTube"):
    con.execute(
        "INSERT INTO Workspaces (uuid, project_name, lesson, topic, language, target_platform, "
        "resolution, aspect_ratio, duration, style, current_scene, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'English', ?, '1920x1080', '16:9', 60, 'Pastel', 'Scene 1', ?, ?, ?)",
        (uuid, name, lesson, name, platform, status, created, updated or created))


def _populate(name: str, con: sqlite3.Connection) -> None:
    tables = _tables(con)
    lifecycle = "updated_at" in _columns(con, "Projects")
    base = "C:\\Users\\Creator\\WonderCubs Studio\\projects"
    if not lifecycle:
        _project(con, "001", "Leo Learns Colors", "Colors", "In Progress", "2026-06-30 10:00:00", f"{base}\\001_Leo_Learns_Colors")
        _project(con, "002", "Café Été — 日本語", "Seasons", "Completed", "2026-06-30 11:00:00", f"{base}\\002_Caf_t")
        _project(con, "003", "Shapes", "Shapes", "Uploaded", "2026-07-01 09:00:00", f"{base}\\003_Shapes")
        if "Workspaces" in tables:
            _project(con, "004", "Intro", "Hello", "In Progress", "2026-07-03 09:00:00", f"{base}\\004_Intro")
            _project(con, "005", "Intro", "Goodbye", "In Progress", "2026-07-03 09:05:00", f"{base}\\005_Intro")
    else:
        _project(con, "001", "Leo Learns Colors", "Colors", "In Progress", "2026-06-30 10:00:00", f"{base}\\001_Leo_Learns_Colors")
        _project(con, "002", "Café Été — 日本語", "Seasons", "Published", "2026-06-30 11:00:00", f"{base}\\002_Caf_t")
        _project(con, "003", "Intro", "Hello", "Review", "2026-08-01 09:00:00", f"{base}\\003_Intro")
        _project(con, "004", "Intro", "Goodbye", "Draft", "2026-08-01 09:05:00", f"{base}\\004_Intro")
        _project(con, "005", "Alpha", "Letters", "In Production", "2026-08-02 12:00:00", f"{base}\\005_Alpha", "2026-08-03 08:00:00")
    if "Goals" in tables:
        con.execute("INSERT INTO Goals (goal_date, description, is_completed, created_at) VALUES "
                    "('2026-06-30', 'Finish Leo storyboard', 1, '2026-06-30 08:00:00'),"
                    "('2026-07-01', 'Record voice — 第一話', 0, '2026-07-01 08:00:00')")
    if "Characters" in tables:
        for uuid, cname, species in (("c-leo", "Leo", "Lion"), ("c-zoe", "Zoë", "Fox")):
            values = {c: "" for c in CHAR_COLS}
            values.update(uuid=uuid, name=cname, species=species, personality="Curious",
                          catchphrase="Let's go! ¡Vamos!", created_at="2026-07-01 10:00:00",
                          updated_at="2026-07-02 10:00:00")
            con.execute(f"INSERT INTO Characters ({', '.join(CHAR_COLS)}) VALUES ({', '.join('?' * len(CHAR_COLS))})",
                        tuple(values[c] for c in CHAR_COLS))
    if "Workspaces" in tables:
        if not lifecycle:
            # Sprint 3.4-3.5: workspaces were typed in by hand, independent of projects.
            _workspace(con, "w-leo", "Leo Learns Colors", "Colors", "In Progress", "2026-07-03 10:00:00")
            _workspace(con, "w-intro", "Intro", "Hello", "Ready", "2026-07-03 10:05:00")
            _workspace(con, "w-ideas", "Unrelated Ideas", "Misc", "Draft", "2026-07-03 10:10:00", platform="TikTok")
        else:
            # v0.3 release: create_project wrote project + workspace in the same second.
            _workspace(con, "w-leo", "Leo Learns Colors", "Colors", "In Progress", "2026-06-30 10:00:00")
            _workspace(con, "w-cafe", "Café Été — 日本語", "Seasons", "Published", "2026-06-30 11:00:00")
            _workspace(con, "w-intro-1", "Intro", "Hello", "Review", "2026-08-01 09:00:00")
            _workspace(con, "w-intro-2", "Intro", "Goodbye", "Draft", "2026-08-01 09:05:00")
            _workspace(con, "w-alpha", "Alpha v2", "Letters", "In Production", "2026-08-02 12:00:00", "2026-08-03 08:00:00")
            _workspace(con, "w-ideas", "Unrelated Ideas", "Misc", "Draft", "2026-08-05 10:10:00", platform="TikTok")
    if "Prompts" in tables:
        con.execute("INSERT INTO Prompts VALUES ('p-story', 'Story Opener', 'Story', 1, 'First draft', "
                    "'Once upon a time {{CHARACTER_NAME}}', '[\"CHARACTER_NAME\"]', '2026-07-22 10:00:00', '2026-07-22 10:00:00', 0)")
        con.execute("INSERT INTO Prompts VALUES ('p-story', 'Story Opener', 'Story', 2, 'Revised', "
                    "'Today {{CHARACTER_NAME}} learns {{LESSON}}', '[\"CHARACTER_NAME\", \"LESSON\"]', '2026-07-22 10:00:00', '2026-07-23 10:00:00', 1)")
        con.execute("INSERT INTO Prompts VALUES ('p-seo', 'SEO Title — 日本', 'SEO', 1, '', "
                    "'{{PROJECT_NAME}} | WonderCubs', '[\"PROJECT_NAME\"]', '2026-07-22 11:00:00', '2026-07-22 11:00:00', 1)")


def build(name: str, commit: str, description: str) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        database = Path(tmp) / "database.db"
        _historical_initialize(commit, database)
        con = sqlite3.connect(database)
        _populate(name, con)
        con.commit()
        dump = "\n".join(con.iterdump())
        con.close()
    target = OUT / f"{name}.sql"
    target.write_text(f"-- {description}\n-- Schema created by initialize_database() at commit {commit}.\n"
                      f"-- Regenerate with tests/fixtures/db/build_fixtures.py\n{dump}\n", encoding="utf-8")
    return target


if __name__ == "__main__":
    for fixture in COMMITS:
        print(build(*fixture))
