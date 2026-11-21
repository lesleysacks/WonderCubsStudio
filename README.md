# WonderCubs Studio

WonderCubs Studio v0.3 (in development) is a local Windows desktop application for organizing preschool video projects and preparing reusable character, workspace, and prompt context. It does not generate media or publish content.

## v0.3 scope

- Character database, repository, service, validation, prompt generation, JSON export, and Character Workspace
- Workspace Context Engine with persistence, switching, validation, and JSON export
- Provider-independent Prompt Engine foundation with versioning, preview, workspace/character context, and JSON, TXT, and Markdown export
- Project lifecycle states, automatic numbering, project creation, active-workspace selection, and dashboard synchronization
- Automated tests, continuous integration, architecture notes, and release documentation

Image Manager, Voice Manager, AI Agent Engine, publishing integration, analytics, and a one-click production pipeline are planned for later releases. The Prompt Engine performs local template rendering only and does not contact an AI provider.

## Setup

Python 3.13 and Windows 11 are the supported development environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt -c constraints.txt
python app.py
```

Run the automated checks with:

```powershell
python -m compileall app.py src tests
python -m pytest -q
python tests/ui/run_isolated.py   # UI tests, one process each (needs a display)
```

## Where your data lives

The database, settings, logs and automatic backups are stored per user, never in the application folder:

| Platform | Data folder |
|---|---|
| Windows | `%APPDATA%\WonderCubs Studio` |
| macOS | `~/Library/Application Support/WonderCubs Studio` |
| Linux | `$XDG_DATA_HOME/wondercubs-studio` (default `~/.local/share/wondercubs-studio`) |

Set `WONDERCUBS_DATA_DIR` to use another folder (for example a portable install). New projects are created in the **Default Project Folder** from Settings, which defaults to `Documents/WonderCubs Studio/Projects`.

On first start, data from an older version's application folder is copied (never moved) into the data folder; see `legacy-import.json` there.

Before every database upgrade a verified backup is written to `data/backups/`. To list or restore backups:

```powershell
python app.py --list-backups
python app.py --restore-backup "<path to backup .db>"
```

Restoring first backs up the current database, so it can be undone.

## Architecture

The application follows `UI -> Controller -> Service -> Repository -> SQLite`. See [`docs/architecture/01_System_Architecture.md`](docs/architecture/01_System_Architecture.md) and the sprint records under [`docs/sprints/`](docs/sprints/).

## Roadmap

See [`ROADMAP.md`](ROADMAP.md). Version 0.3 remains **In Development** until it is published.

## License

WonderCubs Studio is licensed under the [MIT License](LICENSE).
