from __future__ import annotations

from typing import Protocol, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalGroup
from textual.widgets import Footer, Input, ListView, LoadingIndicator, Static

from tgm.config.keybindings import get_binding_objects
from tgm.core.models.messages import Message
from tgm.core.protocol import ClientProtocol
from tgm.screens._base import TgmScreen
from tgm.screens.chat.events import MessageDeleted, MessageEdited, MessagePinned, MessageSent, MessagesLoaded, MessagesLoading
from tgm.widgets.channels.events import ChannelSelected, CreateChannel
from tgm.widgets.channels.list import ChannelList
from tgm.widgets.emoji import EmojiAutocomplete, EmojiPicker
from tgm.widgets.input.bar import InputBar
from tgm.widgets.input.events import ClearReply, SendMessage, SetReply
from tgm.widgets.messages.list import MessageList
from tgm.widgets.search_bar import SearchBar


class AppContext(Protocol):
    current_channel_id: str | None
    reply_to_msg: Message | None
    client: ClientProtocol

    def load_messages(self, channel_id: str | None) -> None: ...
    def send_message(self, channel_id: str, text: str, reply_to_id: str | None) -> None: ...
    def send_file(self, file_path: str) -> None: ...


class ChatScreen(TgmScreen):
    BINDINGS = [
        Binding("ctrl+p", "open_global_search", "Find", priority=True, show=False),
        *get_binding_objects("chat"),
    ]

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

    def action_open_global_search(self) -> None:
        from tgm.screens.search import GlobalSearchScreen

        self.app.push_screen(GlobalSearchScreen())

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
                with VerticalGroup(id="chat-header"):
                    yield Static(id="chat-top-bar")
                    yield Static(id="pinned-bar")
                yield LoadingIndicator(id="msg-spinner")
                yield SearchBar(id="search-bar")
                yield MessageList(id="message-list")
                yield EmojiAutocomplete(id="emoji-ac")
                yield InputBar(id="input-bar")
        yield Footer()

    async def on_mount(self) -> None:
        self._refresh_top_bar()
        self.ctx.load_messages(self.ctx.current_channel_id)
        client = self.ctx.client
        if client and client.on_new_message is None:
            client.on_new_message = self._on_incoming_message  # type: ignore[misc]

    def _on_incoming_message(self, msg) -> None:
        if msg.channel_id == self.ctx.current_channel_id:
            self.query_one(MessageList).append_message(msg)
        self.query_one(ChannelList).refresh_previews()

    async def on_screen_resume(self) -> None:
        self.ctx.load_messages(self.ctx.current_channel_id)

    def on_channel_selected(self, event: ChannelSelected) -> None:
        event.stop()
        self.ctx.current_channel_id = event.channel_id  # type: ignore[misc]
        self.ctx.load_messages(event.channel_id)

    def on_create_channel(self, event: CreateChannel) -> None:
        event.stop()

    def on_send_message(self, event: SendMessage) -> None:
        event.stop()
        channel_id = self.ctx.current_channel_id
        if not channel_id:
            return
        reply_id = self.ctx.reply_to_msg.id if self.ctx.reply_to_msg else None
        self.ctx.send_message(channel_id, event.text, reply_id)

    def on_set_reply(self, event: SetReply) -> None:
        event.stop()
        self.ctx.reply_to_msg = event.reply  # type: ignore[misc]
        self.query_one(InputBar).refresh_reply_bar()
        self.query_one(InputBar).query_one("Input", Input).focus()

    def on_clear_reply(self, event: ClearReply) -> None:
        event.stop()
        self.ctx.reply_to_msg = None  # type: ignore[misc]

    def on_attach_file(self, _) -> None:
        from tgm.screens.chat.file_picker import FilePicker

        def _on_pick(path: str | None) -> None:
            if path:
                self.ctx.send_file(path)  # type: ignore[attr-defined]

        self.app.push_screen(FilePicker(), _on_pick)

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

    def on_messages_loading(self, event: MessagesLoading) -> None:
        event.stop()
        self._show_spinner(True)

    def on_messages_loaded(self, event: MessagesLoaded) -> None:
        event.stop()
        self._show_spinner(False)
        ml = self.query_one(MessageList)
        ml.load_messages(event.messages)
        self._refresh_top_bar()
        self.query_one(ChannelList).refresh_previews()
        channel = self.ctx.client.channels.get(event.channel_id)
        self._update_pinned_bar(channel.pinned_message_id if channel else None, ml)

    def on_message_sent(self, event: MessageSent) -> None:
        event.stop()
        self.query_one(MessageList).append_message(event.message)
        self.ctx.reply_to_msg = None  # type: ignore[misc]

    def on_message_deleted(self, event: MessageDeleted) -> None:
        event.stop()
        self.query_one(MessageList).remove_message(event.message_id)

    def on_message_edited(self, event: MessageEdited) -> None:
        event.stop()
        self.query_one(MessageList).update_message(event.message_id, event.text)

    def on_message_pinned(self, event: MessagePinned) -> None:
        event.stop()
        self._update_pinned_bar(event.msg_id, self.query_one(MessageList))

    def _refresh_top_bar(self) -> None:
        from tgm.core.models.user import format_last_seen

        channel_id = self.ctx.current_channel_id
        if not channel_id:
            return
        channel = self.ctx.client.channels.get(channel_id)
        if not channel:
            return
        if channel.is_dm and channel.peer_user_id:
            user = self.ctx.client.users.get(channel.peer_user_id)
            if user:
                status = format_last_seen(user)
                color = "green" if user.online else "dim white"
                subtitle = f"[{color}]{status}[/]"
            else:
                subtitle = ""
        else:
            subtitle = f"[dim white]{channel.topic}[/]"
        self.query_one("#chat-top-bar", Static).update(
            f"[bold white]{channel.name}[/]\n{subtitle}"
        )

    def _update_pinned_bar(self, msg_id: str | None, ml: MessageList) -> None:
        bar = self.query_one("#pinned-bar", Static)
        if not msg_id:
            bar.display = False
            bar.update("")
            return
        msg = ml._msgs_by_id.get(msg_id)
        if not msg:
            bar.display = False
            return
        sender = msg.username or "?"
        preview = (msg.text or "[Photo]")[:60].replace("[", "[[").replace("]", "]]")
        bar.update(f"[bold yellow]📌[/] [dim white]{sender}:[/] {preview}")
        bar.display = True

    def _show_spinner(self, show: bool) -> None:
        self.query_one("#msg-spinner", LoadingIndicator).display = show
