from textual.app import ComposeResult
from textual.widgets import ListItem, Static

SELECTION_LABELS = {
    "app": "App",
    "chat": "Chat",
    "login": "Login",
    "settings": "Settings",
}

SETTINGS_SECTIONS = [
    ("account", "Account"),
    ("general", "General"),
    ("appearance", "Appearance"),
    ("input", "Input"),
    ("chats", "Chats"),
    ("notifications", "Notifications"),
    ("keybindings", "Keybindings"),
    ("about", "About"),
]


class SettingsSection(ListItem):
    def __init__(self, section_id: str, label: str, **kwargs):
        super().__init__(id=f"section-{section_id}", **kwargs)
        self.section_id = section_id
        self.label = label

    def compose(self) -> ComposeResult:
        yield Static(f" {self.label}", classes="settings-section-name")
