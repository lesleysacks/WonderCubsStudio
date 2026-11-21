# M0.5 Stabilisation — Implementation Report

Branch: `claude/festive-cannon-m9kb7t`, based on the audited commit `7aa2f8b` plus the M0 audit documents (`bc8f99c`).
Scope: stabilise the existing CustomTkinter application. There is no domain generalisation, no PySide6, no new creator-platform features, and no table renames.

## Commits

| Commit | Summary |
|---|---|
| `4f2de9b` | Pin dependencies exactly; CustomTkinter capped below 6 |
| `285d720` | Versioned migrations with verified pre-upgrade backups and restore |
| `399ce85` | Link workspaces to projects by id, not title (D-01, D-02) |
| `fa89df0` | Atomic project, workspace and folder creation (D-03) |
| `4cd8ea1` | Per-user data folder, legacy import, settings-driven project folder (A-03, C-02) |
| `1342b3b` | Cross-platform folder opening (C-01) |
| `281dc0f` | Exports write files; Today's Goal can be set; proven-dead code removed (P-01, P-02, C-03/C-04) |
| `d99d97e` | UI-level tests; dashboard refresh race fixed (U-01, newly found) |
| `0f948cf` | CI on Windows, macOS and Linux with required UI tests and pip-audit |
| `59c89b1` | Windows CI fixes: POSIX rules for XDG paths in tests; fewer Tk interpreters |
| `0250f71` | CI runs each UI test in its own process (Windows Tcl interpreter limit) |

Test counts are in `M0_5_TEST_REPORT.md`, and data evidence is in `M0_5_DATA_PRESERVATION_REPORT.md`.

## Completion criteria

| Criterion | Status | Evidence |
|---|---|---|
| All 62 original tests still pass | ✅ | 62 passed; original test files unchanged since `7aa2f8b` |
| New regression tests pass | ✅ | 161 passed locally (Tk 9.0); CI green on all three OSes |
| Duplicate titles cannot cause cross-project updates | ✅ | D-01 tests, including the UI test |
| Project renaming does not break relationships | ✅ | D-02 tests |
| Failed creation leaves no inconsistent database or filesystem state | ✅ | `tests/test_project_creation_atomicity.py` (residual power-loss case: L-04) |
| Backups and migrations verified | ✅ | `tests/test_migrations.py`, 5 historical fixtures |
| Existing user data preserved | ✅ | Data preservation report §3 and §5 (fixtures; no real user database: L-03) |
| Data independent of the installation folder | ✅ | `test_full_startup_and_project_creation_never_touch_the_install_folder`, end-to-end launch |
| Cross-platform file opening implemented | ✅ (unit-tested; real launch not observed: L-07) | `tests/test_explorer_service.py` |
| Dependencies pinned | ✅ | `requirements*.txt`, `constraints.txt`; hashes not yet (L-09) |
| CI results and limitations documented | ✅ | Test report §5, known limitations |

No fix required a destructive migration. Two open points are **decisions** for you rather than defects: L-01 (how to link unlinked workspaces) and L-02 (whether to map legacy statuses).

---

## M0.5.1 — Data integrity

### D-01 Workspace status written to the wrong project (Critical)
- **Original defect:** With two projects titled "Intro", saving project 001's workspace as *Review* changed **project 002** (audit probe P1).
- **Root cause:** Workspaces had no reference to their project. `WorkspaceController.on_save_workspace` called `ProjectService.change_status_by_title`, which used `ProjectRepository.get_by_title` (`ORDER BY id DESC LIMIT 1`), so the newest project with that title was updated.
- **Changed files:** `src/database/schema.py` (migration 2), `src/models/workspace.py`, `src/database/workspace_repository.py`, `src/services/workspace_service.py`, `src/controllers/workspace_controller.py`, `src/controllers/main_controller.py`, `src/services/project_service.py`, `src/database/project_repository.py`.
- **Fix:** `Workspaces.project_id INTEGER REFERENCES Projects(id)` with a unique partial index (one workspace per project). Foreign keys are enforced per connection. Sync goes `project_id → ProjectService.change_status`. The link cannot be changed by ordinary updates, and the service always keeps the stored value. `change_status_by_title` and `get_by_title` (the only title lookup) were removed. The legacy `project_status_saver(name, status)` constructor hook remains for API compatibility, and an original test uses it, but the application no longer wires it.
- **Regression tests:** `tests/test_project_workspace_link.py`: `test_d01_duplicate_titles_update_only_the_linked_project`, `test_unlinked_workspace_never_updates_a_project_with_the_same_title`, `test_one_project_cannot_be_linked_to_two_workspaces`, `test_link_to_a_missing_project_is_rejected`, `test_migrated_duplicate_title_workspace_updates_only_its_own_project`. Also `tests/ui/test_ui_flows.py::test_workspace_screen_status_change_updates_only_its_project`.
- **Results:** pass. Run against `7aa2f8b`, the title test fails with `{'001': 'Published'} == {'001': 'Draft'}`, which shows the defect it guards against.
- **Remaining risk:** Workspaces that migration 2 cannot link with certainty stay unlinked and no longer sync to any project (see the limitations document, L-01).

### D-02 Renaming breaks sync (High)
- **Original defect:** Renaming a workspace's project name silently stopped status sync (probe P2).
- **Root cause:** Same as D-01. Once the title no longer matched, the lookup returned nothing.
- **Fix:** The ID link survives renames. Renaming a workspace does not rename the project; titles may now differ, which matches the old stored data.
- **Regression tests:** `test_d02_renamed_workspace_keeps_its_project_link`, `test_link_survives_a_form_draft_that_omits_project_id`, and the migration test covering the renamed "Alpha v2" workspace.
- **Remaining risk:** None known for linked workspaces.

### Partial write when a linked workspace has an invalid status (new, found while fixing D-01)
- **Defect:** The workspace was saved first, and then the project update raised `ValueError` for statuses such as the legacy `In Progress`. That left the workspace and project disagreeing.
- **Fix:** For linked workspaces the status is validated before anything is written.
- **Test:** `test_invalid_status_on_linked_workspace_is_rejected_before_any_write`.

### D-03 Non-atomic project creation (High)
- **Original defect:** A workspace failure left a project row and folder with no workspace (probe P4). An insert failure left an orphan folder. After restoring an older database, every creation failed with `FileExistsError` (probe P5).
- **Root cause:** Folders were created before the insert, the workspace was inserted on a separate connection, and the next number came only from the database.
- **Changed files:** `src/database/connection.py` (`transaction()`), `src/database/project_repository.py`, `src/database/workspace_repository.py`, `src/services/project_service.py`, `src/services/workspace_service.py`, `src/controllers/main_controller.py`.
- **Fix:**
  1. The scaffold is built in a hidden `.wcs-creating-<uuid>` folder.
  2. The project row and its workspace are inserted in **one** `BEGIN IMMEDIATE` transaction.
  3. The staging folder is renamed to its final name as the last step before commit.
  4. On any failure, including a failed commit after the rename, the folder is moved back and only the staging folder is removed. Pre-existing folders are never touched.
  5. The workspace is activated only after commit.
  6. The next number skips numbers already used by folders on disk.
- **Regression tests:** `tests/test_project_creation_atomicity.py` (7 tests: workspace failure, insert failure, commit failure after rename, folder appearing mid-creation, recovery after database loss, unrelated user folders preserved, success path).
- **Results:** pass. Against `7aa2f8b`: `(1, 0) == (0, 0)` (orphan project), `['001_Leo'] == []` (orphan folder), `'001' == '002'` (number collision).
- **Remaining risk:** The filesystem and the database cannot share one true transaction. A hard power loss between the rename and the commit could leave a folder without a row. That folder's number is then skipped, and no data is lost.

## M0.5.2 — Database safety

### D-04 No schema versioning, migration history or backup (High)
- **Root cause:** `initialize_database` ran `CREATE IF NOT EXISTS` plus one ad-hoc upgrade, and recorded no version.
- **Changed files:** new `src/database/migrations.py` and `src/database/backup.py`; `src/database/schema.py`; `app.py`.
- **Fix:**
  - The version is stored in `PRAGMA user_version`, and a `schema_migrations` log records version, name, time, app version and a JSON report.
  - Each migration runs in its own transaction together with its version bump.
  - An existing database is copied with the SQLite online backup API and `PRAGMA integrity_check`ed **before** any pending migration. If no backup can be made, there is no upgrade.
  - A failed step rolls back and raises `MigrationError` carrying the backup path.
  - Databases from a newer schema are refused unchanged.
  - Migration 1 is the unchanged v0.3 schema and Projects upgrade, which is idempotent for every historical shape. Migration 2 adds the project link.
- **Recovery path:** `restore_backup()` safety-backs-up the current database first, then restores a verified copy. On the command line: `python app.py --list-backups` and `python app.py --restore-backup <file>`. A failed upgrade stops startup and shows the backup path and the restore command.
- **Regression tests:** `tests/test_migrations.py` (18 tests), `tests/test_user_data.py::test_cli_lists_and_restores_backups`, `::test_failed_upgrade_stops_startup_and_explains_recovery`.
- **Remaining risk:** Backups are never pruned (L-05). The restore command is CLI-only, with no restore screen.

## M0.5.3 — User data and portability

### A-03 Data stored in the installation folder (High)
- **Fix:** New `src/utils/user_dirs.py` (standard library only). Data lives in `%APPDATA%\WonderCubs Studio`, `~/Library/Application Support/WonderCubs Studio`, or `$XDG_DATA_HOME/wondercubs-studio`, and can be overridden with `WONDERCUBS_DATA_DIR`. `AppPaths.for_current_user()` is used by `app.py`. In that mode nothing is created in the install folder.
- **Legacy migration:** `src/services/legacy_data_service.py`. On first start it copies `<install>/data/database.db` (verified copy) and `config.json` into the user folder, then writes `legacy-import.json`.
  - Legacy files are only read.
  - It never overwrites existing user data and runs once.
  - A relative or legacy-default project folder is resolved. If it was the old in-install default, new projects go to `Documents/WonderCubs Studio/Projects` and existing project folders stay where they are (their paths are in the database). This is recorded in the marker notes.
- **Tests:** `tests/test_user_data.py` (platform locations, install folder byte-identical after a full startup and project creation, import preserves data and leaves legacy files byte-identical, runs once, never overwrites, custom/relative folders, unreadable legacy settings). The end-to-end launch of the real `app.py` is recorded in the test report.

### C-02 "Default Project Folder" ignored (High)
- **Root cause:** `ProjectService` received the fixed `paths.projects_dir`.
- **Fix:** `ProjectService` accepts a folder or a callable. `MainController` passes `SettingsService.get_projects_dir`, so the saved setting applies to the next project, its preview and its numbering. `SettingsService` now:
  - keeps an unreadable file as `config.json.corrupt-<time>` and uses defaults (previously an unhandled `JSONDecodeError`);
  - falls back per value when one value is invalid;
  - resolves relative folders against the config folder;
  - saves atomically.
- **Tests:** `test_c02_saved_project_folder_controls_where_projects_are_created`, `test_project_numbering_continues_across_folder_changes`, settings robustness tests, and `tests/ui/test_ui_flows.py::test_settings_window_changes_where_the_next_project_goes`.

### C-01 Folder opening crashed on macOS and Linux (High)
- **Fix:** `src/services/explorer_service.py` uses `os.startfile` on Windows, `open` on macOS and `xdg-open` elsewhere, launched detached with no shell and the path as one argument. A missing launcher gives a clear error.
- **Tests:** `tests/test_explorer_service.py` (8 tests, including a path containing `& $HOME; rm -rf`).
- **Remaining risk:** Command selection is unit-tested, but no real file manager was opened on macOS or Windows (L-07).

### Paths with spaces and non-ASCII characters
Covered for the data root, project folder, backups and restore (including `#` and `%`, which forced percent-encoded SQLite URIs), exports, and the explorer path. Example names used: `Mes Données 日本語 & Co`, `日本語 #1 100%`, `Projects ñ`.

## M0.5.4 — Dependency and reliability

- **Pins:** `customtkinter==5.2.2`, `pytest==9.2.0`, and transitive pins in `constraints.txt`. 5.2.2 was smoke-tested on the audited commit and is used for every UI test run. 6.0.0 also passed a shallow open-every-screen smoke test, but was not tested further, so it is excluded.
- **P-01 misleading exports:** Character, workspace and prompt "Export" buttons (now "Export…") open a save dialog and write UTF-8 files atomically, with safe default names (`Zoë.json`, reserved Windows names avoided). The JSON payloads are unchanged.
- **P-02 Today's Goal:** Set Goal… / Edit Goal… and Mark Complete / Mark Incomplete on the dashboard. `DashboardRepository.save_goal` edits today's goal in place. There is validation for empty text and a 200-character limit.
- **Dead code removed (evidence: no callers in `src/` or `tests/`):** `ProjectService.get_dashboard_statistics`, `WonderCubsApp._open_video_queue`, plus the title lookup removed under D-01.
- **Kept deliberately:** legacy status counters (`In Progress`, `Uploaded`), because v0.1–v0.3 databases contain them (see the fixtures). `CharacterService.build_prompt` is tested and functional.
- **U-01 (new, found by the UI tests): spurious "Could not create project" error.** Reproduced on `7aa2f8b` under Tk 9.0: creating a project from the New Project dialog showed `invalid command name ".!ctkframe2…canvas"` although the project was created. Cause: the `project_updated` event queued `after_idle(_show_dashboard)`, and CustomTkinter processes idle tasks while building widgets, so the queued refresh destroyed the screen being built. Fix (`src/ui/app_window.py`): refreshes are coalesced and cancelled whenever navigation rebuilds the content. Tests: `test_new_project_dialog_creates_project_workspace_and_folder`, `test_dashboard_still_refreshes_after_a_project_change`. Whether it reproduces on Windows with Tk 8.6 is **unverified**.

## M0.5.5 — Automated verification
See `M0_5_TEST_REPORT.md`. CI now runs on Windows, macOS and Linux with required UI tests (Xvfb on Linux) and a pip-audit job.

## Behaviour changes (deliberate and documented)

| Change | Why |
|---|---|
| Data moves to the per-user folder on first start (copied, not moved) | A-03 |
| New installs create projects in `Documents/WonderCubs Studio/Projects` | A-03 |
| The Default Project Folder setting now takes effect | C-02 |
| Workspaces without a project link no longer change any project's status | D-01 |
| A linked workspace with a non-lifecycle status (e.g. legacy `In Progress`) cannot be saved until a valid status is chosen | prevents partial writes |
| Next project number skips numbers already used by folders | D-03 recovery |
| Export buttons save files instead of showing text | P-01 |
| Unreadable `config.json` is set aside and defaults are used | the project folder now depends on settings |
