from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import App as _AppBase
    from textual.message import Message as TextualMessage
    from tgm.core.models.messages import Message
    from tgm.core.protocol import ClientProtocol
else:
    _AppBase = object


class _MediaMixin(_AppBase):
    client: ClientProtocol | None

    if TYPE_CHECKING:
        def _post_to_chat(self, message: TextualMessage) -> None: ...  # provided by _MessagingMixin

    def _start_media_download(self, msg: Message) -> None:
        self.run_worker(
            self._download_msg_media(msg),
            exclusive=False,
            group="msg-media",
        )

    async def _download_msg_media(self, msg: Message) -> None:
        if not self.client:
            return
        from dataclasses import replace
        from tgm.config.dirs import MEDIA_DIR
        from tgm.screens.chat.events import MessageUpdated

        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            paths = await self.client.download_media(msg, MEDIA_DIR)
        except Exception:
            return
        if not paths:
            return
        updated = replace(msg, media_paths=paths)
        self._post_to_chat(MessageUpdated(msg.channel_id, updated))
