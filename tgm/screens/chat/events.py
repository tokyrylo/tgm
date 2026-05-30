from __future__ import annotations

from typing import TYPE_CHECKING

from textual.message import Message

if TYPE_CHECKING:
    from tgm.core.models.messages import Message as TgMessage


class MessagesLoading(Message):
    def __init__(self, channel_id: str) -> None:
        super().__init__()
        self.channel_id = channel_id


class MessagesLoaded(Message):
    def __init__(self, channel_id: str, messages: list[TgMessage]) -> None:
        super().__init__()
        self.channel_id = channel_id
        self.messages = messages


class MessageSent(Message):
    def __init__(self, channel_id: str, message: TgMessage) -> None:
        super().__init__()
        self.channel_id = channel_id
        self.message = message
