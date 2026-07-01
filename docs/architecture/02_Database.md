# Database

WonderCubs Studio uses SQLite for local application data.

## Tables

### Projects

Stores video project metadata and folder locations.

### Goals

Stores dashboard production goals by date.

### Characters

Added in v0.3 Sprint 3.1 as the backend foundation for the Character Intelligence System.

Columns:

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

Indexes:

- Primary key on `uuid`
- Name index for character listing and future lookup workflows

The `Characters` table is created with `CREATE TABLE IF NOT EXISTS` during database initialization, so existing project and dashboard data is preserved.
