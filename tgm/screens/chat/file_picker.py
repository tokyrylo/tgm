from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ListItem, ListView, Static

from tgm.screens._base import TgmModalScreen

_DIR_ICON = "📁"
_FILE_ICON = "📄"

_IGNORED = {".git", "__pycache__", ".DS_Store"}


def _entries(path: Path) -> list[tuple[str, Path, bool]]:
    """Return (label, path, is_dir) sorted dirs-first then by name."""
    items: list[tuple[str, Path, bool]] = []
    try:
        for p in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if p.name in _IGNORED:
                continue
            is_dir = p.is_dir()
            icon = _DIR_ICON if is_dir else _FILE_ICON
            items.append((f"{icon} {p.name}", p, is_dir))
    except PermissionError:
        pass
    return items


class _Entry(ListItem):
    def __init__(self, label: str, path: Path, is_dir: bool) -> None:
        super().__init__()
        self._label = label
        self.path = path
        self.is_dir = is_dir

    def compose(self) -> ComposeResult:
        yield Static(self._label)


class FilePicker(TgmModalScreen[str | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("backspace", "go_up", "Up", show=False),
    ]

    def __init__(self, start: Path | None = None) -> None:
        super().__init__()
        self._cwd = (start or Path.home()).resolve()

    def compose(self) -> ComposeResult:
        with Vertical(id="fp-container"):
            yield Static("", id="fp-path")
            yield ListView(id="fp-list")
            with Horizontal(id="fp-footer"):
                yield Static("", id="fp-selected")
                yield Button("Cancel", id="fp-cancel", variant="default")

    def on_mount(self) -> None:
        self._navigate(self._cwd)

    def _navigate(self, path: Path) -> None:
        self._cwd = path
        self.query_one("#fp-path", Static).update(
            f"[bold white]📂 {path}[/]"
        )
        lv = self.query_one("#fp-list", ListView)
        lv.clear()
        if path.parent != path:
            lv.append(_Entry(f"{_DIR_ICON} ..", path.parent, is_dir=True))
        for label, p, is_dir in _entries(path):
            lv.append(_Entry(label, p, is_dir))
        self.query_one("#fp-selected", Static).update("")
        lv.focus()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, _Entry) and not event.item.is_dir:
            self.query_one("#fp-selected", Static).update(
                f"[dim white]{event.item.path.name}[/]"
            )
        else:
            self.query_one("#fp-selected", Static).update("")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not isinstance(event.item, _Entry):
            return
        if event.item.is_dir:
            self._navigate(event.item.path)
        else:
            self.dismiss(str(event.item.path))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fp-cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_go_up(self) -> None:
        if self._cwd.parent != self._cwd:
            self._navigate(self._cwd.parent)
