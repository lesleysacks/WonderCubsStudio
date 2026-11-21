# 06 — Test and CI Audit

## 1. Executed results (2026-11-21, Linux, Python 3.13.18)

| Command | Result |
|---|---|
| `python -m pip install -r requirements.txt -r requirements-dev.txt` | Installed (customtkinter **6.0.0** resolved) |
| `python -m compileall app.py src tests` | **Passed** |
| `python -m pytest -q` | **62 passed in 0.86 s**, 0 failed, 0 skipped |
| `coverage run --source=src,app -m pytest` | **51 % total** (2,208 statements, 1,076 missed) |
| `python app.py` | **Not executed.** No Tk module and no display in the audit container. The UI has not been verified by this audit. |
| GitHub Actions run history | **Not inspected.** Results above are local only. |

62 tests come from 53 test functions (some are parametrised), across 10 modules.

## 2. Coverage by layer

| Layer | Coverage | Notable gaps |
|---|---|---|
| Models | 91–100 % | — |
| Repositories | 80–95 % | error/logging branches |
| Services | 55–94 % | `settings_service` 55 %, `explorer_service` 60 %, `character_service` 77 %, `dashboard_service` 78 % |
| Controllers | 78–92 % | `prompt_controller` 78 % |
| UI (10 files) | **0 %** | everything |
| `app.py` | **0 %** (never imported) | startup, fatal-error path |

## 3. Findings

### T-01 Zero UI and startup coverage — **High** — Verified
No test imports `src/ui` or `app.py`. Regressions such as the CustomTkinter 6 upgrade, broken widget wiring, or startup on a fresh machine cannot be detected. **Do not** invest in CustomTkinter UI tests, because that UI is being replaced. Do add a **headless startup smoke test** (`initialize_database` + `MainController` + one call per controller), and make UI tests a requirement of the M2 shell (`pytest-qt` if PySide6 is chosen).

### T-02 CI does not test what users run — **High** — Verified
- **Evidence:** `.github/workflows/tests.yml` runs only on `ubuntu-latest`, Python 3.13, with unpinned dependencies. The product is documented as Windows 11 only.
- **Fix:** Matrix `windows-latest`, `macos-latest`, `ubuntu-latest`; install from the lock file; add coverage reporting with a non-UI floor (start at 85 %, ratchet upward); add a packaging smoke job in M8.

### T-03 Known defects have no failing tests — **High** — Verified
None of D-01, D-02, D-03, C-01, C-02 or C-07 is covered. The 13 audit probes should become regression tests **before** the fixes (write each test so it fails, then fix).

### T-04 Migration tests cover one historical shape — **Medium** — Verified
`test_project_lifecycle.py:28` covers a v0.1-style `Projects` table. No fixture covers a full v0.2 or v0.3 database, and no test checks data preservation across all tables.

### T-05 Untested modules — **Medium** — Verified
`SettingsService` (corrupt or partial config), `ExplorerService`, `DashboardService` error paths, `ProjectService.get_dashboard_statistics` (dead).

### T-06 Good test hygiene — Verified (strength)
Every test uses `tmp_path` and real SQLite, with no shared state or network. The suite is deterministic and fast. Keep this style: repository and service tests against real SQLite files are worth more here than mocks.

## 4. Verification strategy for migrations (applies from M0.5)

| Test type | What it proves | Introduced |
|---|---|---|
| Unit | Domain rules (validation, lifecycle, versioning) | existing; extend |
| Integration | Service + repository + SQLite, unit-of-work atomicity | M0.5 |
| Migration | Each historical fixture DB → latest; idempotent; resumes after a simulated failure | M0.5 |
| Data preservation | Row counts and field-level round-trip per legacy column; backup created and restorable | M0.5 |
| Regression | One test per audit finding (probes P1–P13) | M0.5 |
| UI | Shell boots, navigation, critical journeys (pytest-qt or Playwright depending on toolkit) | M2 |
| Platform compatibility | Full suite on Windows/macOS/Linux runners | M0.5 (matrix), M8 (installers) |
| Packaging | Built artefact launches, creates DB in the user data dir, upgrades a fixture DB | M8 |
| Security | pip-audit, bandit, secret scanning | M0.5 |

**Reporting rule:** each milestone's Definition of Done includes a results table like §1, listing the commands run, the platforms, the counts, and anything **not** executed and why.
