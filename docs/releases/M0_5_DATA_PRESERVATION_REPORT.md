# M0.5 — Data Preservation Report

This report is about whether existing projects, characters, workspaces, prompts, goals and settings survive the M0.5 upgrade. It records what was verified, how, and what was not.

## 1. Guarantees and how each is enforced

| Guarantee | Mechanism | Verified by |
|---|---|---|
| No upgrade without a verified backup | `migrate()` copies the database with the SQLite online backup API and runs `PRAGMA integrity_check` on the copy before any change. If the backup fails, the upgrade is cancelled | `test_upgrade_is_cancelled_when_backup_cannot_be_made`, `test_historical_database_upgrades_with_verified_backup_and_no_data_loss` |
| Each step is all-or-nothing | Each migration and its `user_version` bump run in one `BEGIN IMMEDIATE` transaction | `test_failed_migration_rolls_back_and_reports_backup` (a step that adds a column and overwrites every title, then crashes, leaves no trace) |
| Upgrades are additive | Migrations add tables, columns and indexes only. No column is dropped or renamed, and no table is rebuilt | Code review of `src/database/schema.py`; `assert_original_values_preserved` on every fixture |
| Re-running is harmless | Version gate plus idempotent statements | `test_upgrade_is_idempotent` (5 fixtures) |
| Newer databases are not touched | `DatabaseTooNewError` before any write | `test_newer_database_is_refused_unchanged` (byte-identical file) |
| Recovery is always possible | `restore_backup()` verifies the backup, backs up the current database first, and writes atomically. CLI: `python app.py --list-backups`, `--restore-backup <file>` | `test_recovery_path_restores_pre_upgrade_state_after_failure`, `test_cli_lists_and_restores_backups`, `test_restore_refuses_a_corrupt_backup_and_keeps_current_database` |
| Legacy install data is never modified | The first-run import only reads the install folder, copies with verification, and refuses to overwrite existing user data | `test_legacy_data_is_copied_without_modifying_the_original` (SHA-256 of every legacy file before and after), `test_existing_user_data_is_never_overwritten_by_legacy_data` |
| Tests never touch real user data | Every test uses `tmp_path`. Fixtures are SQL text loaded into fresh temporary files | `tests/db_fixtures.py`; no test reads the user data folder |

## 2. Historical databases used

The fixtures are **not hand-written schemas**. `tests/fixtures/db/build_fixtures.py` fetches each historical commit's own `src/database/schema.py` and `connection.py` with `git show`, runs that release's `initialize_database()`, inserts representative data matching that schema, and dumps the result to reviewable SQL.

| Fixture | Commit | Shape |
|---|---|---|
| `v0_1` | `0190936` | Projects only; status `In Progress` / `Completed` / `Uploaded` |
| `v0_2` | `cbecf37` | + Goals |
| `v0_3_sprint_3_4` | `6c95a42` | + Characters, Workspaces typed in **by hand** (statuses `In Progress`, `Ready`) |
| `v0_3_sprint_3_5` | `3da6db4` | + Prompts (multi-version), pre-lifecycle Projects |
| `v0_3_release` | `7aa2f8b` | Lifecycle columns; workspaces auto-created with projects; duplicate titles; a renamed workspace |

The data includes non-ASCII text (`Café Été — 日本語`, `Zoë`, `¡Vamos!`, `第一話`), Windows paths with spaces, duplicate project titles, and a workspace with no matching project.

**Limitation:** these are representative reconstructions, not copies of a real user's database. No real user database was available or used (see `M0_5_KNOWN_LIMITATIONS.md`, L-03).

## 3. Upgrade results (executed 2026-11-21, Python 3.13, SQLite 3.53.1)

| Fixture | Tables (rows before → after) | Backup verified and identical to pre-upgrade | Every original value identical | Schema version |
|---|---|---|---|---|
| `v0_1` | Projects 3→3; new empty tables: Characters, Goals, Prompts, Workspaces | yes | yes | 0 → 2 |
| `v0_2` | Goals 2→2, Projects 3→3; new empty tables: Characters, Prompts, Workspaces | yes | yes | 0 → 2 |
| `v0_3_sprint_3_4` | Characters 2→2, Goals 2→2, Projects 5→5, Workspaces 3→3; new empty table: Prompts | yes | yes | 0 → 2 |
| `v0_3_sprint_3_5` | Characters 2→2, Goals 2→2, Projects 5→5, Prompts 3→3, Workspaces 3→3 | yes | yes | 0 → 2 |
| `v0_3_release` | Characters 2→2, Goals 2→2, Projects 5→5, Prompts 3→3, Workspaces 6→6 | yes | yes | 0 → 2 |

"Every original value identical" means every original table, column and row, compared value by value (`tests/db_fixtures.py::assert_original_values_preserved`). New columns are added alongside:
- `Projects.updated_at` and `published_at` for pre-lifecycle databases. This is the unchanged v0.3 rule: `updated_at` copies `created_at`.
- `Workspaces.project_id`.

One pre-existing v0.3 rule can change a value: a `Projects.status` that is NULL or blank becomes `Draft`. This rule existed before M0.5 and is unchanged. No fixture contains a blank status.

## 4. Workspace → project link backfill (migration 2)

Links are written only on conclusive evidence. Everything else stays unlinked and is listed in `schema_migrations.details` for version 2.

| Evidence | Rule |
|---|---|
| Unique title | Exactly one project and one workspace share the exact title |
| Created with project | Exactly one project and one workspace share `created_at` (to the second) **and** `lesson`. This is the signature of v0.3's `create_project`, and it holds after a rename |

| Fixture | Linked | Left unlinked (reason) |
|---|---|---|
| `v0_3_sprint_3_4` / `_3_5` | `w-leo` → 1 (unique title) | `w-intro` (ambiguous: 2 projects share this title); `w-ideas` (no project has this title) |
| `v0_3_release` | `w-leo` → 1, `w-cafe` → 2 (unique title); `w-intro-1` → 3, `w-intro-2` → 4 (duplicate titles, created with project); `w-alpha` "Alpha v2" → 5 (renamed, created with project) | `w-ideas` (no project has this title) |

**Effect of staying unlinked:** the workspace keeps all its data and remains editable, but saving it no longer changes any project's status. Before M0.5 it would have changed whichever project had the same title, or none. This is the D-01 fix, applied conservatively. Relinking such workspaces needs a small UI decision (L-01).

## 5. Relocation of user data (first start of the new version)

| Item | What happens | Original |
|---|---|---|
| `<install>/data/database.db` | Verified copy to `<user data>/data/database.db`, then upgraded there (backup in `<user data>/data/backups/`) | Untouched |
| `<install>/config.json` | Copied. A relative or old-default project folder is resolved (see below) | Untouched |
| Project folders | **Not moved.** Paths stored in the database still point to them | Untouched |
| `<install>/logs` | Not copied (logs are not user data) | Untouched |
| Record | `<user data>/legacy-import.json`: source, destination, notes, `legacy_files_modified: false` | — |

The default project folder: if the legacy setting was the old in-install default (`projects`, or `<install>/projects`), new projects go to `Documents/WonderCubs Studio/Projects`, and the marker notes where existing projects remain. A user-chosen folder is kept.

**End-to-end check of the real application:** `python app.py` was run under Xvfb (Tk 9.0, CustomTkinter 5.2.2) on a scratch copy of the branch with a `v0_3_release` database in the install folder, and `WONDERCUBS_DATA_DIR` set to a folder named `…/e2e data/Zoë`. The log shows the import, the backup, migrations 1 and 2, and the dashboard loading. SHA-256 of the legacy `data/database.db` and `config.json` matched before and after. No `logs/` or `projects/` folder was created in the install folder.

## 6. Settings preservation

- An unreadable `config.json` is kept as `config.json.corrupt-<UTC time>` (bytes preserved) and defaults are used. Previously, settings failed to open.
- An unreadable legacy settings file is kept as `config.legacy-unreadable.json` in the user folder, and the database is still imported.
- Saves are atomic (`.tmp` + `os.replace`).

## 7. Not verified

- Upgrades of a real user's database (none available).
- Real Windows or macOS user-profile layouts (OneDrive-redirected Documents, roaming profiles). The path logic is unit-tested, and CI exercises the app layer on Windows and macOS runners.
- Very large databases (backup time and disk usage).
