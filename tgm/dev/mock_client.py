from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Callable

from tgm.core.models.channel import Channel
from tgm.core.models.messages import Message
from tgm.core.models.user import User

_ME = User(id="me", name="You", color="text")
_ALICE = User(id="u1", name="Alice", color="#2B5278")
_BOB = User(id="u2", name="Bob", color="#1E6B3A")
_CAROL = User(id="u3", name="Carol", color="#4A2D7A")

_USERS: dict[str, User] = {u.id: u for u in [_ME, _ALICE, _BOB, _CAROL]}

_CHANNELS: list[Channel] = [
    Channel(
        id="c1",
        name="General",
        topic="General chat",
        last_message="Have you seen the new Textual release?",
        unread=3,
    ),
    Channel(
        id="c2",
        name="Random",
        topic="Off-topic stuff",
        last_message="lol same",
        unread=0,
    ),
    Channel(
        id="c3", name="Dev", topic="Tech talk", last_message="PR merged 🎉", unread=1
    ),
    Channel(id="c4", name="Alice DM", topic="", last_message="sounds good!", unread=0),
]

_now = datetime.now()

_MESSAGES: dict[str, list[Message]] = {
    "c1": [
        Message(
            id="c1-1",
            user_id="u1",
            username="Alice",
            text="Hey everyone!",
            timestamp=_now - timedelta(hours=3),
            channel_id="c1",
            read=True,
        ),
        Message(
            id="c1-2",
            user_id="u2",
            username="Bob",
            text="What's up!",
            timestamp=_now - timedelta(hours=2, minutes=50),
            channel_id="c1",
            read=True,
        ),
        Message(
            id="c1-3",
            user_id="me",
            username="You",
            text="Good morning 👋",
            timestamp=_now - timedelta(hours=2),
            channel_id="c1",
            out=True,
            read=True,
        ),
        Message(
            id="c1-4",
            user_id="u1",
            username="Alice",
            text="Have you seen the new Textual release? Pretty cool stuff with reactive attributes.",
            timestamp=_now - timedelta(hours=1),
            channel_id="c1",
            read=True,
        ),
        Message(
            id="c1-5",
            user_id="me",
            username="You",
            text="Yeah it's awesome! Building a TUI client with it right now.",
            timestamp=_now - timedelta(minutes=40),
            channel_id="c1",
            out=True,
            read=True,
        ),
        Message(
            id="c1-6",
            user_id="u2",
            username="Bob",
            text="Wait you're building a Telegram client in the terminal?",
            timestamp=_now - timedelta(minutes=30),
            channel_id="c1",
            read=True,
        ),
        Message(
            id="c1-7",
            user_id="me",
            username="You",
            text="Yep! Check out the repo when it's ready 🚀",
            timestamp=_now - timedelta(minutes=25),
            channel_id="c1",
            out=True,
            read=False,
            reply_to_msg_id="c1-6",
        ),
        Message(
            id="c1-8",
            user_id="u3",
            username="Carol",
            text="That sounds really cool, can't wait to try it!",
            timestamp=_now - timedelta(minutes=5),
            channel_id="c1",
            read=False,
        ),
    ],
    "c2": [
        Message(
            id="c2-1",
            user_id="u2",
            username="Bob",
            text="anyone tried the new rust-based terminal emulators?",
            timestamp=_now - timedelta(days=1, hours=2),
            channel_id="c2",
            read=True,
        ),
        Message(
            id="c2-2",
            user_id="u1",
            username="Alice",
            text="ghostty is pretty nice actually",
            timestamp=_now - timedelta(days=1, hours=1),
            channel_id="c2",
            read=True,
        ),
        Message(
            id="c2-3",
            user_id="me",
            username="You",
            text="I'm still on alacritty lol same",
            timestamp=_now - timedelta(days=1),
            channel_id="c2",
            out=True,
            read=True,
        ),
    ],
    "c3": [
        Message(
            id="c3-1",
            user_id="u1",
            username="Alice",
            text="just opened a PR for the new auth flow",
            timestamp=_now - timedelta(hours=5),
            channel_id="c3",
            read=True,
        ),
        Message(
            id="c3-2",
            user_id="u2",
            username="Bob",
            text="reviewing now",
            timestamp=_now - timedelta(hours=4),
            channel_id="c3",
            read=True,
        ),
        Message(
            id="c3-3",
            user_id="me",
            username="You",
            text="LGTM, approving",
            timestamp=_now - timedelta(hours=3),
            channel_id="c3",
            out=True,
            read=True,
        ),
        Message(
            id="c3-4",
            user_id="u1",
            username="Alice",
            text="PR merged 🎉",
            timestamp=_now - timedelta(hours=1),
            channel_id="c3",
            read=False,
        ),
    ],
    "c4": [
        Message(
            id="c4-1",
            user_id="u1",
            username="Alice",
            text="hey, free for lunch tomorrow?",
            timestamp=_now - timedelta(hours=6),
            channel_id="c4",
            read=True,
        ),
        Message(
            id="c4-2",
            user_id="me",
            username="You",
            text="yeah definitely, where?",
            timestamp=_now - timedelta(hours=5),
            channel_id="c4",
            out=True,
            read=True,
        ),
        Message(
            id="c4-3",
            user_id="u1",
            username="Alice",
            text="that new ramen place on main st?",
            timestamp=_now - timedelta(hours=4),
            channel_id="c4",
            read=True,
        ),
        Message(
            id="c4-4",
            user_id="me",
            username="You",
            text="sounds good!",
            timestamp=_now - timedelta(hours=3),
            channel_id="c4",
            out=True,
            read=True,
        ),
    ],
}

_msg_counter = len(sum(_MESSAGES.values(), []))


class MockClient:
    current_user: User | None = _ME
    current_user_id: str | None = "me"
    users: dict[str, User] = _USERS
    channels: dict[str, Channel] = {ch.id: ch for ch in _CHANNELS}
    channel_list: list[Channel] = list(_CHANNELS)
    on_new_message: Callable | None = None
    _main_loop: asyncio.AbstractEventLoop | None = None

    async def is_authorized(self) -> bool:
        return True

    async def get_me(self) -> User | None:
        return _ME

    async def reset_session(self) -> None:
        pass

    async def send_code(self, phone: str) -> None:  # noqa: ARG002
        pass

    async def resend_code_sms(self, phone: str) -> None:  # noqa: ARG002
        pass

    async def sign_in(self, phone: str, code: str) -> User:  # noqa: ARG002
        return _ME

    async def sign_in_with_password(self, password: str) -> User:  # noqa: ARG002
        return _ME

    async def load_dialogs(self, limit: int = 100) -> None:  # noqa: ARG002
        pass

    async def disconnect(self) -> None:
        pass

    async def get_channel_messages(
        self, channel_id: str, limit: int = 50
    ) -> list[Message]:  # noqa: ARG002
        await asyncio.sleep(0.05)
        return list(_MESSAGES.get(channel_id, []))

    async def add_message(
        self,
        text: str,
        channel_id: str,
        reply_to_msg_id: str | None = None,
    ) -> Message:
        global _msg_counter
        _msg_counter += 1
        msg = Message(
            id=f"{channel_id}-{_msg_counter}",
            user_id="me",
            username="You",
            text=text,
            timestamp=datetime.now(),
            channel_id=channel_id,
            out=True,
            read=False,
            reply_to_msg_id=reply_to_msg_id,
        )
        _MESSAGES.setdefault(channel_id, []).append(msg)
        ch = self.channels.get(channel_id)
        if ch:
            ch.last_message = text
        return msg

    async def send_file(
        self,
        channel_id: str,
        file_path: str,
        caption: str = "",
        reply_to_msg_ud: str | None = None,  # noqa: ARG002 — protocol compat
    ) -> Message:
        return await self.add_message(f"[File: {file_path}] {caption}", channel_id)

    async def mark_as_read(self, channel_id: str) -> None:
        ch = self.channels.get(channel_id)
        if ch:
            ch.unread = 0

    async def forward_message(
        self, from_channel_id: str, to_channel_id: str, message_id: str  # noqa: ARG002
    ) -> None:
        pass

    async def create_group(self, title: str) -> Channel:
        ch = Channel(id=f"new-{title}", name=title, topic="")
        self.channels[ch.id] = ch
        self.channel_list.append(ch)
        return ch

    async def search_global(
        self, query: str, limit: int = 20
    ) -> list[Channel]:  # noqa: ARG002
        return []

    async def open_channel(self, channel_id: str) -> Channel:
        return self.channels[channel_id]

    def start_auto_reply(self, channel_id: str) -> None:  # noqa: ARG002
        pass
