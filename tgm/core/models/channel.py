from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tgm.core.models.user import User


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


@dataclass
class ChannelInfo:
    channel: Channel
    is_dm: bool
    user: User | None = None
    members: list[User] = field(default_factory=list)
    members_count: int = 0
