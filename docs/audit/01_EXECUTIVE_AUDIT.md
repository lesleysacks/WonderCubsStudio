# 01 — Executive Audit

Audit date: 2026-11-21 · Commit audited: `7aa2f8b` (main, "harden v0.3") · Milestone: **M0, Phase Zero**

This audit covers the whole repository: 46 Python source files, 10 test modules, the schema, configuration, CI, documentation, 29 issues and 4 pull requests. It changes no application code.

## How findings were established

| Method | Result |
|---|---|
| Read every file in `src/`, `tests/`, `app.py`, CI, docs | Done |
| `python -m compileall app.py src tests` (Python 3.13.18, Linux) | **Passed** |
| `python -m pytest -q` | **62 passed in 0.86 s** |
| Line coverage (`coverage run`, tool installed temporarily, not added to repo) | **51 % overall; ~86 % non-UI; 0 % UI** |
| 13 behaviour probes against the real services on temporary databases (scripts kept outside the repo) | 13 of 13 suspected defects **reproduced** |
| Launch the desktop UI (`python app.py`) | **Not executed.** The audit container has no Tk and no display, and it runs Linux, not the supported Windows 11. No UI claim below is based on running the UI. |
| GitHub issues and pull requests | 29 issues (11 open), 4 merged PRs reviewed |

**Verified** means reproduced by a test, a probe or a direct code reading cited by path. **Assumption** marks anything inferred and not executed.

## Headline verdict

The non-UI core is **sound and worth keeping**: a clear `UI → Controller → Service → Repository → SQLite` layering, immutable dataclass models, a prompt engine with real immutable versioning, validation at the service layer, an idempotent schema upgrade, and a fast, deterministic test suite.

The product is **not yet release-grade, even for its current scope**. Three verified data-integrity defects and one platform blocker stand in the way. The most important architectural fact is that **"Workspace" duplicates "Project"**. The two are linked only by a title string, and that link already corrupts data.

The UI layer (≈1,100 lines of CustomTkinter, 0 % tested) cannot reach the "commercial creative software" bar. It will be replaced whichever architecture is chosen, so it should not drive any decision to preserve code.

## Top findings (full detail in documents 02–06)

| ID | Severity | Finding | Verified |
|---|---|---|---|
| D-01 | **Critical** | Saving a workspace updates the **wrong project's** status when two projects share a title. Workspace↔Project link is a title string. | Probe P1 |
| D-02 | High | Renaming a workspace's project name silently breaks project sync. | Probe P2 |
| D-03 | High | Project creation is non-atomic across folder, project row and workspace row; partial failures leave orphans. | Probes P4, P5 |
| C-01 | High | "Open folder" crashes on macOS and Linux (`os.startfile`). | Probe P11 |
| C-02 | High | The **Default Project Folder** setting is saved but never used. | Probe P3 |
| D-04 | High | No schema versioning, migration history or pre-migration backup. Only `Projects` has an upgrade path. | Probe P8, `schema.py` |
| A-03 | High | User data is written inside the application directory. This fails once installed under Program Files or `/Applications`. | `app_paths.py`, `app.py:17` |
| T-02 | High | `customtkinter>=5.2.2` now resolves to **6.0.0**, a major version the UI has never been tested against. | `pip` resolution |
| P-01 | Medium | Every "export" (character, workspace, prompt) opens a message box. No file is written. | UI code |
| P-02 | Medium | "Today's Goal" panel has no write path anywhere in the application. | grep for `Goals` writes |

## What currently works (verified by tests or probes)

- Project creation with database-generated sequential numbers, a folder scaffold and a README (`ProjectService`).
- Six-state project lifecycle with `published_at` preserved on first publish, plus event-driven dashboard refresh.
- Character CRUD, case-insensitive duplicate-name protection, search, duplicate, JSON payload, and a character prompt builder (the builder has no caller in the app).
- Workspace CRUD, validation (aspect ratio, resolution, duration), switching and a context payload.
- Prompt templates with immutable versions, a single active version enforced by a partial unique index, placeholder validation, rendering with workspace/character context, duplication, and JSON/TXT/Markdown rendering.
- Idempotent upgrade of v0.1-era `Projects` tables (Probe P9 and `test_project_lifecycle.py:28`).

## Stale tracking (the code is ahead of the issue tracker)

Open issues #23 (auto-increment), #24 (clipboard shortcuts), #26 (title focus), #27 (folder preview) and #12 (Workspace Context Engine) are **implemented** (`app_window.py:38, 400, 415–417`; PR #20). #7 (Character Prompt Builder) is implemented in the service (`character_service.py:127`) but not exposed in the UI. All six should be closed or re-scoped.

## Recommendation in one paragraph

Approve **M0.5: stabilise before generalising**. Fix D-01–D-04, C-01, C-02 and T-02, introduce a migration framework with automatic backups, and move data to a per-user location. The remedy for D-01/D-02, folding Workspace into Project, is also the first step of generalisation, so the work is not wasted. Then proceed with the universal domain (M1) on the existing Python services.

For the new desktop shell, the preliminary recommendation is **Python + PySide6** (rationale and the conditions that would favour Tauri are in `03_ARCHITECTURE_AUDIT.md` §5). The formal decision document `docs/architecture/GLOBAL_DESKTOP_ARCHITECTURE.md` is deliberately **not** written yet. It belongs to Phase One, which needs your approval first.

## Challenges to the directive

1. **Six modules is a portfolio, not a product.** Publishing (E) and Performance Intelligence (F) depend on third-party platform APIs. Those need OAuth app review, quotas and constant maintenance, and they compete with mature tools. For a single-maintainer project (all 20 commits share one author), they should start as *manual and import-based* features, not integrations. See `07_PRODUCT_GAP_ANALYSIS.md`.
2. **"Operating system for the complete lifecycle" has no beachhead.** The existing strengths (reusable identities, versioned templates, numbered series, per-episode scaffolds) fit **series-based creators**: animation channels, educators, faceless and short-form channels, and podcasts. Lead with that segment. Agencies and multi-brand teams imply collaboration and sync, which is a much later, much costlier capability.
3. **Do not migrate frameworks and the domain at the same time.** Generalise the domain behind the current UI first (M1), keeping it shippable, then replace the shell (M2). Doing both together removes the ability to verify that data survived.
