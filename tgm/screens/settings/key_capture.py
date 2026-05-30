from textual import events
from textual.app import ComposeResult
from textual.widgets import Static

from tgm.screens._base import TgmScreen


class KeyCaptureScreen(TgmScreen):

    BINDINGS = []

    def __init__(self, section: str, action_name: str, callback):
        super().__init__()
        self._section = section
        self._action_name = action_name
        self.callback = callback

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold white]Press new key for: {self._action_name}[/bold white]\n\n",
            id="capture-prompt",
        )
        yield Static(
            "[dim]Press [b]ESC[/b] to cancel.[/dim]",
            id="capture-hint",
        )

    def on_key(self, event: events.Key):
        if event.key == "escape":
            self.app.pop_screen()
        else:
            self.callback(self._section, self._action_name, event.key)
            self.app.pop_screen()
