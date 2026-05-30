from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Static

from tgm.widgets.emoji.data import EMOJI_CATEGORIES, EmojiCategory


class EmojiPicker(ModalScreen[str | None]):
    EMOJI_PER_ROW = 8

    def __init__(self):
        super().__init__()
        self._category_index = 0
        self._emoji_index = 0

    @property
    def _category(self) -> EmojiCategory:
        return EMOJI_CATEGORIES[self._category_index]

    @property
    def _emojis(self) -> list[tuple[str, str, str]]:
        return self._category["emojis"]

    def compose(self) -> ComposeResult:
        with Vertical(id="emoji-picker-container"):
            with Horizontal(id="emoji-categories"):
                for i, cat in enumerate(EMOJI_CATEGORIES):
                    cls = "emoji-cat-btn selected" if i == 0 else "emoji-cat-btn"
                    yield Static(str(cat["icon"]), classes=cls, id=f"ecat-{i}")
            yield Grid(id="emoji-grid")
            yield Static("", id="emoji-hint")

    async def on_mount(self) -> None:
        self._grid = self.query_one("#emoji-grid", Grid)
        self._hint = self.query_one("#emoji-hint", Static)
        self._cat_tabs = list(self.query(".emoji-cat-btn"))
        await self._load_category()

    async def _load_category(self) -> None:
        await self._grid.remove_children()
        await self._grid.mount_all(
            Static(emoji, classes="emoji-cell") for emoji, _, _ in self._emojis
        )
        self._update_cursor()
        self._update_hint()
        self._update_category_tabs()

    def _update_cursor(self) -> None:
        cells = list(self._grid.children)
        for cell in cells:
            cell.remove_class("selected")
        if not cells:
            return
        cells[self._emoji_index].add_class("selected")
        cells[self._emoji_index].scroll_visible()

    def _update_hint(self) -> None:
        _, name, keywords = self._emojis[self._emoji_index]
        self._hint.update(
            f"[bold white]{self._category['name']}[/]  "
            f"[dim white]:{name}:[/]  "
            f"[dim]{keywords}[/]"
        )

    def _update_category_tabs(self) -> None:
        for i, tab in enumerate(self._cat_tabs):
            if i == self._category_index:
                tab.add_class("selected")
            else:
                tab.remove_class("selected")

    def _move(self, dx: int = 0, dy: int = 0) -> None:
        count = len(self._emojis)
        if dx:
            self._emoji_index = max(0, min(self._emoji_index + dx, count - 1))
        elif dy:
            cols = self.EMOJI_PER_ROW
            row, col = divmod(self._emoji_index, cols)
            row = max(0, min(row + dy, (count - 1) // cols))
            self._emoji_index = min(row * cols + col, count - 1)
        self._update_cursor()
        self._update_hint()

    def _select_current(self) -> None:
        self.dismiss(self._emojis[self._emoji_index][0])

    async def _switch_category(self, delta: int) -> None:
        self._category_index = (self._category_index + delta) % len(EMOJI_CATEGORIES)
        self._emoji_index = 0
        await self._load_category()

    async def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            self._select_current()
        elif event.key == "left":
            self._move(dx=-1)
        elif event.key == "right":
            self._move(dx=1)
        elif event.key == "up":
            self._move(dy=-1)
        elif event.key == "down":
            self._move(dy=1)
        elif event.key == "tab":
            await self._switch_category(1)
        elif event.key == "shift+tab":
            await self._switch_category(-1)
        elif event.key.isdigit() and 1 <= int(event.key) <= min(9, len(EMOJI_CATEGORIES)):
            self._category_index = int(event.key) - 1
            self._emoji_index = 0
            await self._load_category()

    async def on_static_clicked(self, event: Static.Clicked) -> None:  # type: ignore[name-defined]
        widget = event.widget
        if widget.has_class("emoji-cat-btn"):
            idx = int(widget.id.removeprefix("ecat-"))
            if idx != self._category_index:
                self._category_index = idx
                self._emoji_index = 0
                await self._load_category()
        elif widget.has_class("emoji-cell"):
            cells = list(self._grid.children)
            try:
                self.dismiss(self._emojis[cells.index(widget)][0])
            except ValueError:
                pass
