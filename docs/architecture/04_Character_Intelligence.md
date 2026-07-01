# Character Intelligence

The Character Intelligence System provides reusable character records for future story, image, voice, thumbnail, and animation workflows.

Sprint 3.1 implements the backend foundation only:

- `Character` dataclass model
- `Characters` SQLite table
- `CharacterRepository` CRUD/search/existence methods
- Unit tests for persistence behavior

No UI, dashboard navigation, prompt builder, controller, or service layer is implemented in this sprint.

## Data Model

The `Character` model contains:

- uuid
- name
- species
- gender
- age_group
- fur_color
- mane_color
- eye_color
- shirt
- pants
- shoes
- accessories
- personality
- voice_style
- catchphrase
- description
- image_folder
- created_at
- updated_at

## Repository

`CharacterRepository` owns SQLite persistence for character records.

Methods:

- `create()`
- `update()`
- `delete()`
- `get_by_id()`
- `get_all()`
- `search()`
- `exists()`

All repository methods use parameterized SQL queries, log failures, and re-raise SQLite exceptions for the caller to handle.

## Planned Architecture

```mermaid
classDiagram
    class CharacterController {
        -CharacterService characterService
        +handleSaveCharacter(formData) void
        +handleDeleteCharacter(id) void
        +showCharacterList() void
        +generateCharacterPrompt(id) string
    }

    class CharacterService {
        -CharacterRepository repository
        -PromptBuilder promptBuilder
        +createCharacter(characterData) Character
        +getCharacterById(id) Character
        +getAllCharacters() List~Character~
        +updateCharacter(id, characterData) bool
        +deleteCharacter(id) bool
        +buildPromptForCharacter(id) string
    }

    class CharacterRepository {
        -DatabaseConnection db
        +create(Character) Character
        +get_by_id(id) Character
        +get_all() List~Character~
        +update(Character) bool
        +delete(id) bool
        +search(text) List~Character~
        +exists(id) bool
    }

    class PromptBuilder {
        +buildSystemPrompt(Character) string
        -interpolateTemplate(template, data) string
    }

    class Character {
        +string uuid
        +string name
        +string species
        +string gender
        +string age_group
        +string fur_color
        +string mane_color
        +string eye_color
        +string shirt
        +string pants
        +string shoes
        +string accessories
        +string personality
        +string voice_style
        +string catchphrase
        +string description
        +string image_folder
        +datetime created_at
        +datetime updated_at
    }

    CharacterController --> CharacterService : Depends on
    CharacterService --> CharacterRepository : Uses for CRUD
    CharacterService --> PromptBuilder : Uses for prompt generation
    CharacterRepository ..> Character : Manages lifecycles of
    PromptBuilder ..> Character : Extracts data from
```
