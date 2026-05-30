from textual.message import Message


class ChannelListEvent(Message):
    NAMESPACE = "channel_list"


class ChannelSelected(ChannelListEvent):
    def __init__(self, channel_id: str) -> None:
        super().__init__()
        self.channel_id = channel_id


class CreateChannel(ChannelListEvent):
    pass


class AvatarUpdated(ChannelListEvent):
    def __init__(self, channel_id: str) -> None:
        super().__init__()
        self.channel_id = channel_id
