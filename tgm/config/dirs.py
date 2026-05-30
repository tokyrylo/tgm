"""All runtime directory / file paths for the app.

Override the base directory with the TGM_CONFIG_DIR env variable:
  TGM_CONFIG_DIR=~/.config/my_tgm poetry run tgm
"""

import os
from pathlib import Path

APP_DIR = Path(
    os.environ.get("TGM_CONFIG_DIR", "") or (Path.home() / ".config" / "tgm")
)

SETTINGS_FILE = APP_DIR / "settings.json"
AVATAR_DIR = APP_DIR / "avatars"
SESSION_DIR = APP_DIR / "sessions"
