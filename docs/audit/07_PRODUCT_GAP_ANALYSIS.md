# 07 — Product Gap Analysis

Compares the directive's six modules (A–F) with what exists. **Exists** means verified in code. Effort uses T-shirt sizes for one developer (S ≤ 1 week, M 2–3 weeks, L 4–6 weeks, XL > 6 weeks). Sizes are estimates, not measurements.

## 1. Module coverage

| Module | Capability | Exists today | Reuse | Gap | Size |
|---|---|---|---|---|---|
| **A. Command Centre** | Dashboard, statistics | ✅ lifecycle counts, recent activity | `DashboardService`, `EventBus` | Deadlines, per-series/brand views | M |
| | Projects list | ⚠ basic modal table (`ProjectListWindow`) | `ProjectService.list_projects` | Filter, sort, search, open-in-app (not just Explorer) | S |
| | Deadlines, notifications | ❌ | — | Due dates on projects/tasks; local notifications | M |
| | Quick actions | ✅ buttons | — | Command palette (M2) | S |
| **B. Production Studio** | Project creation | ✅ | `ProjectService` | Content type, brief, template choice | M |
| | Content briefs | ⚠ `lesson` + `topic` fields only | Workspace fields | Structured brief (goal, audience, key messages, references) | M |
| | Scripts | ⚠ placeholder `story.txt` file | Prompt Engine for drafting | In-app script editor with versions | L |
| | Storyboards, scenes | ⚠ `current_scene` free text | — | Scene/shot entities, thumbnails per scene | L |
| | Tasks and stages | ⚠ 6 fixed lifecycle states | `ProjectStatus` | Configurable stages and checklists per workflow template | M |
| | Reviews/revisions | ❌ (lifecycle has a *Review* state) | Prompt versioning pattern | Comment and approval records | M |
| | Deliverables | ⚠ fixed `Final/`, `Upload/` folders | Folder scaffold | Deliverable entities linked to export presets | M |
| | Production templates | ⚠ hard-coded `PIPELINE_FOLDERS` | `ProjectService._create_project_folders` | Data-driven workflow templates | M |
| **C. Asset & Identity Library** | Characters | ✅ (animal-specific fields) | `Character*` stack | Generalise to Identity (§08 3.3) | M |
| | Human talent, voice profiles | ❌ | Identity model | Identity kinds + consent/usage-rights fields | S (after Identity) |
| | Image/video/audio/doc library | ❌ (issues #6, #14 open) | — | Asset store: import/copy, content hash, metadata, thumbnails | L |
| | Brand kits, logos, fonts | ❌ | Asset store | Brand entity grouping assets, colours, fonts | M |
| | Tagging, search, filter | ⚠ per-entity `LIKE` search | — | Tags + FTS5 global search | M |
| **D. AI Creative Intelligence** | Prompt management | ✅ versioned templates, context rendering | `PromptService` (strongest module) | Configurable kinds, variable entry UI, file export | S |
| | Provider-independent AI layer | ❌ (issue #15) | Prompt Engine as input | Provider port, adapters, cost metering, keychain | L |
| | Research/script/SEO/thumbnail assistants | ❌ | — | Built on the AI layer; each is a template + adapter call | M each |
| | Image/voice/video generation | ❌ | — | Adapters per provider; results imported as assets | L |
| **E. Distribution & Publishing** | Platform profiles | ⚠ `target_platform` free text | Workspace field | Platform profile entity (aspect, duration, metadata limits) | S |
| | Content calendar, scheduling | ❌ | — | Planned publish dates + calendar view (local) | M |
| | Export presets | ⚠ resolution/aspect/fps fields | Workspace + settings | Preset entity; FFmpeg render recipes | M |
| | Publishing integrations | ❌ (issue #16) | — | Per-platform OAuth, API review, quota handling | **XL, ongoing** |
| | Campaigns | ❌ | — | Group projects + dates + platforms | M |
| **F. Performance Intelligence** | Analytics, engagement | ❌ (issue #17) | — | Manual entry or CSV import first; API sync later | M (manual) / XL (APIs) |
| | Production and AI costs | ❌ | — | Cost entries per project; AI usage metered by the adapter | S–M |
| | Profitability | ❌ | — | Revenue entries + cost roll-up | S |

## 2. Gaps in the current scope (fix before expanding)

| ID | Severity | Gap | Evidence |
|---|---|---|---|
| P-01 | Medium | Exports display text in a message box; no file is written, and large JSON is unusable there | `character_window.py:143`, `workspace_window.py:222`, `prompt_window.py:135` |
| P-02 | Medium | "Today's Goal" cannot be set | no writer for `Goals` in `src/` |
| P-03 | Medium | Prompt preview cannot accept custom variable values; character chosen by typing a UUID | `prompt_window.py:58, 104` |
| P-04 | Low | Analytics nav item leads to "Coming Soon" plus a modal | `app_window.py:263–270` |
| P-05 | Low | "Latest Project Created" panel actually shows the most recently *updated* project | `dashboard_repository.py:56–71` |

## 3. Challenges and simplifications

1. **Publishing integrations are the costliest, least differentiating module.** Each platform needs OAuth app registration and usually a review or audit before public posting is allowed. APIs and policies change frequently, and schedulers such as Buffer and Later already serve this. **Recommendation:** M6 delivers a *publishing workspace*: platform profiles, metadata validation per platform, a calendar, export presets, a checklist and a copy-to-clipboard handoff. Add at most one direct integration, chosen by user demand, after launch.
2. **Analytics via platform APIs has the same cost profile.** Start with manual entry and CSV import (most platforms export CSV). Value comes from joining performance with *your own* production and AI cost data, which no platform dashboard does. That join is the differentiator.
3. **"Multi-brand teams and agencies" imply collaboration**: shared libraries, permissions, conflict resolution. This contradicts "local-first, single SQLite file" unless sync is designed for it. Defer until after v1. A **brand/workspace switch inside one local library** covers solo multi-brand creators cheaply.
4. **AI generation integrations (image/voice/video)**: build the provider port once and ship **one adapter per media type**. Each adapter is maintenance forever, so do not chase the catalogue.
5. **Reuse what already solves requirements:** versioned templates (Prompt Engine) generalise directly to brief templates, script outlines and SEO templates. The lifecycle states plus EventBus already form the core of production tracking. Character Intelligence is the seed of the Identity library.

## 4. Proposed product structure (target)

```
Command Centre        → Home (today, deadlines, activity), Projects, Calendar
Production Studio     → Project: Brief · Script · Scenes · Tasks · Reviews · Deliverables
Library               → Assets · Identities (characters, talent, voices) · Brands · Templates
Creative Intelligence → Assistants (per template) · Providers · Usage & cost
Distribution          → Platform profiles · Export presets · Publishing queue (manual first)
Insights              → Performance (manual/CSV) · Costs · Profitability
```

The six directive modules collapse into **four navigation areas for v1** (Command Centre, Production Studio, Library, Settings/Providers), with Distribution and Insights entering as project tabs before they earn top-level navigation.
