from __future__ import annotations

from dataclasses import dataclass, field

from tgm.core.models.channel import Channel
from tgm.core.models.user import User


@dataclass
class Store:
    users: dict[str, User] = field(default_factory=dict)
    channels: dict[str, Channel] = field(default_factory=dict)
    channel_list: list[Channel] = field(default_factory=list)
    current_user: User | None = None
    current_user_id: str | None = None
