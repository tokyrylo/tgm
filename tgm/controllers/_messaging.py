from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tgm.screens.chat.events import (
    MessageDeleted,
    MessageEdited,
    MessagePinned,
    MessageSent,
    MessagesLoaded,
    MessagesLoading,
)
from tgm.widgets.input.events import (
    ClearReply,
    DeleteMessage,
    EditMessage,
    SendMessage,
    SetEdit,
    SetReply,
    TogglePinMessage,
)

if TYPE_CHECKING:
    from tgm.core.models.messages import Message
    from tgm.core.protocol import ClientProtocol


class _MessagingMixin:
    client: ClientProtocol | None
    current_channel_id: str | None
    reply_to_msg: Message | None

    def load_messages(self, channel_id: str | None) -> None:
        if not channel_id or not self.client or channel_id not in self.client.channels:
            return
        self.run_worker(self._fetch_messages(channel_id), exclusive=True, group="msg-load")  # type: ignore[attr-defined]

    def send_message(self, channel_id: str, text: str, reply_to_id: str | None) -> None:
        self.run_worker(  # type: ignore[attr-defined]
            self._do_send(channel_id, text, reply_to_id),
            exclusive=False,
            group="msg-send",
        )

    def send_file(self, file_path: str) -> None:
        if not self.current_channel_id:
            return
        self.run_worker(  # type: ignore[attr-defined]
            self._do_send_file(self.current_channel_id, file_path),
            exclusive=False,
            group="msg-send",
        )

    def on_send_message(self, event: SendMessage) -> None:
        event.stop()
        if not self.current_channel_id:
            return
        reply_id = self.reply_to_msg.id if self.reply_to_msg else None
        self.send_message(self.current_channel_id, event.text, reply_id)

    def on_set_reply(self, event: SetReply) -> None:
        self.reply_to_msg = event.reply  # type: ignore[assignment]
        self._sync_input_bar_reply()
        self._focus_input()

    def on_clear_reply(self, event: ClearReply) -> None:  # noqa: ARG002
        self.reply_to_msg = None
        self._sync_input_bar_reply()

    def on_set_edit(self, event: SetEdit) -> None:
        event.stop()
        self._get_input_bar_and(lambda bar: bar.activate_edit(event.msg_id, event.text))

    def on_delete_message(self, event: DeleteMessage) -> None:
        event.stop()
        if self.current_channel_id:
            self.run_worker(  # type: ignore[attr-defined]
                self._do_delete(self.current_channel_id, event.msg_id),
                exclusive=False,
                group="msg-delete",
            )

    def on_edit_message(self, event: EditMessage) -> None:
        event.stop()
        if self.current_channel_id:
            self.run_worker(  # type: ignore[attr-defined]
                self._do_edit(self.current_channel_id, event.msg_id, event.text),
                exclusive=False,
                group="msg-edit",
            )

    def on_toggle_pin_message(self, event: TogglePinMessage) -> None:
        event.stop()
        channel_id = self.current_channel_id
        if not channel_id or not self.client:
            return
        channel = self.client.channels.get(channel_id)
        if not channel:
            return
        if channel.pinned_message_id == event.msg_id:
            self.run_worker(self._do_unpin(channel_id), exclusive=False, group="msg-pin")  # type: ignore[attr-defined]
        else:
            self.run_worker(self._do_pin(channel_id, event.msg_id), exclusive=False, group="msg-pin")  # type: ignore[attr-defined]

    async def _fetch_messages(self, channel_id: str) -> None:
        self._post_to_chat(MessagesLoading(channel_id))
        try:
            messages = await self.client.get_channel_messages(channel_id)  # type: ignore[union-attr]
            await self.client.mark_as_read(channel_id)  # type: ignore[union-attr]
        except Exception:
            messages = []
        self._post_to_chat(MessagesLoaded(channel_id, messages))

    async def _do_send(
        self, channel_id: str, text: str, reply_to_id: str | None
    ) -> None:
        if not self.client:
            return
        try:
            msg = await self.client.add_message(
                text, channel_id, reply_to_msg_id=reply_to_id
            )
            self.reply_to_msg = None
            self._sync_input_bar_reply()
            self._post_to_chat(MessageSent(channel_id, msg))
        except Exception:
            pass

    async def _do_send_file(self, channel_id: str, file_path: str) -> None:
        if not self.client:
            return
        try:
            msg = await self.client.send_file(channel_id, file_path)
            self._post_to_chat(MessageSent(channel_id, msg))
        except Exception:
            pass

    async def _do_delete(self, channel_id: str, msg_id: str) -> None:
        if not self.client:
            return
        try:
            await self.client.delete_message(channel_id, msg_id)
            self._post_to_chat(MessageDeleted(channel_id, msg_id))
        except Exception:
            pass

    async def _do_edit(self, channel_id: str, msg_id: str, text: str) -> None:
        if not self.client:
            return
        try:
            await self.client.edit_message(channel_id, msg_id, text)
            self._post_to_chat(MessageEdited(channel_id, msg_id, text))
        except Exception:
            pass

    async def _do_pin(self, channel_id: str, msg_id: str) -> None:
        if not self.client:
            return
        try:
            await self.client.pin_message(channel_id, msg_id)
            self._post_to_chat(MessagePinned(channel_id, msg_id))
        except Exception:
            pass

    async def _do_unpin(self, channel_id: str) -> None:
        if not self.client:
            return
        try:
            await self.client.unpin_message(channel_id)
            self._post_to_chat(MessagePinned(channel_id, None))
        except Exception:
            pass

    def _post_to_chat(self, message: Any) -> None:
        from tgm.screens.chat.screen import ChatScreen

        for screen in self.screen_stack:  # type: ignore[attr-defined]
            if isinstance(screen, ChatScreen):
                screen.post_message(message)
                return

    def _sync_input_bar_reply(self) -> None:
        self._get_input_bar_and(lambda bar: bar.sync_reply(self.reply_to_msg))

    def _focus_input(self) -> None:
        from textual.widgets import Input

        self._get_input_bar_and(lambda bar: bar.query_one("Input", Input).focus())

    def _get_input_bar_and(self, fn: Any) -> None:
        from tgm.screens.chat.screen import ChatScreen
        from tgm.widgets.input.bar import InputBar

        for screen in self.screen_stack:  # type: ignore[attr-defined]
            if isinstance(screen, ChatScreen):
                try:
                    fn(screen.query_one(InputBar))
                except Exception:
                    pass
                return
