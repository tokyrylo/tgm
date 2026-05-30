from __future__ import annotations

import asyncio
from typing import Protocol, cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, ListView, ListItem, Static

from tgm.core.models.channel import Channel
from tgm.core.protocol import ClientProtocol
from tgm.screens._base import TgmModalScreen
from tgm.screens.search.events import ChannelChosen


class AppContext(Protocol):
    client: ClientProtocol
    current_channel_id: str | None


class _ResultItem(ListItem):
    def __init__(self, channel: Channel) -> None:
        super().__init__()
        self.channel = channel
        self._label: Static

    def compose(self) -> ComposeResult:
        self._label = Static(self._fmt(self.channel))
        yield self._label

    def update_channel(self, channel: Channel) -> None:
        self.channel = channel
        self._label.update(self._fmt(channel))

    @staticmethod
    def _fmt(ch: Channel) -> str:
        return f"[bold white]{ch.name}[/]  [dim white]{ch.topic or ''}[/]"


class GlobalSearchScreen(TgmModalScreen[None]):
    def __init__(self) -> None:
        super().__init__()
        self._lv: ListView | None = None

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    def compose(self) -> ComposeResult:
        with Vertical(id="gs-container"):
            yield Input(placeholder="Search chats...", id="gs-input")
            yield ListView(id="gs-results")
            yield Static("[dim]Enter to open · Esc to close[/]", id="gs-hint")

    def on_mount(self) -> None:
        self._lv = self.query_one("#gs-results", ListView)
        self.query_one("#gs-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        self.run_worker(self._search(event.value), exclusive=True, group="gs-search")

    async def _search(self, query: str) -> None:
        try:
            await asyncio.sleep(0.15)
        except asyncio.CancelledError:
            return

        lv = self._lv
        if lv is None:
            return

        query = query.strip()
        if not query:
            await lv.clear()
            return

        try:
            results = await self.ctx.client.search_global(query)
        except asyncio.CancelledError:
            return

        if not results:
            await lv.clear()
            await lv.mount(Static("[dim]No results[/]"))
            return

        children = list(lv.children)
        if len(children) == len(results) and all(isinstance(c, _ResultItem) for c in children):
            for item, ch in zip(children, results):
                cast(_ResultItem, item).update_channel(ch)
        else:
            await lv.clear()
            await lv.mount_all([_ResultItem(ch) for ch in results])

        if lv.index is None or lv.index >= len(results):
            lv.index = 0

    def _choose(self, item: _ResultItem) -> None:
        self.app.post_message(ChannelChosen(item.channel.id))
        self.dismiss()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, _ResultItem):
            self._choose(event.item)

    def on_key(self, event) -> None:
        lv = self._lv
        if event.key == "escape":
            self.dismiss()
            event.prevent_default()
        elif event.key == "enter":
            item = lv.highlighted_child if lv is not None else None
            if isinstance(item, _ResultItem):
                self._choose(item)
                event.prevent_default()
        elif event.key in ("down", "up") and lv is not None:
            lv.focus()
