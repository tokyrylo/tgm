from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    id: str
    user_id: str
    username: str
    text: str
    timestamp: datetime
    channel_id: str
    out: bool = False
    read: bool = False
    media_paths: list[str] | None = None
    media_types: list[str] | None = None
    grouped_id: str | None = None
    reply_to_msg_id: str | None = None
