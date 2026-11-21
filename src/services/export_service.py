"""Write exports to user-chosen files."""
from __future__ import annotations

import os
from pathlib import Path
import re
import unicodedata

_RESERVED = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def suggested_file_name(name: str, extension: str, fallback: str = "export") -> str:
    """A safe default file name that keeps non-ASCII letters (e.g. 'Café_Été.json')."""
    clean = unicodedata.normalize("NFC", name)
    clean = _RESERVED.sub(" ", clean)
    clean = re.sub(r"\s+", "_", clean.strip()).strip("._") or fallback
    if clean.upper() in _WINDOWS_RESERVED_NAMES:
        clean = f"{clean}_{fallback}"
    return f"{clean[:120]}.{extension.lstrip('.')}"


def write_text_file(path: str | Path, content: str) -> Path:
    """Write UTF-8 text atomically, so an existing file is never left half-written."""
    target = Path(path)
    temporary = target.with_name(target.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return target
