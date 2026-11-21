# M0.5 — Test Report

Every result below was executed. Anything not executed is listed in §6.

## 1. Environments

| Environment | Python | Tk | CustomTkinter | SQLite | Used for |
|---|---|---|---|---|---|
| Cloud container, Linux (no Tk) | 3.13.18 | none | 5.2.2 | 3.53.1 | Full suite; UI tests skip |
| Same container, standalone CPython build + Xvfb | 3.13.14 | 9.0 | 5.2.2 | bundled | Full suite including UI tests; coverage; end-to-end `app.py` launch |
| GitHub Actions `ubuntu-latest` + Xvfb | 3.13 | see CI log | 5.2.2 | runner | CI |
| GitHub Actions `windows-latest` | 3.13.17 | 8.6 | 5.2.2 | runner | CI |
| GitHub Actions `macos-latest` | 3.13 | see CI log | 5.2.2 | runner | CI |

All local runs installed `requirements.txt`, `requirements-dev.txt` and `constraints.txt`. pytest 9.2.0.

## 2. Local results (commit `0250f71`)

| Command | Result |
|---|---|
| `python -m compileall -q app.py src tests` | passed |
| `python -m pytest -q` (no Tk) | **151 passed, 10 skipped** (the 10 UI tests skip with "tkinter is not installed") |
| `WONDERCUBS_REQUIRE_UI_TESTS=1 xvfb-run -a python -m pytest -q` (Tk 9.0) | **161 passed** |
| `WONDERCUBS_REQUIRE_UI_TESTS=1 xvfb-run -a python tests/ui/run_isolated.py` | **10 passed, 0 failed** (one process each) |
| `WONDERCUBS_REQUIRE_UI_TESTS=1 python -m pytest tests/ui` without Tk | 10 errors: the required flag turns a skip into a failure, as designed |
| The 10 original test modules alone | **62 passed**; `git diff 7aa2f8b -- <those files>` is empty, so the original tests are unchanged |
| `pip-audit -r requirements.txt -r requirements-dev.txt` | No known vulnerabilities found |
| `git diff --check 7aa2f8b HEAD` | clean |

### Coverage (Tk 9.0 run, all 161 tests)

| | Audit baseline (`7aa2f8b`) | M0.5 |
|---|---|---|
| Total | 51 % | **87 %** |
| `src/ui/app_window.py` | 0 % | 82 % |
| `src/ui/prompt/prompt_window.py` | 0 % | 82 % |
| `src/ui/workspace/workspace_window.py` | 0 % | 78 % |
| `src/ui/character/character_window.py` | 0 % | 51 % |
| `src/database/migrations.py` | — | 100 % |
| `src/database/backup.py` | — | 97 % |
| `src/services/project_service.py` | 80 % | 93 % |
| `src/services/settings_service.py` | 55 % | 95 % |
| `src/services/explorer_service.py` | 60 % | 94 % |
| `app.py` | 0 % | 65 % (the main window launch path is exercised by the end-to-end run, not by pytest) |

## 3. Test inventory

| Module | Tests | New in M0.5 | Covers |
|---|---|---|---|
| 10 original modules | 62 | — | unchanged |
| `tests/test_migrations.py` | 18 | yes | version tracking; 5 historical upgrades; idempotence; rollback; backup failure; too-new refusal; restore; unicode paths; corrupt backup |
| `tests/test_project_workspace_link.py` | 10 | yes | D-01, D-02, link integrity, migration backfill |
| `tests/test_project_creation_atomicity.py` | 7 | yes | D-03 failure and recovery paths |
| `tests/test_user_data.py` | 28 | yes | A-03, legacy import, C-02, settings robustness, recovery CLI, startup failure |
| `tests/test_explorer_service.py` | 8 | yes | C-01 |
| `tests/test_exports_and_goals.py` | 18 | yes | P-01, P-02, safe file names, dead-code evidence |
| `tests/ui/test_ui_flows.py` | 10 | yes | every screen; New Project dialog; workspace sync; goals; exports; settings; dashboard refresh (U-01) |
| **Total** | **161** | **99** | |

## 4. Regression evidence: the new tests fail on the audited code

The new data-integrity tests were copied onto `7aa2f8b` and run there (one test that needs the new `transaction()` helper was removed for this run). All 16 failed. Five failed on the defect itself rather than on a missing API:

| Test | Failure on `7aa2f8b` | Defect |
|---|---|---|
| `test_workspace_failure_rolls_back_project_row_and_folder` | `(1, 0) == (0, 0)` | D-03 orphan project |
| `test_database_insert_failure_leaves_no_folder` | `['001_Leo'] == []` | D-03 orphan folder |
| `test_recovery_after_database_loss_skips_numbers_used_by_existing_folders` | `'001' == '002'` | D-03 number collision |
| `test_unrelated_user_folders_are_preserved_on_failure` | `['001_Leo', 'Client Work'] == ['Client Work']` | D-03 orphan folder |
| `test_unlinked_workspace_never_updates_a_project_with_the_same_title` | `{'001': 'Published'} == {'001': 'Draft'}` | D-01 cross-project write |

Audit probes P1 (D-01), P2 (D-02), P3 (C-02), P7 (corrupt config) and P11 (C-01) reproduced the remaining defects on `7aa2f8b` during the audit. U-01 was reproduced on `7aa2f8b` with a UI script ("Could not create project: invalid command name …canvas").

## 5. Continuous integration

Workflow `.github/workflows/tests.yml`. Jobs: `ubuntu-latest`, `windows-latest` and `macos-latest` on Python 3.13, each running pip check, a Tk version report, compileall, the non-UI suite, and the UI tests one process each (Xvfb on Linux) with `WONDERCUBS_REQUIRE_UI_TESTS=1`. Plus a `pip-audit` job.

### Final run: [run 44878383457](https://github.com/lesleysacks/WonderCubsStudio/actions/runs/44878383457), commit `0250f71`. All jobs succeeded

| Job | Non-UI suite | UI tests (one process each) | Result |
|---|---|---|---|
| `ubuntu-latest` / 3.13 (Xvfb) | passed | passed | ✅ success |
| `windows-latest` / 3.13.17, Tk 8.6 | **151 passed** | **10 passed, 0 failed** | ✅ success |
| `macos-latest` (arm64) / 3.13.17 | passed (count not retrieved from the log tail) | **10 passed, 0 failed** | ✅ success |
| Dependency vulnerability audit | — | — | ✅ success |

### Earlier runs on this branch (kept for the record)

| Run | Commit | Outcome | Cause and fix |
|---|---|---|---|
| [44878060458](https://github.com/lesleysacks/WonderCubsStudio/actions/runs/44878060458) | `0f948cf` | Linux, macOS and audit passed; **Windows failed** (1 failed, 1 error, 159 passed) | (a) A test applied Windows path rules to a Linux XDG path; fixed in `src/utils/user_dirs.py` (POSIX rules). (b) The 10th Tk interpreter failed (`tcl_findLibrary`) |
| [44878228782](https://github.com/lesleysacks/WonderCubsStudio/actions/runs/44878228782) | `59c89b1` | **Windows failed** (159 passed, 2 errors) | Tk interpreter creation still failed late in the run (`Can't find a usable init.tcl … No error`). Fixed by running each UI test in its own process (`tests/ui/run_isolated.py`) |

Neither failure was an application defect. Both were test or CI environment issues, found and fixed on this branch. Every CI result above was read from the GitHub Actions job logs.

## 6. Not executed or not verifiable here

- Interactive use on a real Windows, macOS or Linux desktop by a person: dialogs, the native file chooser, the real file manager opening.
- `python app.py` on Windows or macOS. It was only launched end-to-end on Linux/Xvfb. CI covers the same code through pytest.
- Upgrading a real user's database (none available; see `M0_5_DATA_PRESERVATION_REPORT.md` §2).
- Packaging and installers (out of scope until M8).
- CustomTkinter 6.0 beyond a shallow smoke test (excluded by the pin).
