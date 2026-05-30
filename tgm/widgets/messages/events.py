from textual.message import Message as TxtMessage


class MessageListEvent(TxtMessage):
    NAMESPACE = "message_list"


class LoadOlderMessages(MessageListEvent):
    def __init__(self, oldest_id: int) -> None:
        super().__init__()
        self.oldest_id = oldest_id
