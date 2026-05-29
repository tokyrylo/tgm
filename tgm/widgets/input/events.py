from typing import Protocol

from textual.message import Message


class Reply(Protocol):
    username: str | None
    text: str | None


class InputBarEvent(Message):
    NAMESPACE = "input_bar"


class SendMessage(InputBarEvent):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class SetReply(InputBarEvent):
    def __init__(self, reply: Reply) -> None:
        super().__init__()
        self.reply = reply


class ClearReply(InputBarEvent):
    pass


class AttachFile(InputBarEvent):
    pass
