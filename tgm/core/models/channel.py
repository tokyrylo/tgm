from dataclasses import dataclass


@dataclass
class Channel:
    id: str
    name: str
    topic: str = ""
    last_message: str = ""
    unread: int = 0


@dataclass
class ChannelSettings:
    muted: bool = False
    color: str = ""
    notify: bool = True
    forward_to: str = ""
