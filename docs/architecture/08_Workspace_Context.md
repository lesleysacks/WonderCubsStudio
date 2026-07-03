# Workspace Context Architecture

Sprint 3.4 introduces the Workspace Context Engine.

The workspace is the single source of truth for the currently active production project.

```text
Workspace UI
  -> WorkspaceController
  -> WorkspaceService
  -> WorkspaceRepository
  -> SQLite
```

## Model

`Workspace` stores:

- uuid
- project_name
- lesson
- topic
- language
- target_platform
- resolution
- aspect_ratio
- duration
- style
- current_scene
- status
- created_at
- updated_at

The dataclass is frozen and designed for future expansion by adding explicit fields or structured child value objects later.

## Service

`WorkspaceService` owns:

- create_workspace()
- load_workspace()
- save_workspace()
- update_workspace()
- delete_workspace()
- switch_workspace()
- validate_workspace()
- export_context()

Validation rules:

- Project Name required
- Lesson required
- Aspect Ratio valid
- Resolution valid
- Duration positive
- Language required

## Export Contract

`export_context()` returns JSON-ready structured data for future Story, Voice, Image, Thumbnail, and SEO agents.

No AI providers are called in Sprint 3.4.

## UI Boundary

`WorkspaceWindow` communicates only with `WorkspaceController`. It does not import or use `WorkspaceRepository`.
