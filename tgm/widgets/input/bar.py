from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Protocol, cast

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.widgets import Button, Input

from .events import AttachFile, ClearReply, Reply, SendMessage, SetReply
from .reply_bar import ReplyBar

if TYPE_CHECKING:
    from textual.timer import Timer

INPUT_ID = "message-input"
REPLY_BAR_ID = "reply-bar"
EMOJI_AC_ID = "emoji-ac"


class _EmojiAC(Protocol):
    is_showing: bool

    def get_selected_emoji(self) -> str | None: ...
    def show_results(self, text: str) -> None: ...
    def hide(self) -> None: ...
    def select_next(self) -> None: ...
    def select_prev(self) -> None: ...


class AppContext(Protocol):
    reply_to_msg: Reply | None
    emoji_trigger: str
    enter_to_send: bool

    def query_one(self, selector: str) -> Any: ...


class InputBar(Horizontal):

    def compose(self) -> ComposeResult:
        yield ReplyBar(id=REPLY_BAR_ID, classes="reply-bar")
        yield Input(
            placeholder=f"Message... (type {self.ctx.emoji_trigger} for emoji)",
            id=INPUT_ID,
        )
        yield Button("📎 Attach", id="attach-btn")
        yield Button("Send", variant="primary", id="send-btn")

    def on_mount(self) -> None:
        self._input: Input = self.query_one(f"#{INPUT_ID}", Input)
        self._reply_bar: ReplyBar = self.query_one(f"#{REPLY_BAR_ID}", ReplyBar)
        self._ac: _EmojiAC | None = self._safe_get_ac()
        self._ac_debounce: Timer | None = None
        self._ac_seq: int = 0
        self.refresh_reply_bar()

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    def refresh_reply_bar(self) -> None:
        """Initial sync only — subsequent updates come via SetReply / ClearReply."""
        self._update_reply(self.ctx.reply_to_msg)

    def on_input_bar_set_reply(self, event: SetReply) -> None:
        self._update_reply(event.reply)
        event.stop()

    def on_input_bar_clear_reply(self, _: ClearReply) -> None:
        self._update_reply(None)

    def _update_reply(self, reply: Reply | None) -> None:
        self._reply_bar.show(self._format_reply(reply) if reply else None)

    def _format_reply(self, reply: Reply) -> str:
        sender = reply.username or "?"
        preview = reply.text[:60] if reply.text else "[Photo]"
        preview = preview.replace("[", "[[").replace("]", "]]")
        return (
            f"[dim #6DB2FF]▎ Reply to [bold]{sender}[/][/] "
            f"[dim white]{preview}[/]  [dim](Esc to cancel)[/]"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self._send(self._input.value)
            event.stop()
        elif event.button.id == "attach-btn":
            self.post_message(AttachFile())
            event.stop()

    def _send(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self.post_message(SendMessage(text))
        self._input.clear()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        ac = self._get_ac()
        if ac and ac.is_showing:
            emoji = ac.get_selected_emoji()
            if emoji:
                self._insert_emoji(emoji)
            event.stop()
            return
        if self.ctx.enter_to_send:
            self._send(event.value)
            event.stop()

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._ac_debounce is not None:
            self._ac_debounce.stop()
        self._ac_seq += 1
        seq = self._ac_seq
        value = event.value
        self._ac_debounce = self.set_timer(0.08, lambda: self._trigger_ac(value, seq))
        ac = self._get_ac()
        if ac and ac.is_showing:
            event.stop()

    def _trigger_ac(self, value: str, seq: int) -> None:
        if seq != self._ac_seq:
            return
        ac = self._get_ac()
        if ac:
            ac.show_results(value)

    def _safe_get_ac(self) -> _EmojiAC | None:
        try:
            return cast(_EmojiAC, self.app.query_one(f"#{EMOJI_AC_ID}"))
        except NoMatches:
            return None

    def _get_ac(self) -> _EmojiAC | None:
        ac = self._ac or self._safe_get_ac()
        if ac:
            self._ac = ac
        return ac

    def _insert_emoji(self, emoji: str) -> None:
        value = self._input.value
        cursor = self._input.cursor_position
        prefix = value[:cursor]
        match = re.search(rf"{re.escape(self.ctx.emoji_trigger)}[^\s]*$", prefix)
        if match:
            idx = match.start()
            new_value = value[:idx] + emoji + value[cursor:]
            self._input.value = new_value
            self._input.cursor_position = idx + len(emoji)
        ac = self._get_ac()
        if ac:
            ac.hide()
        self._input.focus()

    def on_key(self, event) -> None:
        if event.key == "escape":
            if self._handle_ac_escape(event):
                return
            if self._handle_reply_escape(event):
                return
            return
        ac = self._get_ac()
        if ac and ac.is_showing:
            if event.key == "tab":
                ac.select_next()
                event.stop()
            elif event.key == "shift+tab":
                ac.select_prev()
                event.stop()

    def _handle_ac_escape(self, event) -> bool:
        ac = self._get_ac()
        if ac and ac.is_showing:
            ac.hide()
            event.stop()
            return True
        return False

    def _handle_reply_escape(self, event) -> bool:
        if self.ctx.reply_to_msg:
            self.post_message(ClearReply())
            event.stop()
            return True
        return False
