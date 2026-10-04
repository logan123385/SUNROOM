"""SUNROOM per-user data directory.

Matches ``magda::paths::alwaysOSDefault()``: JUCE's ``userApplicationDataDirectory``
plus ``SUNROOM``. On macOS that special location is ``~/Library``, not
``~/Library/Application Support``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def data_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "SUNROOM"


def ai_config() -> Path:
    return data_dir() / "sunroom-ai.json"
