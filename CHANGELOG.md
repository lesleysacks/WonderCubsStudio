# Changelog

## Version 0.2

### Added

* Dashboard
* Sidebar Navigation
* Statistics Cards
* Latest Project Panel
* Today's Goal Panel
* Dashboard Service

### Version 0.3

# Changelog

## v0.3.0 (In Development)

### Sprint 3.4.1 - Project Creation UX Improvements

#### Added

- Database-generated, read-only project numbering
- Project lifecycle status selection and persistence
- Live project-folder preview and title-field focus
- Resizable, scrollable New Project dialog
- Global Ctrl+C, Ctrl+V, Ctrl+X, and Ctrl+A support for editable text fields
- Automatic dashboard refresh, project opening, and workspace activation after project creation

#### Testing

- Added project-numbering, status, folder-preview, and project-creation regression tests

### Sprint 3.4 - Workspace Context Engine

#### Added

- Workspace model for active production project context
- Workspace repository backed by SQLite
- Workspace service with CRUD, validation, switching, and structured context export
- Workspace controller for UI action coordination
- Modular Workspace Context UI
- Workspace Context Engine tests

#### Architecture

- Workspace Context follows UI -> Controller -> Service -> Repository -> SQLite
- Workspace UI communicates only with `WorkspaceController`
- Exported workspace context is JSON-ready for future Story, Voice, Image, Thumbnail, and SEO agents
- No AI provider integration was added

#### Testing

- Added repository, service, and controller tests for Workspace CRUD, validation, export, and switching
- 39 tests passing

### Sprint 3.3 - Character Workspace UI

#### Added

- Character Workspace UI
- Character controller
- Character toolbar component
- Character list panel with live search
- Character details panel
- Character preview panel with image placeholders
- UI action smoke tests

#### Architecture

- Character Workspace follows UI -> Controller -> Service -> Repository -> SQLite
- UI uses CharacterService through CharacterController only
- No Dashboard code or repository access added to UI components

#### Documentation

- Added Character Workspace architecture documentation
- Updated README and roadmap

### Sprint 3.2 - Character Intelligence Service

#### Added

- Character service business logic layer
- Character validation rules
- Duplicate character name checks
- Structured character JSON export
- Reusable character prompt builder
- Character service unit tests

#### Logging

- Added service logs for character creation, updates, deletion, validation failures, and JSON export

#### Testing

- Added service unit tests for valid characters, missing required fields, duplicate names, long descriptions, JSON export, and prompt building

#### Documentation

- Updated Character Intelligence documentation
- Updated roadmap status for Sprint 3.2

### Sprint 3.1 - Character Database Foundation

#### Added

- Character domain model
- Character repository
- Character database schema
- Character database index
- Character repository unit tests

#### Database

- Added `Characters` table
- Added `idx_characters_name` index
- Existing tables remain unchanged

#### Testing

- Added repository unit tests
- All tests passing (6/6)

#### Documentation

- Updated Character Intelligence architecture
- Updated Database architecture documentation

---
## Sprint 3.3 – Character Workspace

### Added

- Modular Character Workspace UI
- Character Controller
- Character Toolbar
- Character List Panel
- Character Details Panel
- Character Preview Panel
- Service-only UI architecture

### Testing

- Added controller tests
- 20 tests passing

### Documentation

- Character Workspace architecture
- Sprint documentation




## v0.1.0 - Initial Release

### Added

* New Project Creator
* Project Folder Generator
* SQLite Database
* Project Management
* README Generator
* Logging System
* Settings System

### Fixed

* Initial bug fixes

### Notes

First public release of WonderCubs Studio.
