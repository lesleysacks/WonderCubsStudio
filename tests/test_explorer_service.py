"""Regression tests for audit finding C-01 (Windows-only folder opening)."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.services.explorer_service import ExplorerService

ODD_NAME = "Mes Données 日本語 & $HOME; rm -rf"


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    path = tmp_path / ODD_NAME
    path.mkdir()
    return path


@pytest.mark.parametrize(
    ("platform", "program"), [("darwin", "open"), ("linux", "xdg-open"), ("freebsd14", "xdg-open")]
)
def test_unix_platforms_pass_the_path_as_one_argument(folder: Path, platform: str, program: str) -> None:
    calls: list[list[str]] = []
    ExplorerService(platform=platform, launcher=lambda command: calls.append(list(command))).open_folder(str(folder))

    assert calls == [[program, str(folder.resolve())]]


def test_windows_uses_startfile(folder: Path) -> None:
    opened: list[str] = []
    ExplorerService(platform="win32", startfile=opened.append).open_folder(str(folder))

    assert opened == [str(folder.resolve())]


def test_missing_launcher_gives_a_clear_error(folder: Path) -> None:
    def missing(_command):
        raise FileNotFoundError("xdg-open")

    with pytest.raises(OSError, match="xdg-open"):
        ExplorerService(platform="linux", launcher=missing).open_folder(str(folder))


def test_missing_folder_is_reported(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ExplorerService(platform="linux", launcher=lambda c: None).open_folder(str(tmp_path / "nope"))


def test_file_instead_of_folder_is_reported(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        ExplorerService(platform="linux", launcher=lambda c: None).open_folder(str(file_path))


def test_default_service_no_longer_crashes_on_this_platform(folder: Path, monkeypatch) -> None:
    """On the audit's Linux machine this raised AttributeError (os.startfile)."""
    launched: list[list[str]] = []
    monkeypatch.setattr("src.services.explorer_service._spawn", lambda command: launched.append(list(command)))
    service = ExplorerService(startfile=lambda path: launched.append([path]))

    service.open_folder(str(folder))

    assert launched and launched[0][-1] == str(folder.resolve())
