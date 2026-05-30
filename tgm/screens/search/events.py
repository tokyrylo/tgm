from textual.message import Message


class SearchEvent(Message):
    NAMESPACE = "global_search"


class ChannelChosen(SearchEvent):
    def __init__(self, channel_id: str) -> None:
        super().__init__()
        self.channel_id = channel_id
