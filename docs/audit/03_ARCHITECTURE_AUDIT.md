# 03 — Architecture Audit

## 1. As-built architecture (verified)

```
app.py
  └─ AppPaths(base_path = directory of app.py)          ← data lives next to code
  └─ SettingsService(config.json)
  └─ initialize_database(data/database.db)
  └─ MainController  (composition root + facade)
        ├─ ProjectService ── ProjectRepository ──┐
        ├─ DashboardService ── DashboardRepository┤
        ├─ CharacterService ── CharacterRepository┤──► SQLite (one file, no FKs, user_version = 0)
        ├─ WorkspaceService ── WorkspaceRepository┤
        ├─ PromptService ── PromptRepository ─────┘
        │      └─ uses WorkspaceService + CharacterService for context
        ├─ CharacterController / WorkspaceController / PromptController
        ├─ ExplorerService (os.startfile)
        └─ EventBus ("project_updated")
  └─ WonderCubsApp (CustomTkinter) ── calls MainController / sub-controllers only
```

Dependency direction is correct: UI → controllers → services → repositories → SQLite. No service imports UI code, and no repository holds business rules. `PromptService` depends on two sibling services, which is acceptable composition, but that is where cross-module coupling will grow.

## 2. Strengths to preserve

| Strength | Evidence |
|---|---|
| Strict layering, UI-independent domain | No `customtkinter`/`tkinter` import outside `src/ui` (grep verified) |
| Immutable models | All `@dataclass(frozen=True)` |
| Repository pattern (ADR-001) | One repository per aggregate |
| Event bus decouples refresh | `utils/event_bus.py`, idempotent subscribe |
| Provider-independent prompt engine | No network code anywhere (grep for `http`, `requests`: none) |
| Controllers are testable without UI | `tests/test_*_controller.py` |

## 3. Findings

### A-01 Workspace is a second Project, linked by a title string — **Critical** — Verified (Probes P1, P2)
- **Evidence:** `MainController.create_project` (`main_controller.py:58–70`) creates a `Project` and then a separate `Workspace` copying title, lesson and status. Synchronisation runs through `WorkspaceController.on_save_workspace` → `ProjectService.change_status_by_title` (`workspace_controller.py:33–41`, `project_service.py:116–121`) → `ProjectRepository.get_by_title` (`ORDER BY id DESC LIMIT 1`). `Workspaces` has no `project_id` column.
- **Impact:** With duplicate titles, the *newest* project receives another project's status (P1). After a rename, sync silently stops (P2). The dashboard then reports false production state.
- **Fix:** Add `project_id` to the workspace data and backfill it by `(title, created order)`. Then fold the workspace fields into a `ProductionProfile` owned by the project (see `08_MIGRATION_STRATEGY.md` §3.2). "Active workspace" becomes "open project".
- **Dependencies:** D-04 (migration framework) must land first.

### A-02 `MainController` is a god-object composition root — **Medium** — Verified
- **Evidence:** It constructs every repository, service and controller and also exposes project operations directly (`main_controller.py:31–122`).
- **Impact:** Every new module edits this file, and replacing the UI means re-implementing its facade.
- **Fix:** Split into an `ApplicationContainer` (wiring only) and per-module controllers or use-case services. The new UI binds to those.

### A-03 Data is stored inside the installation directory — **High** — Verified (by reading)
- **Evidence:** `app.py:17` sets `base_path = Path(__file__).resolve().parent`. `AppPaths` derives `data/`, `logs/`, `projects/` and `config.json` from it (`utils/app_paths.py`).
- **Impact:** Installed builds cannot write under `C:\Program Files` or a signed macOS bundle. An update or reinstall can wipe user data. Backup is unclear to users.
- **Fix:** Per-OS user data directories (`%APPDATA%`, `~/Library/Application Support`, `$XDG_DATA_HOME`), resolved by a ~20-line helper, so no new dependency is needed. Projects default to `Documents/WonderCubs Studio`. On first run, **copy** (never move) legacy data into place and leave a marker file.

### A-04 Active context is in-memory only — **Medium** — Verified (Probe P6)
- **Evidence:** `WorkspaceService._current_workspace_uuid` (`workspace_service.py:30`). After a restart there is no active workspace.
- **Fix:** Persist "last opened project" in user state (not in `config.json`, which holds preferences).

### A-05 No background job, plugin or integration boundary — **Medium (blocking for M4–M7)** — Verified
- **Evidence:** None exists. AI, media and publishing features would otherwise be written directly inside services.
- **Fix:** Define ports in M1–M2: a `JobRunner`, `AssetStore`, `SecretStore`, and `ProviderAdapter` interfaces (AI and publishing). Adapters live outside the domain package.

### A-06 Cross-platform assumptions — **High** — Verified
Windows-only calls (C-01), the Segoe UI font (C-12), and Windows-only setup docs (`README.md`). CI runs only on `ubuntu-latest` and **cannot execute the UI**, so platform behaviour is untested.

## 4. Platform compatibility matrix (current code)

| Concern | Windows | macOS | Linux | Evidence |
|---|---|---|---|---|
| Domain/services | ✅ (assumed) | ✅ (assumed) | ✅ verified | tests pass on Linux |
| Open folder | ✅ | ❌ | ❌ verified | C-01 |
| UI launch | Unverified | Unverified | Not executed | No Tk/display in the audit environment |
| Fonts | ✅ | ⚠ fallback | ⚠ fallback | C-12 |
| Data location | ⚠ fails under Program Files (assumed) | ⚠ | ⚠ | A-03 |

## 5. Forward architecture — preliminary options (formal doc deferred to Phase One)

The formal comparison and decision record (`docs/architecture/GLOBAL_DESKTOP_ARCHITECTURE.md`) needs your approval to start Phase One. This is the audit's preliminary view, so the roadmap can be sized.

**Facts that drive the decision:**
- The reusable asset is about **1,300 statements of Python domain, service and repository code at ~86 % coverage**. The UI (~900 statements, 0 % coverage) is replaced in every option.
- One maintainer (all 20 commits share one author).
- Local-first with SQLite. Future needs include media (FFmpeg as a subprocess in every option), AI over HTTP (Python has the broadest SDK support), and background jobs.

| Criterion | A. Python + PySide6 | B. Tauri 2 + React/TS + Python sidecar | C. Electron + React/TS (+ Python sidecar) |
|---|---|---|---|
| Reuse of existing services | Direct import, zero boundary | Via IPC/HTTP sidecar. Every call needs a serialised contract | Same as B |
| Languages to master | 1 (Python) | 3 (Rust, TypeScript, Python) | 2–3 |
| Windows/macOS/Linux | Mature (Qt 6) | Good. Linux WebKitGTK and macOS WebKit rendering differ from Windows WebView2 | Most uniform (bundled Chromium) |
| UI ceiling, "pro creative tool" feel | High (docking, model/view tables, custom painting), but styling takes discipline | Highest velocity for a polished modern UI | Same as B |
| Memory/footprint | ~80–150 MB RAM, ~60–120 MB package (assumption) | Smallest shell, but the bundled Python sidecar adds ~40–80 MB | Largest (~150–300 MB RAM) |
| Background jobs | `QThreadPool`/`concurrent.futures` in-process | Sidecar process: good isolation, more plumbing | Same as B |
| Media playback/preview | QtMultimedia (adequate); FFmpeg for processing | HTML5 media (good for preview) | Same as B |
| Packaging | PyInstaller/Nuitka/Briefcase. Code signing and notarisation are manual work | First-class bundler and signing, but the Python sidecar must also be frozen and signed | electron-builder, mature |
| Auto-update | **Weakest.** No built-in updater; needs a custom or third-party one | Built-in updater plugin | Mature `autoUpdater` |
| i18n | Qt Linguist, built in | i18next etc. | Same as B |
| Licensing | PySide6 is LGPL-3. Fine for commercial use with dynamic linking; ship notices | MIT/Apache | MIT |
| Long-term maintenance for one developer | Lowest | Highest (three toolchains and an IPC contract) | High |

**Preliminary recommendation: A (Python + PySide6)**, because it keeps the verified domain code in-process, keeps one language for a single maintainer, and Qt's docking and model/view widgets fit dense, multi-panel production workspaces. Its known costs, which must be budgeted in M8, are auto-update and signing/notarisation.

**What would change the recommendation to B (Tauri):** a plan to hire front-end web engineers; a requirement for a browser or cloud companion sharing UI code; or a design direction that relies heavily on web-native motion and layout. If B is chosen, the Python services should run as a **local sidecar exposing a versioned JSON-RPC API**, and that contract should be built first.

Electron (C) is not recommended. It has B's sidecar complexity plus the highest memory cost, and no capability the product needs is unavailable in A or B.

The concrete next steps (a two-day PySide6 spike measuring package size, cold start and a docked three-panel layout on all three OSes) are listed in `08_MIGRATION_STRATEGY.md`.
