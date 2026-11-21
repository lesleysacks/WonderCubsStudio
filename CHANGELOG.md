# Changelog

## M0.5 Stabilisation (unreleased)

### Fixed

- Workspace status changes could update the wrong project when titles were duplicated, and stopped syncing after a rename; workspaces now link to projects by id
- Project creation is atomic across the project row, its workspace and its folder; failures leave nothing behind, and creation recovers when folders outlive their database rows
- Opening a project folder crashed on macOS and Linux
- The Default Project Folder setting was saved but ignored
- Creating a project from the New Project dialog could show a spurious "Could not create project" error
- Exports only displayed text; they now save files
- Today's Goal could not be set

### Added

- Schema versioning, transactional migrations, verified pre-upgrade backups, and `--list-backups` / `--restore-backup`
- Per-user data folder with a one-time, non-destructive import of older data
- UI-level tests and CI on Windows, macOS and Linux

### Changed

- Dependencies pinned exactly (`customtkinter==5.2.2`); see `constraints.txt`
- An unreadable settings file is kept aside and defaults are used

## v0.3.0 (In Development)

### Added

- Character database, repository, service, validation, prompt builder, JSON export, and Character Workspace
- Workspace Context Engine with persistence, validation, active-workspace switching, and JSON export
- Database-generated project numbering, lifecycle states, live folder preview, title focus, clipboard shortcuts, and workspace activation
- Persisted lifecycle updates, dashboard synchronization, recent activity, and safe schema migration
- Provider-independent Prompt Engine with versioned templates, local context rendering, preview, activation, duplication, search, and JSON/TXT/Markdown export
- Automated test workflow for Python 3.13

### Fixed

- Prompt Engine test collection now defines its test-data helper before parameter evaluation
- Release scope, roadmap ordering, metrics, contribution guidance, and license metadata now agree with the repository

### Notes

- v0.3 remains in development until automated checks and the Windows smoke test pass and a release is published.
- Image Manager, Voice Manager, AI Agent Engine, publishing, analytics, and one-click production are not part of v0.3.

## v0.2.0

### Added

- Dashboard home and sidebar navigation
- Statistics cards, latest-project panel, today's-goal panel, and dashboard service

## v0.1.0 - Initial Release

### Added

- Project creator and folder generator
- SQLite project management
- README generator, logging, and settings
