from __future__ import annotations

from typing import Protocol, Sequence, cast

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ListView, Static

from tgm.core.models.channel import Channel

from .events import AvatarUpdated, ChannelSelected, CreateChannel
from .preview import ChannelPreview


class AppContext(Protocol):
    current_channel_id: str | None
    channels: Sequence[Channel]


class ChannelList(Vertical):

    def compose(self) -> ComposeResult:
        with Horizontal(classes="sidebar-header"):
            yield Static("[bold white]Channels[/]", classes="sidebar-title")
            yield Button("＋", id="add-channel-btn", variant="primary")
        yield ListView(id="channel-items")

    def on_mount(self) -> None:
        self._lv: ListView = self.query_one("#channel-items", ListView)
        self._items_by_id: dict[str, ChannelPreview] = {}

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-channel-btn":
            self.post_message(CreateChannel())
            event.stop()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, ChannelPreview):
            self.post_message(ChannelSelected(event.item.channel.id))
            event.stop()

    def on_avatar_updated(self, event: AvatarUpdated) -> None:
        item = self._items_by_id.get(event.channel_id)
        if item:
            item.invalidate_avatar()
            item.refresh_content()

    def refresh_previews(self) -> None:
        self._sync_items()
        self._restore_selection()

    def _sync_items(self) -> None:
        channels = list(self.ctx.channels)
        new_ids = {ch.id for ch in channels}

        # remove stale
        for ch_id in list(self._items_by_id):
            if ch_id not in new_ids:
                self._items_by_id.pop(ch_id).remove()

        # add new items (order fixed below)
        for ch in channels:
            if ch.id not in self._items_by_id:
                item = ChannelPreview(ch)
                self._items_by_id[ch.id] = item
                self._lv.mount(item)

        # update data for all
        for ch in channels:
            self._items_by_id[ch.id].refresh_content(ch)

        # reorder to match desired sequence
        for i, ch in enumerate(channels):
            item = self._items_by_id[ch.id]
            children = list(self._lv.children)
            if i < len(children) and children[i] is not item:
                self._lv.move_child(item, before=children[i])
                children.remove(item)
                children.insert(i, item)

    def _restore_selection(self) -> None:
        current_id = self.ctx.current_channel_id
        if current_id is None or current_id not in self._items_by_id:
            return
        item = self._items_by_id[current_id]
        try:
            self._lv.index = list(self._lv.children).index(item)
        except ValueError:
            pass
