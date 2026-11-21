# 04 — Database and Data Audit

## 1. Current schema (verified from `src/database/schema.py`)

| Table | Key | Columns of note | Relations | Indexes |
|---|---|---|---|---|
| `Projects` | `id` INTEGER AUTOINCREMENT | `video_number` TEXT UNIQUE, `title`, `lesson`, `status`, `created_at`, `updated_at`, `published_at`, `folder_path` (absolute) | none | unique on `video_number` |
| `Goals` | `id` | `goal_date`, `description`, `is_completed` | none | `goal_date` |
| `Characters` | `uuid` TEXT | 15 descriptive TEXT columns (`fur_color`, `mane_color`, …), `image_folder` (absolute) | none | `name` |
| `Workspaces` | `uuid` TEXT | `project_name`, `lesson`, `topic`, `language`, `target_platform`, `resolution`, `aspect_ratio`, `duration`, `style`, `current_scene`, `status` | **none, although it is logically 1:1 with Projects** | `project_name` |
| `Prompts` | (`id`, `version`) | `template`, `variables` (JSON TEXT), `active` (CHECK 0/1) | none | partial UNIQUE (`id`) WHERE active=1; `name NOCASE` |

`PRAGMA user_version = 0`, `PRAGMA foreign_keys = 0` (Probe P8). No WAL. No migration table.

## 2. Data inventory and ownership

| Data | Location | Format | Backed up by the app? |
|---|---|---|---|
| Database | `<install dir>/data/database.db` | SQLite | No |
| Preferences | `<install dir>/config.json` | JSON | No |
| Logs | `<install dir>/logs/app.log` | text, **unbounded growth** | n/a |
| Project files | `<install dir>/projects/NNN_Title/` (setting ignored, C-02) | folders, README.md, placeholder .txt | No |
| Character images | Any user folder, referenced by absolute path | PNG | No |

## 3. Findings

### D-01 Workspace status is written to the wrong project — **Critical** — Verified (Probe P1)
- **Evidence:** Two projects titled "Intro" (001/L1, 002/L2). Saving the L1 workspace with status *Review* changed **project 002** to Review; 001 stayed Draft. Cause: `ProjectRepository.get_by_title` (`project_repository.py:61`) picks the newest row by title.
- **Business impact:** Silent corruption of production state, which feeds the dashboard and, in future, publishing queues.
- **Fix:** See A-01. Interim hot-fix: link by `project_id` and reject ambiguous titles.
- **Migration risk:** Backfill is ambiguous for existing duplicate titles. Pair them by creation order and **report** pairs it cannot settle to the user, without guessing silently.

### D-02 Renaming breaks synchronisation silently — **High** — Verified (Probe P2)
- **Evidence:** After renaming a workspace from "Alpha" to "Alpha v2" and setting *Review*, the project stayed *Draft* with no error (`change_status_by_title` returns `None`).
- **Fix:** Same as D-01.

### D-03 Non-atomic project creation and orphan folders — **High** — Verified (Probes P4, P5)
- **Evidence:** `ProjectService.create_project` creates the folders (`project_service.py:66`) **before** inserting the row (line 85). `MainController.create_project` then inserts the workspace in a separate step. P4: a workspace failure left 1 project and 0 workspaces. P5: after the database was lost or restored from an older backup, numbering restarts at 001, the folder exists, and creation fails permanently with `FileExistsError` (line 62) until the user renames folders by hand.
- **Fix:** One unit of work: insert the rows in a transaction, create the folders in a temp sibling, and rename them into place on commit. On a folder collision, pick the next free number rather than failing. Never delete user folders (current conservative behaviour is correct).

### D-04 No schema versioning, migration log or backup — **High** — Verified
- **Evidence:** `initialize_database` (`schema.py:114`) runs `CREATE IF NOT EXISTS` plus one ad-hoc `_upgrade_projects_schema` (line 132). No version is recorded. Other tables have no upgrade path at all.
- **Impact:** Every generalisation step in M1 is a migration. Without versioning, a partial failure cannot be detected or resumed, and old databases cannot be proven to upgrade correctly.
- **Fix:** Ordered migration scripts `NNN_name.py`, `user_version` plus a `schema_migrations` table (id, applied_at, app_version, checksum). Each migration runs in a transaction. An **automatic backup through the SQLite online backup API** is taken before any pending migration, keeping the last N copies.

### D-05 No referential integrity — **Medium** — Verified
- **Evidence:** No foreign keys are declared or enforced. Deleting a character leaves any references (future) dangling. Deleting a workspace leaves the project.
- **Fix:** Enable `PRAGMA foreign_keys=ON` per connection in `connection.py`, and add FKs in new tables. Existing tables gain them via the rebuild pattern (create new → copy → swap) only where needed.

### D-06 Destructive hard deletes without recovery — **Medium** — Verified (Probe P13)
- **Evidence:** `PromptService.delete_prompt` deletes **every version** (`prompt_repository.py` `delete` with no version). Characters and workspaces are hard-deleted. The UI asks for confirmation, but there is no undo, trash or backup.
- **Fix:** Soft delete (`deleted_at`), plus a Trash view and a purge policy. This aligns with "never destroy user data".

### D-07 Absolute file paths stored in the database — **Medium** — Verified
- **Evidence:** `Projects.folder_path`, `Characters.image_folder`. `CharacterService` rejects saves when the folder is missing (`character_service.py:171`), so moving a library or restoring on another machine makes characters **un-editable**.
- **Fix:** Named storage roots (`library://`, `projects://`) plus relative paths. Missing files become a *warning state*, not a save blocker.

### D-08 Mixed time bases — **Medium** — Verified
See C-06. SQLite `CURRENT_TIMESTAMP` defaults (UTC) coexist with naive local strings in `created_at`/`updated_at`. Probe P9 shows a migrated legacy row stamped by SQLite.

### D-09 Two-step version switching without a transaction — **Low** — Verified by reading
- **Evidence:** `PromptService.update_prompt` and `activate_version` call `deactivate_all`, then `create` or `activate_version`, on **separate connections** (`prompt_service.py:54–72, 107–112`). There is a manual compensation path for insert failures. A crash between the two steps leaves no active version (the prompt disappears from lists, but the data survives).
- **Fix:** A repository-level `replace_active_version()` in one transaction.

### D-10 Legacy statuses and unused tables — **Low** — Verified
`"Uploaded"` and `"In Progress"` are counted in `dashboard_repository.py` but cannot be produced. `Goals` has no writer (P-02). Map the legacy statuses in a migration, then either build goal editing or drop the panel.

## 4. Data preservation guarantees required for every migration

1. Back up before migrating (verified by a test asserting the backup file exists and opens).
2. Row counts per legacy table equal the mapped counts after migration.
3. A field-level round-trip for every legacy column: either mapped to a new column or preserved in an `attributes` JSON or `legacy` table. **No column is dropped in the release that introduces its replacement.**
4. Re-running a migration is a no-op (idempotence test).
5. Fixture databases for each historical schema (v0.1, v0.2, v0.3), committed under `tests/fixtures/db/`.
