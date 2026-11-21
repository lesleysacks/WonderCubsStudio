# 08 — Migration Strategy and Roadmap

Status: **Proposal. Nothing here is implemented.** Each milestone needs explicit approval before work starts.

## 1. Principles

1. **Stabilise before generalising.** Fix the verified defects first, because the generalisation migrations depend on a trustworthy migration path.
2. **Domain first, shell second.** Generalise models and services behind the current UI (keeping it shippable), then replace the UI. Never both in one milestone.
3. **Expand → migrate → contract.** Add new structures, copy or map data, run both for a release, and remove old structures only in a later release with a tested backup.
4. **Every migration is a numbered, transactional, idempotent script with a pre-migration backup and a fixture test.**
5. **No new dependency without a named need.** Planned: `PySide6` (M2, if approved), `keyring` (M5), the FFmpeg binary (M4/M6, an external tool, not a Python dependency). Dev-only: `pip-audit`, `coverage`, `pytest-qt`.

## 2. Keep / Generalise / Replace / Remove

| Decision | Items |
|---|---|
| **Preserve as-is** | Layering, repository pattern, frozen dataclass models, `EventBus`, `PromptService` versioning and rendering, lifecycle rules (`ProjectStatus`), validation-in-service pattern, real-SQLite test style, conservative never-delete-folders policy |
| **Generalise** | Project → ContentProject; Workspace → ProductionProfile on the project; Character → Identity; Prompt → Template; `PIPELINE_FOLDERS` → WorkflowTemplate; lesson/topic → ContentBrief; `target_platform`/`channel_name` → PlatformProfile/Brand; `AppPaths` → per-user data dirs + storage roots |
| **Replace** | CustomTkinter UI (M2); `os.startfile` explorer (M0.5); ad-hoc schema upgrade → migration framework (M0.5); title-based project link → `project_id` (M0.5); message-box exports → file exports (M1) |
| **Remove** | Dead code (C-04); duplicate statistics (C-03); legacy status counters after mapping; "Coming Soon" Analytics nav item; the separate Workspace screen once folded into projects (M1/M2) |

## 3. Domain generalisation mappings

### 3.1 Project → ContentProject (in place, additive)
| Legacy | New | Rule |
|---|---|---|
| `Projects.id` | unchanged | — |
| `video_number` | `sequence_code` (keep `video_number` column until contract phase) | Copy. Numbering becomes per-series; existing projects join a default series "WonderCubs" so their numbers keep their meaning |
| `title` | `title` | — |
| `lesson` | `ContentBrief.objective` | Copy; the column is kept read-only for one release |
| `status` | `stage` via the default workflow template | 1:1 map of the 6 states; legacy `Uploaded`→`Published`, `In Progress`→`In Production` |
| `folder_path` | `storage_root` + `relative_path` | Split when under a known root; otherwise keep absolute and flag |
| — | `content_type`, `series_id`, `brand_id`, `due_at`, `deleted_at` | New, nullable |

### 3.2 Workspace → ProductionProfile (fixes D-01/D-02)
1. Migration adds `Workspaces.project_id`. Backfill by exact title match with 1:1 pairing in creation order. Unmatched or ambiguous rows are listed in a migration report shown to the user, and **no row is deleted**.
2. Fields `language`, `target_platform`, `resolution`, `aspect_ratio`, `duration`, `style` move to `production_profiles` (FK `project_id`). `current_scene` becomes the first `Scene` record. `topic` maps to `ContentBrief.summary`.
3. `WorkspaceService` keeps its public API as a thin adapter over the project during M1, so the 16 existing workspace test functions keep passing.
4. The "active workspace" becomes "last opened project", persisted.

### 3.3 Character → Identity
| Legacy | New |
|---|---|
| `uuid`, `name`, `description`, `personality`, `catchphrase`, `voice_style`, `age_group`, `gender` | Core `identities` columns (kind = `animated_character`) |
| `species`, `fur_color`, `mane_color`, `eye_color`, `shirt`, `pants`, `shoes`, `accessories` | `attributes` JSON, keyed by the original column name, plus an identity-kind schema that tells the UI which fields to show |
| `image_folder` | Identity ↔ Asset links (once the asset store exists); the path is kept until then |

New kinds: `human_talent` (with consent and usage-rights dates), `voice_profile`, `brand_persona`. The `Characters` table stays, populated, until the contract release. `CharacterService` becomes a façade over `IdentityService(kind=animated_character)`, so `export_json` output is byte-identical (golden-file test).

### 3.4 Prompt → Template
Already versioned with `(id, version)`. Add `kind` (prompt, brief, script_outline, seo, checklist), `tags`, and `output_format`. The fixed `CATEGORIES` become seed tags, and existing rows get `kind='prompt'` with `tags=[category]`. Add a per-template variable schema (name, label, type, default) so the UI can render inputs (fixes P-03).

### 3.5 Fixed folders → WorkflowTemplate
The current 10 folders and placeholder files become a seeded template "Animated Episode (Classic)". Projects record which template and version created them. Existing project folders on disk are **never restructured**.

## 4. Milestone roadmap

Sizes are rough estimates for one developer.

### M0 — Technical audit and architecture approval *(this deliverable)*
- **Deliverables:** `docs/audit/01–08`. After approval: `docs/architecture/GLOBAL_DESKTOP_ARCHITECTURE.md`, plus a 2-day toolkit spike (cold start, package size, three-panel docked layout, file dialogs on Windows/macOS/Linux).
- **DoD:** Documents reviewed; architecture decision recorded as ADR-002; issue tracker reconciled (close #12, #23, #24, #26, #27; re-scope #7).

### M0.5 — Stabilisation (recommended insertion) · **M, 2–3 weeks**
- **Objectives:** Make current data trustworthy and migratable.
- **Deliverables:** Migration framework with backup (D-04); `project_id` link (D-01/D-02); atomic project creation (D-03); cross-platform folder opener (C-01); settings-driven project root (C-02); per-user data dir with legacy copy (A-03); lock file with hashes (S-01); CI matrix with three OSes and pip-audit (T-02); regression tests for probes P1–P13 (T-03).
- **Files:** `src/database/schema.py`, new `src/database/migrations/`, `connection.py`, `project_service.py`, `project_repository.py`, `workspace_*`, `main_controller.py`, `explorer_service.py`, `utils/app_paths.py`, `app.py`, `requirements*.txt`, `.github/workflows/tests.yml`, `tests/fixtures/db/`.
- **Acceptance:** Each probe has a test that passed after the fix and was shown to fail before it; v0.1/v0.2/v0.3 fixture DBs upgrade with identical row counts; backup file created and restorable; suite green on all three OSes.
- **Risks:** Ambiguous duplicate-title backfill (surface it, never guess); first-run data copy on Windows paths with OneDrive redirection.

### M1 — Universal creator domain foundation · **L, 4–6 weeks**
- **Objectives:** The §3 mappings, behind the current UI.
- **Deliverables:** ContentProject, Series, ContentBrief, ProductionProfile, Identity (+ kinds), Template (kind, variables), WorkflowTemplate, Tags, soft delete + Trash, UTC clock utility, Unicode slugs, file exports (P-01), goal editing or panel removal (P-02), `ApplicationContainer` split (A-02).
- **Acceptance:** All legacy tests pass unchanged or through façades; golden-file tests for legacy exports; migration preservation tests per §04 §4.
- **Risks:** Over-generalisation. Mitigation: each new field must map to a journey in the screen specifications.

### M2 — New desktop foundation and design system · **L, 4–6 weeks**
- **Prerequisite:** UX screen specifications and user journeys approved, *before* implementation.
- **Deliverables:** New shell (toolkit per ADR-002), design tokens (light/dark), resizable sidebar, command palette, keyboard map, job runner with progress and cancel (C-11), error and empty-state patterns, i18n scaffolding (all strings externalised, locale-aware dates and numbers). The old UI is retained until parity, then removed.
- **Acceptance:** Every existing journey (create project, edit character, edit template, preview, export) is reproducible in the new shell; UI tests pass in CI on three OSes; keyboard-only navigation of the main flows.
- **Risks:** Scope creep into features. The shell ships with **parity only**.

### M3 — Command Centre and production workspaces · **L**
Dashboard with deadlines, projects table (filter/sort), project workspace tabs (Brief, Script editor with versions, Scenes, Tasks/Checklist from the workflow template, Reviews), FTS5 global search. **Depends on:** M1, M2.

### M4 — Asset and identity library · **L**
Content-addressed asset store (copy-in, hash, metadata, thumbnails in a worker process), tags, collections, brand kits, identity↔asset links, missing-file handling (D-07). **Depends on:** M1 storage roots, M2 job runner.

### M5 — AI provider integrations · **L**
Provider port, keychain `SecretStore` (S-02), one text adapter + one image adapter + one voice adapter, usage and cost metering, assistants as template + adapter, results saved as assets with provenance. **Depends on:** M1 templates, M4 assets. **Risk:** API churn; keep adapters thin and isolated.

### M6 — Distribution and publishing · **M (manual-first)**
Platform profiles, metadata validation, calendar, export presets with FFmpeg render recipes, publishing checklist and handoff. Direct integrations: at most one, chosen post-launch by demand (§07 §3).

### M7 — Analytics and performance · **M**
Manual and CSV performance import, cost entries, AI cost roll-up, per-project profitability, series trends.

### M8 — Packaging and global release readiness · **L**
Signed installers (MSIX/NSIS, notarised DMG, AppImage/Flatpak), auto-update, first-run storage-location choice, backup/restore UI, crash reporting (opt-in), translations for 2–3 launch languages, release automation with SHA-pinned actions (S-05). **Note:** packaging spikes belong in M2, not deferred to M8. Signing and notarisation surprises are the most common late-stage blocker.

## 5. Dependency graph

```
M0 ─► M0.5 ─► M1 ─┬─► M3 ─┐
                  ├─► M4 ─┼─► M5 ─► M6 ─► M7
       M0 spike ─► M2 ──┘          │
                                     └─────────► M8 (packaging spikes start in M2)
```

## 6. Critical risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Data loss during generalisation migrations | Medium | Critical | Backups, expand/contract, fixture tests, migration report |
| Scope (six modules) exceeds one-person capacity | High | High | Beachhead segment; manual-first E/F; parity-only shell |
| Toolkit choice regretted after M2 | Medium | High | 2-day spike with measured criteria before ADR-002 |
| Platform API dependency (publishing, analytics) | High | Medium | Manual/CSV-first; isolate adapters |
| Cross-platform packaging and signing late surprises | Medium | High | Packaging spike in M2; CI installers early |
| Unpinned UI dependency breaks the current app | High (already drifted to 6.0) | Medium | Pin `customtkinter<6` now until M2 |
