# Sprint 3.4.2 — Project Lifecycle & Dashboard Synchronization

## Objective

Make SQLite the single source of truth for project lifecycle state and refresh
dashboard data immediately after a successful persisted change.

## Architecture

The implementation follows the existing model → repository → service →
controller → CustomTkinter UI structure. `ProjectStatus` defines the lifecycle
domain. `ProjectService` owns validation, timestamps, publishing rules,
statistics, activity, and numbering. Repositories only perform SQLite queries.

## Lifecycle definitions

- Draft
- In Production
- Review
- Ready to Publish
- Published
- Archived

Active production comprises In Production, Review, and Ready to Publish.
Archived and Draft projects are excluded.

## Files added

- `src/utils/event_bus.py`
- `tests/test_project_lifecycle.py`
- `docs/sprints/Sprint-3.4.2.md`

## Files changed

- `src/models/project.py`
- `src/models/dashboard.py`
- `src/database/schema.py`
- `src/database/project_repository.py`
- `src/database/dashboard_repository.py`
- `src/services/project_service.py`
- `src/services/dashboard_service.py`
- `src/controllers/main_controller.py`
- `src/controllers/workspace_controller.py`
- `src/ui/app_window.py`
- `src/ui/workspace/workspace_window.py`
- `CHANGELOG.md`
- `ROADMAP.md`

## Database changes and migration behaviour

Projects now support `status`, `created_at`, `updated_at`, and `published_at`.
Startup inspects the existing Projects table and adds missing columns
idempotently. Null or blank statuses become Draft. Missing creation timestamps
receive the current timestamp, and missing update timestamps inherit
`created_at`. Existing rows and identifiers are preserved. Re-running startup
is safe.

## Dashboard synchronization flow

```text
Workspace editor
  → WorkspaceController
  → ProjectService
  → ProjectRepository
  → SQLite commit
  → project_updated
  → dashboard reload through DashboardService
  → current database metrics and activity
```

No dashboard-only lifecycle copy is maintained. A failed repository update
raises to the UI before an event can be emitted.

## Event flow

The dependency-free `EventBus` supports subscribe, publish, and unsubscribe.
Subscriptions are idempotent. The app subscribes once during construction,
refreshes an open dashboard after `project_updated`, and unsubscribes on close.

## Testing completed

Automated coverage includes safe legacy migration, the full lifecycle,
first-publish timestamp preservation, failed-save event atomicity, database
statistics, archived exclusion, recent ordering, collision-free next numbering,
dashboard refresh events, and duplicate subscription prevention.

The source tree and tests pass Python bytecode compilation. A lifecycle
integration smoke test was also run against a temporary SQLite database.

## Known limitations

- Workspace-to-project association currently follows the existing unique
  project-title convention because Workspaces do not yet store a project ID.
- Event delivery is synchronous and process-local, appropriate for this
  local-first desktop application.
- The project README records its creation-time status and is not used as a
  lifecycle data source.

## Future improvements

- Add an explicit `project_id` foreign key to Workspaces.
- Add lifecycle transition policy controls if product rules later prohibit
  specific transitions.
- Add richer activity history if the product needs an audit log rather than
  latest-record activity.
