"""Keybinding definitions — defaults, overrides, and Textual Binding objects."""

from textual.binding import Binding

from tgm.config.settings_store import (
    load_keybinding_overrides,
)
from tgm.config.settings_store import (
    save_keybinding as _store_save_keybinding,
)

# Tuple format: (key, action, desc[, show=True])
# show=False → binding is active but hidden from footer and keybindings UI.
DEFAULT_BINDINGS: dict[str, list[tuple]] = {
    "app": [
        ("ctrl+s", "open_settings", "Settings"),
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+t", "toggle_dark", "Theme"),
        ("ctrl+p", "open_global_search", "Find"),
    ],
    "chat": [
        ("ctrl+o", "open_emoji_picker", "Emoji"),
        ("ctrl+g", "app.create_group", "New"),
        ("ctrl+i", "app.open_chat_settings", "Chat info"),
        ("ctrl+k", "focus_channel_list", "Channels"),
        ("ctrl+j", "focus_input", "Message"),
        ("ctrl+f", "app.attach_file", "Attach"),
        ("ctrl+slash", "toggle_search", "Search"),
        ("escape", "focus_smart", "Back"),
        ("ctrl+space", "focus_input", "Type", False),
        ("r", "reply_message", "Reply", False),
    ],
    "login": [
        ("escape", "quit", "Quit"),
    ],
    "settings": [
        ("escape", "go_back", "Back"),
    ],
}

_cache: dict | None = None


def _resolve(entry: tuple, section_overrides: dict) -> tuple:
    default_key, action, desc = entry[0], entry[1], entry[2]
    show = entry[3] if len(entry) > 3 else True
    key = section_overrides.get(action.split(".")[-1], default_key)
    return (key, action, desc, show)


def _load() -> dict[str, list[tuple]]:
    global _cache
    if _cache is not None:
        return _cache

    overrides = load_keybinding_overrides()
    _cache = {
        section: [_resolve(e, overrides.get(section, {})) for e in defaults]
        for section, defaults in DEFAULT_BINDINGS.items()
    }
    return _cache


def reload():
    global _cache
    _cache = None


def get_binding_objects(section: str) -> list[Binding]:
    return [
        Binding(key, action, desc, show=show)
        for key, action, desc, show in _load().get(section, [])
    ]


def load_bindings() -> dict[str, list[tuple]]:
    """Return all bindings (merged defaults + stored overrides)."""
    return _load()


def save_binding(section: str, short_name: str, key: str):
    """Persist a keybinding override and invalidate the cache."""
    global _cache
    _cache = None
    _store_save_keybinding(section, short_name, key)
