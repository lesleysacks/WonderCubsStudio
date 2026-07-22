# Sprint 3.4.1 - Project Creation UX Improvements

## Objective

Make Project Creation feel like a reliable desktop workflow while preserving the existing layered architecture.

## Delivered

- Project numbers are calculated from SQLite and displayed read-only in the dialog.
- The dialog has a live folder-path preview, automatic title focus, status selection, resizing, and scrolling.
- Supported statuses are Draft, In Production, Review, Ready to Publish, Published, and Archived. Draft is the default.
- Standard Ctrl+C, Ctrl+V, Ctrl+X, and Ctrl+A shortcuts are available in editable text fields.
- Creating a project refreshes the dashboard, opens the project, displays the refreshed project list, and creates and activates its workspace context.

## Architecture

```text
Presentation -> MainController -> ProjectService / WorkspaceService
             -> ProjectRepository / WorkspaceRepository -> SQLite
```

The UI does not access SQLite directly. Project number calculation and folder preview remain in the ProjectService, while the controller coordinates workspace activation.

## Testing

- Project number generation
- Status validation, persistence, and README output
- Live folder-preview service behavior
- Project folder/database creation regression coverage

## Suggested Sprint 3.5

- Add controlled project status transitions.
- Link the project record and workspace record with a stable identifier.
- Let Story Agent inputs consume the active workspace context.
