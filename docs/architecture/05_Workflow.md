# v0.3 Application Workflow

1. A user creates a numbered project and its local folder structure.
2. The controller refreshes project data and creates or selects the active workspace context.
3. Lifecycle changes persist to SQLite before a project event refreshes the dashboard.
4. A user creates or selects reusable character data through the Character Workspace.
5. The Prompt Engine combines a versioned template with explicit values, active workspace context, and optional character context.
6. The rendered prompt can be previewed or exported as JSON, TXT, or Markdown.

All generation in v0.3 is deterministic and local. Media creation, AI-provider calls, publishing, and analytics are outside this workflow.
