from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tgm.core.models.messages import Message


@dataclass
class NewMessageEvent:
    msg: Message


@dataclass
class StatusChangeEvent:
    user_id: str
    online: bool
    last_seen: datetime | None


ClientEvent = NewMessageEvent | StatusChangeEvent
