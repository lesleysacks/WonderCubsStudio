"""One-time, non-destructive import of pre-M0.5 data from the install folder.

Before M0.5 the database, settings and logs lived next to the application
code. This service copies them into the per-user data folder the first time
the new version starts. The legacy files are only read, never modified,
moved or deleted, so the old copy remains a complete fallback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from src.database.backup import BackupError, copy_database
from src.utils.app_paths import AppPaths
from src.utils.logger import get_logger

MARKER_NAME = "legacy-import.json"


@dataclass(frozen=True)
class LegacyImportResult:
    status: str
    database_copied: bool = False
    config_copied: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)
    marker: Path | None = None


def import_legacy_data(legacy_root: Path, paths: AppPaths) -> LegacyImportResult:
    """Copy legacy data from ``legacy_root`` into ``paths`` if appropriate.

    Statuses: ``same_location``, ``already_imported``, ``target_has_data``,
    ``no_legacy_data``, ``imported``.
    """
    logger = get_logger(__name__)
    legacy = AppPaths(base_path=legacy_root)
    if paths.root.resolve() == legacy.root.resolve():
        return LegacyImportResult("same_location")
    marker = paths.root / MARKER_NAME
    if marker.exists():
        return LegacyImportResult("already_imported", marker=marker)
    if paths.database_file.exists():
        return LegacyImportResult("target_has_data")
    if not legacy.database_file.is_file():
        return LegacyImportResult("no_legacy_data")

    notes: list[str] = []
    paths.ensure_directories()
    try:
        copy_database(legacy.database_file, paths.database_file)
    except BackupError as error:
        logger.error("Legacy database could not be copied: %s", error)
        raise

    config_copied = False
    if legacy.config_file.is_file() and not paths.config_file.exists():
        config_copied = _import_config(legacy, paths, notes)

    marker.write_text(
        json.dumps(
            {
                "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "source_folder": str(legacy_root),
                "database": {"from": str(legacy.database_file), "to": str(paths.database_file)},
                "config_copied": config_copied,
                "notes": notes,
                "legacy_files_modified": False,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    logger.info("Legacy data imported from %s into %s", legacy_root, paths.root)
    return LegacyImportResult(
        "imported",
        database_copied=True,
        config_copied=config_copied,
        notes=tuple(notes),
        marker=marker,
    )


def _import_config(legacy: AppPaths, paths: AppPaths, notes: list[str]) -> bool:
    try:
        data = json.loads(legacy.config_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
    except (ValueError, UnicodeDecodeError) as error:
        kept = paths.root / "config.legacy-unreadable.json"
        shutil.copyfile(legacy.config_file, kept)
        notes.append(f"Legacy settings were unreadable ({error}); a copy was kept at {kept}.")
        return False

    raw_folder = str(data.get("default_project_folder") or "").strip()
    folder = Path(raw_folder).expanduser() if raw_folder else legacy.projects_dir
    if not folder.is_absolute():
        folder = legacy.root / folder
    if folder.resolve() == legacy.projects_dir.resolve():
        # The old default put projects inside the install folder. Existing
        # projects stay where they are (their paths are stored in the
        # database); new projects use the per-user default instead.
        data["default_project_folder"] = str(paths.projects_dir)
        notes.append(
            f"Existing project folders remain in {legacy.projects_dir}. "
            f"New projects will be created in {paths.projects_dir}; "
            "change this in Settings."
        )
    else:
        data["default_project_folder"] = str(folder)
    paths.config_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True
