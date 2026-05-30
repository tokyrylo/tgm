from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta

from tgm.core.client_events import ClientEvent, NewMessageEvent, StatusChangeEvent
from tgm.core.models.channel import Channel, ChannelInfo
from tgm.core.models.messages import Message
from tgm.core.models.user import User
from tgm.core.store import Store

# ── helpers ─────────────────────────────────────────────────────────────────

_now = datetime.now()


def _t(**kw) -> datetime:
    return _now - timedelta(**kw)


# ── users ────────────────────────────────────────────────────────────────────

_ME    = User(id="me",  name="You",            color="text",    username="you",         phone="+1 555 000 0000", bio="",                             online=True)
_ALICE = User(id="u1",  name="Alice Johnson",  color="#2B5278", username="alice_j",     phone="+44 7911 123456", bio="Product designer at Acme Corp", online=True)
_BOB   = User(id="u2",  name="Bob Smith",      color="#1E6B3A", username="bob_smith",   phone="+1 555 234 5678", bio="Backend engineer · Go & Rust",   online=False, last_seen=_now - timedelta(minutes=7))
_CAROL = User(id="u3",  name="Carol White",    color="#7A2D2D", username="carol_w",     phone="+1 555 345 6789", bio="Frontend dev 🎨",                 online=False, last_seen=_now - timedelta(hours=2))
_DAVE  = User(id="u4",  name="Dave Brown",     color="#4A2D7A", username="dave_brown",  phone="+1 555 456 7890", bio="DevOps & infra nerd",             online=True)
_EVE   = User(id="u5",  name="Eve Wilson",     color="#5E4A1E", username="eve_wilson",  phone="+1 555 567 8901", bio="Loves hiking and coffee ☕",      online=False, last_seen=_now - timedelta(days=1, hours=3))
_FRANK = User(id="u6",  name="Frank Lee",      color="#1E5E5E", username="franklee",    phone="+82 10-1234-5678", bio="",                               online=False, last_seen=_now - timedelta(minutes=34))
_GRACE = User(id="u7",  name="Grace Kim",      color="#6B1E6B", username="grace_k",     phone="+82 10-9876-5432", bio="UX researcher @ Acme",           online=True)

_USERS: dict[str, User] = {u.id: u for u in [_ME, _ALICE, _BOB, _CAROL, _DAVE, _EVE, _FRANK, _GRACE]}


def _msg(
    id: str,
    user: User,
    text: str,
    channel_id: str,
    ts: datetime,
    read: bool = True,
    out: bool = False,
    reply_to: str | None = None,
) -> Message:
    return Message(
        id=id,
        user_id=user.id,
        username=user.name,
        text=text,
        timestamp=ts,
        channel_id=channel_id,
        read=read,
        out=out,
        reply_to_msg_id=reply_to,
    )


# ── channels ─────────────────────────────────────────────────────────────────

_CHANNELS: list[Channel] = [
    Channel(id="g1", name="dev-team",       topic="Engineering discussions",          last_message="ship it 🚢",                    unread=5, pinned_message_id="g1-9"),
    Channel(id="g2", name="random",         topic="Off-topic, memes, water-cooler",   last_message="haha true 😂",                  unread=2),
    Channel(id="g3", name="design-squad",   topic="UI/UX feedback and assets",        last_message="updated the mockups",           unread=0),
    Channel(id="g4", name="ops-alerts",     topic="Infra & incidents",                last_message="deploy looks stable",           unread=0),
    Channel(id="d1", name="Alice Johnson",  topic="", last_message="see you there!",           unread=1, is_dm=True, peer_user_id="u1", pinned_message_id="d1-5"),
    Channel(id="d2", name="Bob Smith",      topic="", last_message="yeah let me check",          unread=0, is_dm=True, peer_user_id="u2"),
    Channel(id="d3", name="Eve Wilson",     topic="", last_message="sounds fun, I'm in",         unread=3, is_dm=True, peer_user_id="u5"),
    Channel(id="d4", name="Grace Kim",      topic="", last_message="thanks for the review 🙏",   unread=0, is_dm=True, peer_user_id="u7"),
]

# ── messages ──────────────────────────────────────────────────────────────────

_MESSAGES: dict[str, list[Message]] = {

    # ── dev-team ─────────────────────────────────────────────────────────────
    "g1": [
        _msg("g1-1",  _ALICE, "morning everyone 👋", "g1", _t(hours=8)),
        _msg("g1-2",  _BOB,   "o/", "g1", _t(hours=7, minutes=55)),
        _msg("g1-3",  _DAVE,  "anyone seen the latency spike from last night?", "g1", _t(hours=7, minutes=30)),
        _msg("g1-4",  _BOB,   "yeah, p99 hit 800ms around 2am. rolled back the cache change", "g1", _t(hours=7, minutes=20)),
        _msg("g1-5",  _DAVE,  "smart. we should add an alert for that", "g1", _t(hours=7, minutes=10)),
        _msg("g1-6",  _ME,    "on it, adding to the runbook too", "g1", _t(hours=7), out=True),
        _msg("g1-7",  _ALICE, "btw new feature branch is ready for review", "g1", _t(hours=6)),
        _msg("g1-8",  _ME,    "link?", "g1", _t(hours=5, minutes=50), out=True),
        _msg("g1-9",  _ALICE, "github.com/org/repo/pull/247", "g1", _t(hours=5, minutes=40)),
        _msg("g1-10", _BOB,   "reviewed, left a few comments", "g1", _t(hours=5)),
        _msg("g1-11", _ALICE, "thanks, addressing now", "g1", _t(hours=4, minutes=30)),
        _msg("g1-12", _CAROL, "just pushed fixes", "g1", _t(hours=4)),
        _msg("g1-13", _BOB,   "looks good, approving", "g1", _t(hours=3, minutes=30)),
        _msg("g1-14", _ALICE, "merged! deploying to staging", "g1", _t(hours=3), reply_to="g1-9"),
        _msg("g1-15", _DAVE,  "staging looks clean", "g1", _t(hours=2, minutes=30)),
        _msg("g1-16", _ME,    "deploying to prod in 10", "g1", _t(hours=2), out=True),
        _msg("g1-17", _BOB,   "watching metrics", "g1", _t(hours=1, minutes=50)),
        _msg("g1-18", _ME,    "deployed ✅", "g1", _t(hours=1, minutes=40), out=True),
        _msg("g1-19", _ALICE, "nice! ship it 🚢", "g1", _t(hours=1, minutes=30), read=False),
        _msg("g1-20", _CAROL, "🎉", "g1", _t(hours=1, minutes=20), read=False),
        _msg("g1-21", _DAVE,  "metrics stable 📈", "g1", _t(hours=1), read=False),
        _msg("g1-22", _BOB,   "love it", "g1", _t(minutes=45), read=False),
        _msg("g1-23", _ALICE, "ship it 🚢", "g1", _t(minutes=20), read=False),
    ],

    # ── random ───────────────────────────────────────────────────────────────
    "g2": [
        _msg("g2-1",  _FRANK, "https://xkcd.com/2347", "g2", _t(days=1, hours=3)),
        _msg("g2-2",  _BOB,   "HAHA the dependency graph one", "g2", _t(days=1, hours=2, minutes=50)),
        _msg("g2-3",  _EVE,   "so accurate it hurts", "g2", _t(days=1, hours=2, minutes=30)),
        _msg("g2-4",  _ME,    "our entire infra in one comic", "g2", _t(days=1, hours=2), out=True),
        _msg("g2-5",  _GRACE, "did anyone watch the Go keynote yesterday?", "g2", _t(days=1, hours=1)),
        _msg("g2-6",  _ALICE, "bits of it, range over funcs is finally in?", "g2", _t(days=1, hours=0, minutes=50)),
        _msg("g2-7",  _BOB,   "only took 10 years lmao", "g2", _t(days=1, hours=0, minutes=40)),
        _msg("g2-8",  _EVE,   "better late than never I guess", "g2", _t(days=1)),
        _msg("g2-9",  _FRANK, "anyone up for lunch today? the Thai place?", "g2", _t(hours=3)),
        _msg("g2-10", _CAROL, "+1", "g2", _t(hours=2, minutes=50)),
        _msg("g2-11", _GRACE, "can't, have a meeting till 2", "g2", _t(hours=2, minutes=40)),
        _msg("g2-12", _ME,    "I'm in, noon?", "g2", _t(hours=2, minutes=30), out=True),
        _msg("g2-13", _FRANK, "noon works", "g2", _t(hours=2, minutes=20)),
        _msg("g2-14", _BOB,   "this video of a cat debugging code is sending me", "g2", _t(hours=1, minutes=30), read=False),
        _msg("g2-15", _EVE,   "haha true 😂", "g2", _t(hours=1, minutes=10), read=False),
    ],

    # ── design-squad ─────────────────────────────────────────────────────────
    "g3": [
        _msg("g3-1",  _CAROL, "hey can someone review the new onboarding flow?", "g3", _t(days=2)),
        _msg("g3-2",  _GRACE, "sure, share the Figma link", "g3", _t(days=1, hours=23)),
        _msg("g3-3",  _CAROL, "figma.com/file/abc123", "g3", _t(days=1, hours=22)),
        _msg("g3-4",  _EVE,   "looking now... the step 3 transition feels abrupt", "g3", _t(days=1, hours=20)),
        _msg("g3-5",  _GRACE, "agreed, maybe add a fade?", "g3", _t(days=1, hours=19)),
        _msg("g3-6",  _CAROL, "good call, trying it", "g3", _t(days=1, hours=18)),
        _msg("g3-7",  _ME,    "the color contrast on the CTA button also looks off on dark mode", "g3", _t(days=1, hours=10), out=True),
        _msg("g3-8",  _CAROL, "oh you're right, fixing that too", "g3", _t(days=1, hours=9)),
        _msg("g3-9",  _EVE,   "much better, the flow feels smooth now", "g3", _t(hours=4)),
        _msg("g3-10", _GRACE, "updated the mockups", "g3", _t(hours=3)),
        _msg("g3-11", _CAROL, "shipping to eng tomorrow", "g3", _t(hours=2)),
    ],

    # ── ops-alerts ───────────────────────────────────────────────────────────
    "g4": [
        _msg("g4-1",  _FRANK, "[ALERT] CPU spike on prod-worker-03 — 94%", "g4", _t(hours=12)),
        _msg("g4-2",  _DAVE,  "on it", "g4", _t(hours=11, minutes=55)),
        _msg("g4-3",  _DAVE,  "rogue cron job, killed it", "g4", _t(hours=11, minutes=40)),
        _msg("g4-4",  _FRANK, "[RESOLVED] CPU back to normal", "g4", _t(hours=11, minutes=30)),
        _msg("g4-5",  _BOB,   "nice catch", "g4", _t(hours=11)),
        _msg("g4-6",  _ME,    "adding that job to monitoring", "g4", _t(hours=10, minutes=30), out=True),
        _msg("g4-7",  _FRANK, "[INFO] scheduled maintenance window tonight 11pm–1am UTC", "g4", _t(hours=6)),
        _msg("g4-8",  _DAVE,  "ack'd", "g4", _t(hours=5, minutes=50)),
        _msg("g4-9",  _BOB,   "ack'd", "g4", _t(hours=5, minutes=45)),
        _msg("g4-10", _ME,    "ack'd", "g4", _t(hours=5, minutes=40), out=True),
        _msg("g4-11", _FRANK, "[INFO] maintenance complete, all services green", "g4", _t(hours=1)),
        _msg("g4-12", _DAVE,  "deploy looks stable", "g4", _t(minutes=30)),
    ],

    # ── Alice DM ─────────────────────────────────────────────────────────────
    "d1": [
        _msg("d1-1",  _ALICE, "hey! are you coming to the team offsite next month?", "d1", _t(days=3)),
        _msg("d1-2",  _ME,    "yes! booked flights already", "d1", _t(days=3), out=True),
        _msg("d1-3",  _ALICE, "nice, we should plan a hike on the Friday", "d1", _t(days=2, hours=20)),
        _msg("d1-4",  _ME,    "100%, I've been wanting to try that coastal trail", "d1", _t(days=2, hours=19), out=True),
        _msg("d1-5",  _ALICE, "same! also there's a good sushi place near the hotel", "d1", _t(days=2, hours=18)),
        _msg("d1-6",  _ME,    "bookmarked, let's go Thursday evening?", "d1", _t(days=2, hours=17), out=True),
        _msg("d1-7",  _ALICE, "perfect, I'll see if Bob and Carol want to join", "d1", _t(days=2, hours=16)),
        _msg("d1-8",  _ME,    "great idea", "d1", _t(days=2, hours=15), out=True),
        _msg("d1-9",  _ALICE, "btw did you see the Q3 metrics? we're ahead of target 🎯", "d1", _t(hours=5)),
        _msg("d1-10", _ME,    "yeah saw that, really solid work from the whole team", "d1", _t(hours=4, minutes=50), out=True),
        _msg("d1-11", _ALICE, "agreed! catch up for coffee this week?", "d1", _t(hours=2)),
        _msg("d1-12", _ME,    "Wednesday afternoon?", "d1", _t(hours=1, minutes=50), out=True),
        _msg("d1-13", _ALICE, "see you there!", "d1", _t(minutes=30), read=False),
    ],

    # ── Bob DM ───────────────────────────────────────────────────────────────
    "d2": [
        _msg("d2-1",  _ME,    "hey Bob, do you have the credentials for the staging DB?", "d2", _t(days=1, hours=4), out=True),
        _msg("d2-2",  _BOB,   "yeah let me check", "d2", _t(days=1, hours=3, minutes=55)),
        _msg("d2-3",  _BOB,   "check 1password vault 'staging-infra', should be there", "d2", _t(days=1, hours=3, minutes=40)),
        _msg("d2-4",  _ME,    "got it, thanks!", "d2", _t(days=1, hours=3, minutes=30), out=True),
        _msg("d2-5",  _BOB,   "no prob. also heads up — I'm refactoring the auth module this week", "d2", _t(days=1, hours=3)),
        _msg("d2-6",  _ME,    "nice, let me know if you need a review", "d2", _t(days=1, hours=2, minutes=50), out=True),
        _msg("d2-7",  _BOB,   "will do. btw the integration tests are flaky again 🙄", "d2", _t(hours=3)),
        _msg("d2-8",  _ME,    "I'll take a look this afternoon", "d2", _t(hours=2, minutes=45), out=True),
        _msg("d2-9",  _BOB,   "yeah let me check", "d2", _t(hours=1)),
    ],

    # ── Eve DM ───────────────────────────────────────────────────────────────
    "d3": [
        _msg("d3-1",  _EVE,   "hey! hiking this weekend?", "d3", _t(days=1, hours=2)),
        _msg("d3-2",  _ME,    "yes!! which trail?", "d3", _t(days=1, hours=1, minutes=50), out=True),
        _msg("d3-3",  _EVE,   "thinking the ridge loop, about 12km", "d3", _t(days=1, hours=1, minutes=30)),
        _msg("d3-4",  _ME,    "perfect difficulty. Saturday or Sunday?", "d3", _t(days=1, hours=1), out=True),
        _msg("d3-5",  _EVE,   "Saturday morning? meet at the trailhead at 8?", "d3", _t(days=1, hours=0, minutes=45)),
        _msg("d3-6",  _ME,    "works for me, I'll bring snacks", "d3", _t(days=1, hours=0, minutes=30), out=True),
        _msg("d3-7",  _EVE,   "I'll bring coffee ☕", "d3", _t(days=1)),
        _msg("d3-8",  _ME,    "deal 🤝", "d3", _t(hours=5), out=True),
        _msg("d3-9",  _EVE,   "oh btw, Frank is joining too if that's ok?", "d3", _t(hours=2), read=False),
        _msg("d3-10", _EVE,   "sounds fun, I'm in", "d3", _t(hours=1), read=False),
        _msg("d3-11", _EVE,   "can't wait! 🏔️", "d3", _t(minutes=15), read=False),
    ],

    # ── Grace DM ─────────────────────────────────────────────────────────────
    "d4": [
        _msg("d4-1",  _GRACE, "hey, sent you the updated component library", "d4", _t(days=2, hours=3)),
        _msg("d4-2",  _ME,    "got it, reviewing now", "d4", _t(days=2, hours=2, minutes=50), out=True),
        _msg("d4-3",  _ME,    "this looks great! especially the new button variants", "d4", _t(days=2, hours=2), out=True),
        _msg("d4-4",  _GRACE, "glad you like it! added accessibility improvements too", "d4", _t(days=2, hours=1, minutes=30)),
        _msg("d4-5",  _ME,    "noticed that, the focus rings are much cleaner", "d4", _t(days=2, hours=1), out=True),
        _msg("d4-6",  _GRACE, "thanks! I'll publish to npm once Carol signs off", "d4", _t(days=2)),
        _msg("d4-7",  _ME,    "sounds good, thanks for the hard work on this 🙏", "d4", _t(days=1, hours=23), out=True),
        _msg("d4-8",  _GRACE, "thanks for the review 🙏", "d4", _t(days=1, hours=22)),
    ],
}

# ── auto-reply pools ──────────────────────────────────────────────────────────

_AUTO_REPLIES: dict[str, list[str]] = {
    "d1": ["haha totally agree", "good point!", "let me think about that...", "yeah sounds good to me", "👍", "interesting, I hadn't considered that", "makes sense!", "I'll check and get back to you", "LOL yes exactly", "that's a great idea actually"],
    "d2": ["yeah let me check", "makes sense", "on it", "roger that", "hmm good point", "I'll push a fix shortly", "can you share more context?", "noted", "checked, should be working now", "👀"],
    "d3": ["haha yes!!", "omg same", "that's so fun!", "can't wait 🎉", "sounds perfect", "I'm down", "yesss", "oh wow really?", "love that idea", "🙌"],
    "d4": ["thanks!", "good catch", "will fix", "noted, updating the design", "great feedback", "on it 🎨", "appreciate it!", "checking now", "done!", "makes total sense"],
    "g1": ["nice", "👍", "lgtm", "on it", "makes sense", "good call", "agreed", "let's do it", "🚀", "shipped"],
    "g2": ["lmaooo", "so true", "🤣", "same", "+1", "classic", "haha", "no way", "facts", "this is the way"],
}

_AUTO_REPLY_USERS: dict[str, list[User]] = {
    "d1": [_ALICE],
    "d2": [_BOB],
    "d3": [_EVE],
    "d4": [_GRACE],
    "g1": [_ALICE, _BOB, _CAROL, _DAVE],
    "g2": [_BOB, _EVE, _FRANK, _GRACE],
    "g3": [_CAROL, _EVE, _GRACE],
    "g4": [_DAVE, _FRANK],
}

_msg_counter = sum(len(v) for v in _MESSAGES.values())


class MockClient:
    def __init__(self) -> None:
        self.store = Store(
            users=dict(_USERS),
            channels={ch.id: ch for ch in _CHANNELS},
            channel_list=list(_CHANNELS),
            current_user=_ME,
            current_user_id="me",
        )
        self.event_queue: asyncio.Queue[ClientEvent] = asyncio.Queue()
        self._status_task_started = False

    # ── Store convenience accessors (protocol requirement) ───────────────────

    @property
    def users(self) -> dict[str, User]:
        return self.store.users

    @property
    def channels(self) -> dict[str, Channel]:
        return self.store.channels

    @property
    def channel_list(self) -> list[Channel]:
        return self.store.channel_list

    @property
    def current_user(self) -> User | None:
        return self.store.current_user

    @property
    def current_user_id(self) -> str | None:
        return self.store.current_user_id

    # ── auth ─────────────────────────────────────────────────────────────────

    async def is_authorized(self) -> bool:
        return True

    async def get_me(self) -> User | None:
        return _ME

    async def reset_session(self) -> None:
        pass

    async def send_code(self, phone: str) -> None:
        pass

    async def resend_code_sms(self, phone: str) -> None:
        pass

    async def sign_in(self, phone: str, code: str) -> User:
        return _ME

    async def sign_in_with_password(self, password: str) -> User:
        return _ME

    # ── lifecycle ────────────────────────────────────────────────────────────

    async def load_dialogs(self, limit: int = 100) -> None:
        if not self._status_task_started:
            self._status_task_started = True
            asyncio.ensure_future(self._simulate_statuses())

    async def disconnect(self) -> None:
        pass

    # ── messaging ────────────────────────────────────────────────────────────

    async def get_channel_messages(
        self, channel_id: str, limit: int = 50
    ) -> list[Message]:
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
        ch = self.store.channels.get(channel_id)
        if ch:
            ch.last_message = text

        if channel_id in _AUTO_REPLY_USERS:
            loop = asyncio.get_event_loop()
            loop.call_later(
                random.uniform(1.5, 3.5),
                lambda: asyncio.ensure_future(self._auto_reply(channel_id)),
            )
        return msg

    async def _auto_reply(self, channel_id: str) -> None:
        users = _AUTO_REPLY_USERS.get(channel_id, [])
        pool = _AUTO_REPLIES.get(channel_id, ["👍"])
        if not users:
            return

        global _msg_counter
        _msg_counter += 1
        user = random.choice(users)
        text = random.choice(pool)
        msg = Message(
            id=f"{channel_id}-{_msg_counter}",
            user_id=user.id,
            username=user.name,
            text=text,
            timestamp=datetime.now(),
            channel_id=channel_id,
            read=False,
        )
        _MESSAGES.setdefault(channel_id, []).append(msg)
        ch = self.store.channels.get(channel_id)
        if ch:
            ch.last_message = text
            ch.unread += 1
        self.event_queue.put_nowait(NewMessageEvent(msg))

    async def send_file(
        self,
        channel_id: str,
        file_path: str,
        caption: str = "",
        reply_to_msg_ud: str | None = None,
    ) -> Message:
        return await self.add_message(f"[File: {file_path}] {caption}", channel_id)

    async def mark_as_read(self, channel_id: str) -> None:
        ch = self.store.channels.get(channel_id)
        if ch:
            ch.unread = 0

    async def forward_message(
        self, from_channel_id: str, to_channel_id: str, message_id: str
    ) -> None:
        pass

    # ── channels ─────────────────────────────────────────────────────────────

    async def create_group(self, title: str) -> Channel:
        ch = Channel(id=f"new-{title}", name=title, topic="")
        self.store.channels[ch.id] = ch
        self.store.channel_list.append(ch)
        return ch

    async def search_global(self, query: str, limit: int = 20) -> list[Channel]:
        await asyncio.sleep(0.05)
        if not query:
            return []
        q = query.lower()
        results: list[Channel] = []
        seen: set[str] = set()
        for ch in _CHANNELS:
            if q in ch.name.lower() or q in (ch.topic or "").lower():
                results.append(ch)
                seen.add(ch.id)
        for channel_id, messages in _MESSAGES.items():
            if channel_id in seen:
                continue
            if any(msg.text and q in msg.text.lower() for msg in messages):
                ch = self.store.channels.get(channel_id)
                if ch:
                    results.append(ch)
                    seen.add(channel_id)
        return results[:limit]

    async def open_channel(self, channel_id: str) -> Channel:
        return self.store.channels[channel_id]

    async def get_channel_info(self, channel_id: str) -> ChannelInfo:
        await asyncio.sleep(0.05)
        channel = self.store.channels[channel_id]
        is_dm = channel_id.startswith("d")

        if is_dm:
            dm_user_map = {"d1": _ALICE, "d2": _BOB, "d3": _EVE, "d4": _GRACE}
            user = dm_user_map.get(channel_id)
            return ChannelInfo(channel=channel, is_dm=True, user=user, members_count=2)

        group_members: dict[str, list[User]] = {
            "g1": [_ME, _ALICE, _BOB, _CAROL, _DAVE],
            "g2": [_ME, _ALICE, _BOB, _EVE, _FRANK, _GRACE],
            "g3": [_ME, _CAROL, _EVE, _GRACE],
            "g4": [_ME, _DAVE, _FRANK, _BOB],
        }
        members = group_members.get(channel_id, [_ME])
        return ChannelInfo(
            channel=channel,
            is_dm=False,
            members=members,
            members_count=len(members),
        )

    async def pin_message(self, channel_id: str, message_id: str) -> None:
        await asyncio.sleep(0.05)
        ch = self.store.channels.get(channel_id)
        if ch:
            ch.pinned_message_id = message_id

    async def unpin_message(self, channel_id: str) -> None:
        await asyncio.sleep(0.05)
        ch = self.store.channels.get(channel_id)
        if ch:
            ch.pinned_message_id = None

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        await asyncio.sleep(0.05)
        msgs = _MESSAGES.get(channel_id, [])
        _MESSAGES[channel_id] = [m for m in msgs if m.id != message_id]

    async def edit_message(self, channel_id: str, message_id: str, text: str) -> None:
        await asyncio.sleep(0.05)
        for msg in _MESSAGES.get(channel_id, []):
            if msg.id == message_id:
                msg.text = text
                break

    # ── background simulation ─────────────────────────────────────────────────

    async def _simulate_statuses(self) -> None:
        dm_user_ids = ["u1", "u2", "u5", "u7"]
        while True:
            await asyncio.sleep(random.uniform(10, 20))
            user_id = random.choice(dm_user_ids)
            user = self.store.users.get(user_id)
            if not user:
                continue
            if user.online:
                user.online = False
                user.last_seen = datetime.now()
            else:
                user.online = True
            self.event_queue.put_nowait(
                StatusChangeEvent(user_id, user.online, user.last_seen)
            )
