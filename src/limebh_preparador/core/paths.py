from __future__ import annotations

import os
import sys
from pathlib import Path

_DOWNLOADS_FOLDER_ID = "{374DE290-123F-4565-9164-39C4925E467B}"


def system_downloads_dir() -> Path:
    """Obtém Downloads do Windows e usa o diretório convencional como fallback."""

    if sys.platform == "win32":
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                raw_value, _ = winreg.QueryValueEx(key, _DOWNLOADS_FOLDER_ID)
            return Path(os.path.expandvars(raw_value)).expanduser()
        except (OSError, TypeError):
            pass
    return Path.home() / "Downloads"


def default_output_root() -> Path:
    return system_downloads_dir() / "Preparador LIMEBH"
