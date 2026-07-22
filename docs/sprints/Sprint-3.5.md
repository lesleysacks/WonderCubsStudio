# Sprint 3.5 – Prompt Engine Foundation

## Outcome

Sprint 3.5 introduces a provider-independent Prompt Engine. It turns structured WonderCubs workspace and character data into reusable text prompts; it makes no network calls and contains no OpenAI, Gemini, Claude, or Ollama integration.

## Architecture

`PromptWindow -> PromptController -> PromptService -> PromptRepository -> SQLite`

The UI communicates only with the controller. Validation, rendering, versioning, exporting, and context composition live in `PromptService`. `PromptRepository` performs persistence only.

## Data and migration

`Prompts` has a composite primary key of `(id, version)`. This keeps all versions under one prompt identity. A partial unique SQLite index ensures that at most one version per prompt is active. Schema initialization uses `CREATE ... IF NOT EXISTS`, so existing databases retain all current tables and records.

## Behaviour

- Supported categories: Story, Image, Voice, Thumbnail, SEO, Custom.
- Valid placeholders use uppercase braces, for example `{{PROJECT_NAME}}` and `{{CHARACTER_NAME}}`.
- Workspace context supplies project name, lesson, style, language, current scene, and topic/background.
- An explicitly selected character supplies character name, voice style, and age group.
- Editing creates version `n + 1`; it does not update older rows.
- Activating a historical version deactivates the other versions.
- Exports are available as JSON, TXT, and Markdown.

## Test coverage

`tests/test_prompt_engine.py` covers CRUD, validation, placeholder replacement, preview rendering, exports, immutable versioning, activation, duplication, search, and controller actions. The full suite should be run with `python -m pytest -q` in the project virtual environment.
