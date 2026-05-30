from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Static


class SearchBar(Widget):

    class QueryChanged(Message):
        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    class Navigate(Message):
        def __init__(self, forward: bool) -> None:
            super().__init__()
            self.forward = forward

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(placeholder="Search...", id="search-input")
            yield Button("▲", id="search-prev")
            yield Button("▼", id="search-next")
            yield Static("", id="search-count")
            yield Button("✕", id="search-close")

    def open(self) -> None:
        self.display = True
        self.query_one("#search-input", Input).focus()

    def close(self) -> None:
        self.display = False
        self.query_one("#search-input", Input).value = ""

    def update_count(self, current: int, total: int) -> None:
        text = f"{current}/{total}" if total else "no results"
        self.query_one("#search-count", Static).update(f"[dim white]{text}[/]")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.post_message(self.QueryChanged(event.value))
            event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-prev":
            self.post_message(self.Navigate(forward=False))
            event.stop()
        elif event.button.id == "search-next":
            self.post_message(self.Navigate(forward=True))
            event.stop()
        elif event.button.id == "search-close":
            self.close()
            self.post_message(self.QueryChanged(""))
            event.stop()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.close()
            self.post_message(self.QueryChanged(""))
            event.stop()
        elif event.key == "enter":
            self.post_message(self.Navigate(forward=True))
            event.stop()
