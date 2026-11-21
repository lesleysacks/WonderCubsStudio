# Contributing

## Setup

Use Python 3.13 on Windows, create a virtual environment, and install runtime and development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt -c constraints.txt
```

## Branches and changes

Start from an up-to-date `main` and use a focused branch such as `feat/short-description`, `fix/short-description`, or `docs/short-description`. Keep UI, controller, service, repository, and persistence responsibilities separated. Do not commit databases, generated projects, logs, caches, exports, secrets, or virtual environments.

## Tests

Before opening a pull request, run:

```powershell
python -m compileall app.py src tests
python -m pytest -q
python tests/ui/run_isolated.py
git diff --check
```

Add meaningful regression coverage for behavior changes.

Schema changes are new numbered migrations in `src/database/schema.py` (`MIGRATIONS`): additive only, never edited after release, covered by `tests/test_migrations.py` against the historical fixtures in `tests/fixtures/db/`. Dependency versions are pinned; change them deliberately and run the full suite, including UI tests. Do not skip or weaken tests to make a change pass. Manually exercise affected CustomTkinter workflows when automated UI coverage is unavailable.

## Commits and pull requests

Write imperative, focused commit subjects (for example, `Fix prompt test collection`). A pull request should explain the problem and solution, list verification performed, identify documentation changes, link relevant issues, and include screenshots for visible UI changes. Keep unrelated changes out of the pull request and wait for CI to pass before merge.
