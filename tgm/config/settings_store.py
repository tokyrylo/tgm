"""Single source of truth for all persistent app settings.

Everything lives in APP_DIR/settings.json (see tgm.config.dirs):
  global      — UI preferences (timestamps, theme, …)
  channels    — per-channel overrides (muted, notify, …)
  telegram    — API credentials (api_id, api_hash)
  keybindings — per-section key overrides
"""

import json

from tgm.config.dirs import APP_DIR, SETTINGS_FILE
from tgm.core.models import ChannelSettings

SETTINGS_DIR = APP_DIR

DEFAULT_GLOBAL = {
    "show_timestamps": True,
    "compact_mode": False,
    "enter_to_send": True,
    "notifications": True,
    "message_density": "comfortable",
    "accent_theme": "Blue",
    "emoji_trigger": ":",
    "text_wrap": True,
    "text_opacity": 1.0,
    "big_msg_threshold": 1,
}


def _ensure_dir():
    APP_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except json.JSONDecodeError, OSError:
            return {}
    return {}


def _write_raw(data: dict):
    _ensure_dir()
    SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_global() -> dict:
    data = _load_raw()
    raw = data.get("global", {})
    result = dict(DEFAULT_GLOBAL)
    result.update(raw)
    return result


def save_global(**kwargs):
    data = _load_raw()
    data.setdefault("global", {}).update(kwargs)
    _write_raw(data)


def load_channel_settings() -> dict[str, ChannelSettings]:
    data = _load_raw()
    raw_channels = data.get("channels", {})
    result = {}
    for cid, raw in raw_channels.items():
        result[cid] = ChannelSettings(
            muted=raw.get("muted", False),
            color=raw.get("color", ""),
            notify=raw.get("notify", True),
            forward_to=raw.get("forward_to", ""),
        )
    return result


def save_channel_settings(channel_id: str, **kwargs):
    data = _load_raw()
    channels = data.setdefault("channels", {})
    channel = channels.setdefault(channel_id, {})
    channel.update(kwargs)
    _write_raw(data)


def load_telegram() -> dict[str, str]:
    """Returns {"api_id": "...", "api_hash": "..."} or empty strings."""
    data = _load_raw()
    tg = data.get("telegram", {})
    # Migration: import from old config.toml if not yet in settings.json
    if not tg.get("api_id"):
        tg = _migrate_telegram_from_toml()
        if tg:
            _save_telegram_raw(tg)
    return {
        "api_id": str(tg.get("api_id", "")),
        "api_hash": str(tg.get("api_hash", "")),
    }


def save_telegram(api_id: str, api_hash: str):
    _save_telegram_raw({"api_id": api_id, "api_hash": api_hash})


def _save_telegram_raw(tg: dict):
    data = _load_raw()
    data["telegram"] = tg
    _write_raw(data)


def _migrate_telegram_from_toml() -> dict:
    """One-time import from old ~/.config/clitel/config.toml."""
    try:
        import tomllib

        toml_path = SETTINGS_DIR / "config.toml"
        if not toml_path.exists():
            return {}
        raw = tomllib.loads(toml_path.read_text())
        tg = raw.get("telegram", {})
        if tg.get("api_id") and tg.get("api_hash"):
            return {"api_id": str(tg["api_id"]), "api_hash": str(tg["api_hash"])}
    except Exception:
        pass
    return {}


def load_keybinding_overrides() -> dict[str, dict[str, str]]:
    """Returns {section: {short_name: key}} overrides (only non-defaults)."""
    data = _load_raw()
    return data.get("keybindings", {})


def save_keybinding(section: str, short_name: str, key: str):
    data = _load_raw()
    kb = data.setdefault("keybindings", {})
    kb.setdefault(section, {})[short_name] = key
    _write_raw(data)


def load_telegram_config() -> dict | None:
    """Return {"api_id": int, "api_hash": str} or None if not configured."""
    tg = load_telegram()
    api_id = tg.get("api_id", "")
    api_hash = tg.get("api_hash", "")
    if api_id and api_hash:
        try:
            return {"api_id": int(api_id), "api_hash": str(api_hash)}
        except ValueError, TypeError:
            pass
    return None
