"""User data location, legacy import and settings (M0.5.3: A-03, C-02)."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

import app as app_module
from src.controllers.main_controller import MainController
from src.database.migrations import MigrationError
from src.database.schema import initialize_database
from src.services.legacy_data_service import import_legacy_data
from src.services.settings_service import SettingsService
from src.utils.app_paths import AppPaths
from src.utils.user_dirs import default_projects_dir, user_data_dir
from tests.db_fixtures import assert_original_values_preserved, load_fixture, snapshot

UNICODE_FOLDER = "Mes Données 日本語 & Co"


# --- platform locations ------------------------------------------------------

@pytest.mark.parametrize(
    ("platform", "env", "expected"),
    [
        ("win32", {"APPDATA": r"C:\Users\Zoë\AppData\Roaming"}, Path(r"C:\Users\Zoë\AppData\Roaming") / "WonderCubs Studio"),
        ("win32", {}, Path("/home/u") / "AppData" / "Roaming" / "WonderCubs Studio"),
        ("darwin", {}, Path("/home/u") / "Library" / "Application Support" / "WonderCubs Studio"),
        ("linux", {}, Path("/home/u") / ".local" / "share" / "wondercubs-studio"),
        ("linux", {"XDG_DATA_HOME": "/data/xdg"}, Path("/data/xdg") / "wondercubs-studio"),
        ("linux", {"XDG_DATA_HOME": "relative/ignored"}, Path("/home/u") / ".local" / "share" / "wondercubs-studio"),
        ("darwin", {"WONDERCUBS_DATA_DIR": "/portable/data"}, Path("/portable/data")),
    ],
)
def test_user_data_dir_follows_platform_conventions(platform, env, expected) -> None:
    assert user_data_dir(platform, env, Path("/home/u")) == expected


def test_default_projects_dir_is_under_documents(tmp_path: Path) -> None:
    (tmp_path / "Documents").mkdir()
    assert default_projects_dir("darwin", {}, tmp_path) == tmp_path / "Documents" / "WonderCubs Studio" / "Projects"
    assert default_projects_dir("linux", {}, tmp_path) == tmp_path / "Documents" / "WonderCubs Studio" / "Projects"
    assert default_projects_dir("win32", {"USERPROFILE": r"C:\Users\Zoë"}, tmp_path) == (
        Path(r"C:\Users\Zoë") / "Documents" / "WonderCubs Studio" / "Projects"
    )


def test_linux_without_documents_falls_back_to_home(tmp_path: Path) -> None:
    assert default_projects_dir("linux", {}, tmp_path) == tmp_path / "WonderCubs Studio" / "Projects"


# --- install folder is never written -----------------------------------------

def _tree(folder: Path) -> dict[str, str]:
    return {
        str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "dir"
        for path in sorted(folder.rglob("*"))
    }


def _user_paths(tmp_path: Path, install: Path) -> AppPaths:
    return AppPaths(
        base_path=install,
        data_root=tmp_path / "user data" / UNICODE_FOLDER,
        default_projects_root=tmp_path / "Documents" / UNICODE_FOLDER / "Projects",
    )


def test_full_startup_and_project_creation_never_touch_the_install_folder(tmp_path: Path) -> None:
    install = tmp_path / "Program Files" / "WonderCubs Studio"
    (install / "src").mkdir(parents=True)
    (install / "config.json").write_text('{"default_project_folder": "projects"}', encoding="utf-8")
    before = _tree(install)
    paths = _user_paths(tmp_path, install)

    paths.ensure_directories()
    import_legacy_data(install, paths)
    settings = SettingsService(paths.config_file, paths.projects_dir)
    settings.ensure_config()
    initialize_database(paths.database_file)
    controller = MainController(paths, settings)
    project = controller.create_project("Café Été", "Seasons")

    assert _tree(install) == before
    assert Path(project.folder_path).parent == paths.projects_dir
    assert paths.database_file.is_file() and paths.config_file.is_file()


def test_for_current_user_uses_the_data_dir_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WONDERCUBS_DATA_DIR", str(tmp_path / "portable"))
    paths = AppPaths.for_current_user(tmp_path / "install")
    assert paths.database_file == tmp_path / "portable" / "data" / "database.db"
    assert paths.config_file == tmp_path / "portable" / "config.json"


# --- legacy import -----------------------------------------------------------

def _legacy_install(tmp_path: Path, config: str | None = '{"default_project_folder": "projects", "author_name": "Zoë"}') -> Path:
    install = tmp_path / "old install"
    load_fixture("v0_3_release", install / "data" / "database.db")
    if config is not None:
        (install / "config.json").write_text(config, encoding="utf-8")
    return install


def test_legacy_data_is_copied_without_modifying_the_original(tmp_path: Path) -> None:
    install = _legacy_install(tmp_path)
    legacy_before = _tree(install)
    original = snapshot(install / "data" / "database.db")
    paths = _user_paths(tmp_path, install)

    result = import_legacy_data(install, paths)

    assert result.status == "imported" and result.database_copied and result.config_copied
    assert _tree(install) == legacy_before
    assert snapshot(paths.database_file) == original
    config = json.loads(paths.config_file.read_text(encoding="utf-8"))
    assert config["author_name"] == "Zoë"
    assert config["default_project_folder"] == str(paths.projects_dir)
    assert any("remain in" in note for note in result.notes)
    marker = json.loads(result.marker.read_text(encoding="utf-8"))
    assert marker["legacy_files_modified"] is False


def test_imported_legacy_database_then_upgrades_with_data_intact(tmp_path: Path) -> None:
    install = _legacy_install(tmp_path)
    original = snapshot(install / "data" / "database.db")
    paths = _user_paths(tmp_path, install)

    import_legacy_data(install, paths)
    initialize_database(paths.database_file)

    assert_original_values_preserved(original, snapshot(paths.database_file))
    assert snapshot(install / "data" / "database.db") == original  # legacy copy still pristine


def test_legacy_import_runs_once(tmp_path: Path) -> None:
    install = _legacy_install(tmp_path)
    paths = _user_paths(tmp_path, install)
    import_legacy_data(install, paths)
    initialize_database(paths.database_file)
    upgraded = snapshot(paths.database_file)

    assert import_legacy_data(install, paths).status == "already_imported"
    assert snapshot(paths.database_file) == upgraded


def test_existing_user_data_is_never_overwritten_by_legacy_data(tmp_path: Path) -> None:
    install = _legacy_install(tmp_path)
    paths = _user_paths(tmp_path, install)
    load_fixture("v0_1", paths.database_file)
    current = snapshot(paths.database_file)

    assert import_legacy_data(install, paths).status == "target_has_data"
    assert snapshot(paths.database_file) == current


def test_custom_legacy_project_folder_is_kept(tmp_path: Path) -> None:
    custom = tmp_path / "My Videos"
    install = _legacy_install(tmp_path, json.dumps({"default_project_folder": str(custom)}))
    paths = _user_paths(tmp_path, install)

    import_legacy_data(install, paths)

    assert SettingsService(paths.config_file, paths.projects_dir).get_projects_dir() == custom


def test_relative_custom_legacy_project_folder_resolves_against_old_install(tmp_path: Path) -> None:
    install = _legacy_install(tmp_path, '{"default_project_folder": "client work"}')
    paths = _user_paths(tmp_path, install)

    import_legacy_data(install, paths)

    assert SettingsService(paths.config_file, paths.projects_dir).get_projects_dir() == install / "client work"


def test_unreadable_legacy_settings_are_kept_and_database_still_imported(tmp_path: Path) -> None:
    install = _legacy_install(tmp_path, "{not json")
    paths = _user_paths(tmp_path, install)

    result = import_legacy_data(install, paths)

    assert result.database_copied and not result.config_copied
    assert (paths.root / "config.legacy-unreadable.json").read_text(encoding="utf-8") == "{not json"


def test_no_legacy_data_means_no_import(tmp_path: Path) -> None:
    paths = _user_paths(tmp_path, tmp_path / "fresh install")
    assert import_legacy_data(tmp_path / "fresh install", paths).status == "no_legacy_data"
    assert not paths.database_file.exists()


# --- settings control project creation (C-02) ------------------------------

def test_c02_saved_project_folder_controls_where_projects_are_created(tmp_path: Path) -> None:
    paths = AppPaths(tmp_path)
    paths.ensure_directories()
    initialize_database(paths.database_file)
    controller = MainController(paths, SettingsService(paths.config_file, paths.projects_dir))
    custom = tmp_path / "Shared Drive" / UNICODE_FOLDER

    controller.save_settings(replace(controller.load_settings(), default_project_folder=str(custom)))

    assert controller.get_project_folder_preview("Leo") == str(custom / "001_Leo")
    project = controller.create_project("Leo", "Colors")
    assert Path(project.folder_path) == custom / "001_Leo"
    assert (custom / "001_Leo" / "README.md").is_file()


def test_project_numbering_continues_across_folder_changes(tmp_path: Path) -> None:
    paths = AppPaths(tmp_path)
    paths.ensure_directories()
    initialize_database(paths.database_file)
    controller = MainController(paths, SettingsService(paths.config_file, paths.projects_dir))
    controller.create_project("First", "L")
    controller.save_settings(replace(controller.load_settings(), default_project_folder=str(tmp_path / "elsewhere")))

    assert controller.create_project("Second", "L").video_number == "002"


def test_corrupt_settings_are_kept_and_defaults_used(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{broken", encoding="utf-8")
    service = SettingsService(config, tmp_path / "projects")

    settings = service.load()

    assert settings.default_project_folder == str(tmp_path / "projects")
    kept = list(tmp_path.glob("config.json.corrupt-*"))
    assert len(kept) == 1 and kept[0].read_text(encoding="utf-8") == "{broken"


@pytest.mark.parametrize(
    ("stored", "field_name", "expected"),
    [
        ({"default_project_folder": "   "}, "default_project_folder", "DEFAULT"),
        ({"default_fps": "fast"}, "default_fps", 30),
        ({"default_project_folder": "rel"}, "default_project_folder", "REL"),
    ],
)
def test_invalid_individual_settings_fall_back(tmp_path: Path, stored, field_name, expected) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps(stored), encoding="utf-8")
    value = getattr(SettingsService(config, tmp_path / "projects").load(), field_name)
    expected = {"DEFAULT": str(tmp_path / "projects"), "REL": str(tmp_path / "rel")}.get(expected, expected)
    assert value == expected


def test_settings_save_is_atomic_and_keeps_unicode(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "config.json", tmp_path / "projects")
    service.save(replace(service.load(), author_name="Zoë 日本"))

    assert service.load().author_name == "Zoë 日本"
    assert not list(tmp_path.glob("*.tmp"))


# --- recovery commands and startup failure ----------------------------------

def test_cli_lists_and_restores_backups(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("WONDERCUBS_DATA_DIR", str(tmp_path / UNICODE_FOLDER))
    paths = AppPaths.for_current_user(tmp_path)
    load_fixture("v0_2", paths.database_file)
    original = snapshot(paths.database_file)
    result = initialize_database(paths.database_file)

    assert app_module.main(["--list-backups"]) == 0
    assert str(result.backup_path) in capsys.readouterr().out
    assert app_module.main(["--restore-backup", str(result.backup_path)]) == 0
    assert snapshot(paths.database_file) == original


def test_failed_upgrade_stops_startup_and_explains_recovery(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WONDERCUBS_DATA_DIR", str(tmp_path / "data root"))
    monkeypatch.setattr(app_module, "INSTALL_DIR", tmp_path / "install")
    shown: list[str] = []
    monkeypatch.setattr(app_module, "_show_startup_error", lambda title, message: shown.append(message))

    def fail(*_args, **_kwargs):
        raise MigrationError("step 2 failed", backup_path=tmp_path / "b.db", current_version=1)

    monkeypatch.setattr("src.database.schema.initialize_database", fail)

    assert app_module.main([]) == 2
    assert "--restore-backup" in shown[0] and str(tmp_path / "b.db") in shown[0]
