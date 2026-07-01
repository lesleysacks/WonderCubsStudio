''''''classDiagram'''''''

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
        +save(Character) bool
        +findById(id) Character
        +findAll() List~Character~
        +update(Character) bool
        +delete(id) bool
    }

    class PromptBuilder {
        +buildSystemPrompt(Character) string
        -interpolateTemplate(template, data) string
    }

    class Character {
        +int id
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
        +to_json() string
    }

    %% Relationships
    CharacterController --> CharacterService : Depends on
    CharacterService --> CharacterRepository : Uses for CRUD
    CharacterService --> PromptBuilder : Uses for Prompt Generation
    CharacterRepository ..> Character : Manages Lifecycles of
    PromptBuilder ..> Character : Extracts Data From


    ''''''sequenceDiagram'''''''
    
    autonumber
    actor User
    participant UI as CharacterWindow (UI)
    participant Ctrl as CharacterController
    participant Serv as CharacterService
    participant Repo as CharacterRepository
    participant DB as SQLite Database

    User->>UI: Click "Save Character"
    activate UI
    UI->>UI: Gather form data (Name, Species, Colors, etc.)
    
    UI->>Ctrl: handleSaveCharacter(formData)
    activate Ctrl
    
    Ctrl->>Serv: createCharacter(characterData)
    activate Serv
    
    Note over Serv: Validates data fields<br/>(e.g., checks if Name is empty)
    
    Serv->>Repo: save(CharacterObject)
    activate Repo
    
    Repo->>DB: INSERT INTO characters (...)
    activate DB
    DB-->>Repo: Return Row ID / Success Confirmation
    deactivate DB
    
    Repo-->>Serv: return true (Success)
    deactivate Repo
    
    Serv-->>Ctrl: return CharacterObject (Saved State)
    deactivate Serv
    
    Ctrl-->>UI: Trigger Success Callback / Update UI List
    deactivate Ctrl
    
    UI-->>User: Display "Character Saved Successfully!" popup
    deactivate UI