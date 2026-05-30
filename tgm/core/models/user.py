from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    id: str
    name: str
    color: str = "text"
    username: str = ""
    phone: str = ""
    bio: str = ""
    online: bool = False
    last_seen: datetime | None = None


def format_last_seen(user: User) -> str:
    if user.online:
        return "online"
    ls = user.last_seen
    if ls is None:
        return "last seen a long time ago"
    now = datetime.now()
    diff = now - ls
    secs = diff.total_seconds()
    if secs < 60:
        return "last seen just now"
    if secs < 3600:
        mins = int(secs / 60)
        return f"last seen {mins} minute{'s' if mins != 1 else ''} ago"
    if diff.days == 0:
        return f"last seen today at {ls.strftime('%H:%M')}"
    if diff.days == 1:
        return f"last seen yesterday at {ls.strftime('%H:%M')}"
    return f"last seen {ls.strftime('%d %b')}"
