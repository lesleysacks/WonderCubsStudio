# Character Workspace Architecture

Sprint 3.3 introduces the Character Workspace UI.

The workspace follows the same Clean Architecture flow as the backend:

```text
UI components
  -> CharacterController
  -> CharacterService
  -> CharacterRepository
  -> SQLite
```

The UI does not access `CharacterRepository` directly. All save, delete, duplicate, search, and export actions are coordinated by `CharacterController` and validated by `CharacterService`.

## Components

- `character_window.py`: workspace composition and user action orchestration
- `character_toolbar.py`: top-level workspace actions
- `character_list_panel.py`: search, selection, add, duplicate, and delete controls
- `character_details_panel.py`: editable character profile fields
- `character_preview_panel.py`: image placeholders, folder selection, and existing PNG previews

## Controller

`CharacterController` owns UI action methods:

- `on_new_character()`
- `on_save_character()`
- `on_delete_character()`
- `on_duplicate_character()`
- `on_export_character()`
- `on_search_changed()`

The controller communicates only with `CharacterService`.

## Error Handling

Validation and missing-record exceptions from `CharacterService` are converted into user-facing message boxes by the workspace frame.

No errors are printed from UI code.

## Image Preview

The preview panel expects these optional files inside the selected image folder:

- `Front.png`
- `Side.png`
- `Back.png`
- `Portrait.png`

Sprint 3.3 displays existing files only. It does not generate images.
