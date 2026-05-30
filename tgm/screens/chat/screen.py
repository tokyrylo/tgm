from __future__ import annotations

from typing import Protocol, cast

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Input, ListView, LoadingIndicator, Static

from tgm.config.keybindings import get_binding_objects
from tgm.core.models.messages import Message
from tgm.core.protocol import ClientProtocol
from tgm.screens._base import TgmScreen
from tgm.widgets.channels.events import ChannelSelected, CreateChannel
from tgm.widgets.channels.list import ChannelList
from tgm.widgets.emoji import EmojiAutocomplete, EmojiPicker
from tgm.widgets.input.bar import InputBar
from tgm.widgets.input.events import ClearReply, SendMessage
from tgm.widgets.messages.list import MessageList
from tgm.widgets.search_bar import SearchBar


class AppContext(Protocol):
    current_channel_id: str | None
    reply_to_msg: Message | None
    client: ClientProtocol


class ChatScreen(TgmScreen):
    BINDINGS = get_binding_objects("chat")

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    def action_focus_channel_list(self) -> None:
        self.query_one(ChannelList).query_one("ListView", ListView).focus()

    def action_focus_input(self) -> None:
        self.query_one(InputBar).query_one("Input", Input).focus()

    def action_focus_messages(self) -> None:
        self.query_one(MessageList).focus()

    def action_focus_smart(self) -> None:
        focused = self.focused
        try:
            channel_lv = self.query_one(ChannelList).query_one("ListView", ListView)
            inp = self.query_one(InputBar).query_one("Input", Input)
            if focused is channel_lv:
                inp.focus()
            elif focused is inp:
                self.query_one(MessageList).focus()
            else:
                inp.focus()
        except Exception:
            pass

    def action_open_url(self, url: str) -> None:
        import webbrowser

        webbrowser.open(url)

    def action_open_emoji_picker(self) -> None:
        def on_dismiss(emoji: str | None) -> None:
            if emoji:
                self.query_one(InputBar).insert_emoji(emoji)

        self.app.push_screen(EmojiPicker(), on_dismiss)

    def action_toggle_search(self) -> None:
        bar = self.query_one(SearchBar)
        if bar.display:
            bar.close()
            self.query_one(MessageList).search("")
        else:
            bar.open()

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ChannelList(id="channel-list")
            with Vertical(id="chat-area"):
                yield Static(id="chat-top-bar")
                yield LoadingIndicator(id="msg-spinner")
                yield SearchBar(id="search-bar")
                yield MessageList(id="message-list")
                yield EmojiAutocomplete(id="emoji-ac")
                yield InputBar(id="input-bar")
        yield Footer()

    async def on_mount(self) -> None:
        self._refresh_top_bar()
        self.update_messages()

    async def on_screen_resume(self) -> None:
        self.update_messages()

    def on_channel_list_channel_selected(self, event: ChannelSelected) -> None:
        event.stop()
        self.ctx.current_channel_id = event.channel_id  # type: ignore[misc]
        self.update_messages()

    def on_channel_list_create_channel(self, event: CreateChannel) -> None:
        event.stop()

    def on_input_bar_send_message(self, event: SendMessage) -> None:
        event.stop()
        self.run_worker(self._send_work(event.text), exclusive=False)

    def on_input_bar_clear_reply(self, event: ClearReply) -> None:
        event.stop()
        self.ctx.reply_to_msg = None  # type: ignore[misc]

    def on_input_bar_attach_file(self, _) -> None:
        pass

    def on_search_bar_query_changed(self, event: SearchBar.QueryChanged) -> None:
        event.stop()
        current, total = self.query_one(MessageList).search(event.query)
        if event.query:
            self.query_one(SearchBar).update_count(current, total)

    def on_search_bar_navigate(self, event: SearchBar.Navigate) -> None:
        event.stop()
        ml = self.query_one(MessageList)
        current, total = ml.next_match() if event.forward else ml.prev_match()
        self.query_one(SearchBar).update_count(current, total)

    def update_messages(self) -> None:
        self.run_worker(self._load_messages_work(), exclusive=True)

    async def _load_messages_work(self) -> None:
        channel_id = self.ctx.current_channel_id
        client = self.ctx.client
        if not channel_id or channel_id not in client.channels:
            return
        self._show_spinner(True)
        try:
            messages = await client.get_channel_messages(channel_id)
        except Exception:
            messages = []
        self._show_spinner(False)
        self.query_one(MessageList).load_messages(messages)
        self._refresh_top_bar()
        self.query_one(ChannelList).refresh_previews()

    async def _send_work(self, text: str) -> None:
        channel_id = self.ctx.current_channel_id
        client = self.ctx.client
        if not channel_id:
            return
        reply_id = self.ctx.reply_to_msg.id if self.ctx.reply_to_msg else None
        try:
            msg = await client.add_message(text, channel_id, reply_to_msg_id=reply_id)
            self.query_one(MessageList).append_message(msg)
            self.ctx.reply_to_msg = None  # type: ignore[misc]
        except Exception:
            pass

    def _refresh_top_bar(self) -> None:
        channel_id = self.ctx.current_channel_id
        if not channel_id:
            return
        channel = self.ctx.client.channels.get(channel_id)
        if channel:
            self.query_one("#chat-top-bar", Static).update(
                f"[bold white]{channel.name}[/]\n[dim white]{channel.topic}[/]"
            )

    def _show_spinner(self, show: bool) -> None:
        self.query_one("#msg-spinner", LoadingIndicator).display = show
