# 02 — Codebase Audit

Scope: `app.py`, `src/**` (46 files, ≈3,950 lines including the UI) at commit `7aa2f8b`. Line numbers refer to that commit.

## 1. Inventory

| Layer | Files | Lines (approx.) | Test coverage | Assessment |
|---|---|---|---|---|
| Models (`src/models`) | 6 | 190 | 91–100 % | Keep. Frozen dataclasses, no I/O. |
| Repositories (`src/database`) | 7 | 840 | 80–95 % | Keep the pattern; consolidate the connection and transaction handling. |
| Services (`src/services`) | 7 | 955 | 55–94 % | Keep. This is where the business value lives. |
| Controllers (`src/controllers`) | 4 | 315 | 78–92 % | Keep as the application-facing API. |
| UI (`src/ui`) | 10 | 1,100 | **0 %** | Replace in M2. Do not invest further. |
| Utils (`src/utils`) | 3 | 108 | 78–100 % | Keep `EventBus` and `AppPaths`. Extend `AppPaths`. |

## 2. Feature completion: actual versus documented

| Feature | Docs say | Actual (verified) |
|---|---|---|
| Project creation, numbering, scaffold | Done | Done. Defects D-01, D-03 (see doc 04). |
| Lifecycle states and dashboard sync | Done | Done. |
| Character CRUD, search, duplicate | Done | Done. |
| Character JSON export | Done | **Partial.** A payload is built (`character_service.py:92`) but the UI only displays it in a message box (`character_window.py:143`). No file is written. |
| Character prompt builder | Open issue #7 | **Implemented in the service** (`character_service.py:127`), never called by the app. Superseded by the Prompt Engine context. |
| Workspace Context Engine | Done (issue #12 still open) | Done. Duplicates Project (A-01). |
| Workspace JSON export | Done | **Partial.** Shown in a message box only (`workspace_window.py:222`). |
| Prompt export JSON/TXT/MD | Done | **Partial.** Rendered string shown in a message box (`prompt_window.py:135`). |
| Prompt preview with variables | Done | **Partial.** The UI cannot supply custom variable values. Only a character UUID typed by hand (`prompt_window.py:58`). Templates with custom placeholders always fail preview. |
| Today's Goal | v0.2 "Done" | **Read-only.** No code anywhere inserts into `Goals`. |
| Settings | v0.1 "Done" | **Partial.** Saved, but only `default_project_folder`, `resolution`, `fps` and the names are stored, and none are consumed (C-02). |
| Analytics | Not claimed | Placeholder screen plus a "Coming Soon" message box (`app_window.py:263–270`). Honest, but it occupies navigation. |

## 3. Findings

### C-01 Windows-only folder opening crashes on macOS and Linux — **High** — Verified (Probe P11)
- **Evidence:** `src/services/explorer_service.py:17` calls `os.startfile`, which exists only on Windows. On Linux it raises `AttributeError: module 'os' has no attribute 'startfile'`. It is called after every project creation (`app_window.py:297`).
- **Impact:** A core flow fails on two of the three target platforms.
- **Fix:** A platform adapter: `os.startfile` on Windows, `open` on macOS, `xdg-open` on Linux, all through `subprocess.run([...])` with a list argument (no shell). Or use the toolkit's own call (`QDesktopServices.openUrl` in Qt).
- **Risk:** Low. It is isolated behind `ExplorerService`.

### C-02 "Default Project Folder" setting is ignored — **High** — Verified (Probe P3)
- **Evidence:** `main_controller.py:40–42` constructs `ProjectService` with `paths.projects_dir`. `SettingsService.load()` is never consulted for project creation. The probe saved a custom folder and the project was still created under `<app>/projects`.
- **Impact:** Users believe they control where their files go, and they do not. This is a trust and data-ownership defect.
- **Fix:** Resolve the projects root from settings at creation time, validate that it is writable, and store project paths relative to a named storage root (see D-07).
- **Risk:** Medium. Existing absolute `folder_path` values must keep working.

### C-03 Duplicate statistics implementations — **Low** — Verified
- **Evidence:** `DashboardRepository.get_statistics()` (`dashboard_repository.py:20–54`) and `ProjectService.get_dashboard_statistics()` (`project_service.py:123–134`) compute the same thing. The latter has no callers, including tests. The repository version also counts legacy statuses `"Uploaded"` and `"In Progress"`, which no code path can produce any more.
- **Fix:** Keep one implementation in the service, backed by a single `GROUP BY` repository query. Map legacy statuses once in a migration.

### C-04 Dead code — **Low** — Verified
- `WonderCubsApp._open_video_queue` (`app_window.py:305`) has no caller.
- `CharacterService.build_prompt` has no production caller.
- `ProjectService.get_dashboard_statistics` has no caller.
- `ProjectListWindow(mode="queue")` is unreachable.
- **Fix:** Remove during M1, or route `build_prompt` through the Prompt Engine.

### C-05 Domain vocabulary is hard-wired to one niche — **Medium** — Verified
- **Evidence:** `Character` fields `fur_color`, `mane_color` (`models/character.py`). `Project.video_number` and `lesson`. `Workspace.lesson`, default `target_platform="YouTube"`. `AppSettings.channel_name`. Fixed `PIPELINE_FOLDERS` including `SEO`/`Upload` (`project_service.py:23–38`). UI strings "Video Title", "Next Video", "Leo Learns Colors". Window title hard-codes "v0.3".
- **Impact:** Blocks every non-preschool audience in the vision.
- **Fix:** Generalise per `08_MIGRATION_STRATEGY.md` §3. Do not rename tables blindly.

### C-06 Timestamps are naive local time — **Medium** — Verified
- **Evidence:** Every model and service uses `datetime.now().strftime("%Y-%m-%d %H:%M:%S")` (for example `models/character.py:9`, `project_service.py:228`). The repeated helper exists five times. `schema.py` defaults use SQLite `CURRENT_TIMESTAMP`, which is UTC, so **two time bases are mixed in the same columns**.
- **Impact:** Ordering and "recent activity" break across DST changes, time-zone moves, and any future sync.
- **Fix:** Store UTC ISO-8601 (`datetime.now(timezone.utc).isoformat()`) through one `clock` utility and format to local time only in the UI. Migrate existing values by treating them as local time at migration (documented assumption).

### C-07 Non-ASCII titles lose their meaning in folder names — **Medium** — Verified
- **Evidence:** `ProjectService._slugify` (`project_service.py:211`) uses `[^A-Za-z0-9]+`. `"Café Été"` becomes `"Caf_t"`; `"こんにちは"` becomes `"Untitled"`.
- **Impact:** International users get meaningless folder names.
- **Fix:** Unicode-aware slug: NFC normalise, keep `str.isalnum()` characters, strip OS-reserved characters (`<>:"/\|?*`, control characters, Windows reserved names), cap the length.

### C-08 Search treats `%` and `_` as wildcards — **Low** — Verified (Probe P10)
- **Evidence:** `character_repository.py:165` and `prompt_repository.py:75` interpolate user text into a `LIKE` pattern without `ESCAPE`. Searching `_` returns all records. This is **not** SQL injection; the parameters are bound.
- **Fix:** Escape the wildcards, or move to SQLite FTS5 when cross-entity search arrives (M3).

### C-09 Inconsistent error handling — **Medium** — Verified by reading
- **Evidence:** `CharacterRepository` and `WorkspaceRepository` log and re-raise `sqlite3.Error`. `ProjectRepository` and `PromptRepository` do neither. `PromptWindow._save` catches only validation errors (`prompt_window.py:111`), so a database error escapes the Tk callback. `SettingsService.load` raises an unhandled `JSONDecodeError` on a corrupt `config.json` (Probe P7).
- **Fix:** A small application error hierarchy (`ValidationError`, `NotFoundError`, `StorageError`) raised by services. The UI maps them to user messages. Settings fall back to defaults and keep a `.corrupt` backup.

### C-10 Prompt category input contradicts validation — **Low** — Verified (Probe P12)
- **Evidence:** `prompt_window.py:43` uses a free-text `CTkComboBox`, while `PromptService.CATEGORIES` (`prompt_service.py:31`) is a fixed set. Typing "Podcast" fails with "Category is invalid."
- **Fix:** In M1, categories become user-configurable template kinds or tags.

### C-11 Synchronous I/O on the UI thread; no job infrastructure — **Medium (future High)** — Verified by reading
- **Evidence:** Every controller call runs on the Tk main loop. A new SQLite connection is opened per query (`connection.py`). There is no worker, queue or cancellation concept.
- **Impact:** Harmless today. Blocking once media import, thumbnail generation, AI calls or exports exist.
- **Fix:** M2 introduces a job service (thread pool, progress, cancellation, persisted job log) beneath the controllers, independent of the UI toolkit.

### C-12 Hard-coded styling — **Medium** — Verified
- **Evidence:** 57 literal hex colours and 26 `"Segoe UI"` font references across `src/ui`. `ctk.set_appearance_mode("dark")` is forced (`app_window.py:36`). Segoe UI is unavailable on macOS and Linux.
- **Fix:** Design tokens in M2. Not worth fixing in CustomTkinter.

## 4. Duplicate functionality

| Duplicate | Locations | Resolution |
|---|---|---|
| Project vs Workspace (name, lesson, status, platform/format) | `models/project.py`, `models/workspace.py` | Merge (A-01, D-01) |
| Two statistics calculators | C-03 | Keep one |
| Character prompt builder vs Prompt Engine | `character_service.py:127`, `prompt_service.py:170` | Keep the Prompt Engine |
| Duplicate-name helpers | `character_controller.py:64`, `prompt_service.py:193` | One shared utility |
| `_current_timestamp()` | 5 copies | One clock utility |

## 5. Performance

No measurable problems at the current data scale. The test suite runs in under 1 s. The following are **assumptions** about scale and were not benchmarked:
- `_validate_duplicate_name` loads every character for each save (`character_service.py:175`). Fine below about 10⁴ rows.
- `get_next_video_number` reads every project row (`project_repository.py:86`). Replace with `MAX()` on a numeric column.
- The dashboard rebuilds every widget on each `project_updated` event (`app_window.py:251`).
- Connection-per-query without WAL is acceptable for a single user. Enable WAL and `busy_timeout` once background jobs write concurrently.
