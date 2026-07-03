# System Architecture

WonderCubs Studio uses a layered desktop architecture:

```text
Presentation
  -> Controllers
  -> Services
  -> Repositories
  -> Persistence
```

Presentation components are CustomTkinter windows and frames. They handle user interaction and delegate actions to controllers.

Controllers translate UI events into service calls. They do not persist data directly.

Services own business rules, validation, switching behavior, and export formatting.

Repositories own SQLite reads and writes only.

Persistence is centralized in SQLite schema initialization and local project assets.

## Workspace Context Engine

Sprint 3.4 adds the Workspace Context Engine as the single source of truth for the currently active production project.

The flow is:

```text
WorkspaceWindow
  -> WorkspaceController
  -> WorkspaceService
  -> WorkspaceRepository
  -> Workspaces table
```

Future AI agents consume `WorkspaceService.export_context()` output instead of requesting production project details independently.
