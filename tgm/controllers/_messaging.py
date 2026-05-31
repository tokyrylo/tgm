from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from tgm.screens.chat.events import (
    MessageDeleted,
    MessageEdited,
    MessagePinned,
    MessageSent,
    MessageUpdated,
    MessagesLoaded,
    MessagesLoading,
)
from tgm.widgets.input.events import (
    DeleteMessage,
    EditMessage,
    SendMessage,
    TogglePinMessage,
)

if TYPE_CHECKING:
    from tgm.core.models.messages import Message
    from tgm.core.protocol import ClientProtocol

_MEDIA_GROUP = "msg-media"


class _MessagingMixin:
    client: ClientProtocol | None
    current_channel_id: str | None

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
        self.send_message(self.current_channel_id, event.text, event.reply_to_msg_id)

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

    async def _client_event_reader(self) -> None:
        from dataclasses import replace
        from tgm.config.dirs import MEDIA_DIR
        from tgm.core.client_events import NewMessageEvent, StatusChangeEvent

        try:
            while self.client:
                event = await self.client.event_queue.get()
                if isinstance(event, NewMessageEvent):
                    msg = event.msg
                    if "photo" in (msg.media_types or []) and not msg.media_paths:
                        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
                        try:
                            paths = await self.client.download_media(msg, MEDIA_DIR)
                            if paths:
                                msg = replace(msg, media_paths=paths)
                        except Exception:
                            pass
                    if msg.channel_id == self.current_channel_id:
                        self._post_to_chat(MessageSent(msg.channel_id, msg))
                    self._refresh_channel_list()  # type: ignore[attr-defined]
                elif isinstance(event, StatusChangeEvent):
                    self._refresh_status_ui()  # type: ignore[attr-defined]
        except asyncio.CancelledError:
            pass

    async def _fetch_messages(self, channel_id: str) -> None:
        self._post_to_chat(MessagesLoading(channel_id))
        try:
            messages = await self.client.get_channel_messages(channel_id)  # type: ignore[union-attr]
            await self.client.mark_as_read(channel_id)  # type: ignore[union-attr]
        except Exception:
            messages = []
        self._post_to_chat(MessagesLoaded(channel_id, messages))
        for msg in messages:
            if "photo" in (msg.media_types or []) and not msg.media_paths:
                self.run_worker(  # type: ignore[attr-defined]
                    self._download_msg_media(msg),
                    exclusive=False,
                    group=_MEDIA_GROUP,
                )

    async def _do_send(self, channel_id: str, text: str, reply_to_id: str | None) -> None:
        if not self.client:
            return
        try:
            msg = await self.client.add_message(text, channel_id, reply_to_msg_id=reply_to_id)
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

    async def _download_msg_media(self, msg: Message) -> None:
        if not self.client:
            return
        from dataclasses import replace
        from tgm.config.dirs import MEDIA_DIR
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            paths = await self.client.download_media(msg, MEDIA_DIR)
        except Exception:
            return
        if not paths:
            return
        updated = replace(msg, media_paths=paths)
        self._post_to_chat(MessageUpdated(msg.channel_id, updated))

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
