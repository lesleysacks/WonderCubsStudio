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
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python app.py
```

Run the automated checks with:

```powershell
python -m compileall app.py src tests
python -m pytest -q
```

Runtime data is stored locally in SQLite. Generated databases, logs, exports, projects, caches, and virtual environments are excluded by `.gitignore`.

## Architecture

The application follows `UI -> Controller -> Service -> Repository -> SQLite`. See [`docs/architecture/01_System_Architecture.md`](docs/architecture/01_System_Architecture.md) and the sprint records under [`docs/sprints/`](docs/sprints/).

## Roadmap

See [`ROADMAP.md`](ROADMAP.md). Version 0.3 remains **In Development** until it is published.

## License

WonderCubs Studio is licensed under the [MIT License](LICENSE).
