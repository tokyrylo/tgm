from __future__ import annotations

import hashlib
from typing import Any, cast

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import ListItem, Static

from tgm.config import ACCENT_THEMES, CHANNEL_COLORS, PALETTE
from tgm.core.app_context import AppContext
from tgm.core.models.channel import Channel
from tgm.media.avatar import avatar_markup, get_cached_avatar, placeholder_avatar_markup

_BADGE_DEFAULT_COLOR = PALETTE["accent_default"]
_LAST_MAX_LEN = 24
_UNSET = object()  # sentinel: "never computed yet"


def _stable_color(channel_id: str) -> str:
    h = int(hashlib.md5(channel_id.encode()).hexdigest(), 16)
    return CHANNEL_COLORS[h % len(CHANNEL_COLORS)]


class ChannelPreview(ListItem):

    def __init__(self, channel: Channel, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.channel = channel
        # avatar diff: compare blob identity (O(1)), not rendered markup
        self._avatar_source: object = _UNSET
        # diff caches: raw values, not rendered markup
        self._c_name_raw: str = ""
        self._c_last_raw: str = ""
        self._c_unread: int = -1
        self._c_accent: str | None = None
        self._c_online: bool | None = None

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    # compose = structure only; data flows via on_mount → refresh_content
    def compose(self) -> ComposeResult:
        self._avatar_w = Static(classes="channel-avatar")
        self._name_w = Static(classes="channel-name")
        self._last_w = Static(classes="channel-last")
        self._badge_w = Static(classes="channel-badge")
        with Horizontal():
            yield self._avatar_w
            with Vertical(classes="channel-info"):
                yield self._name_w
                yield self._last_w
            yield self._badge_w

    def on_mount(self) -> None:
        self.refresh_content()

    def invalidate_avatar(self) -> None:
        self._avatar_source = _UNSET

    def _render_avatar(self, source: Any) -> str:
        if source is not None:
            result = avatar_markup(source, cols=4, rows=3)
            if result:
                return result
        return placeholder_avatar_markup(_stable_color(self.channel.id), cols=4, rows=3)

    def _peer_online(self) -> bool:
        if not self.channel.is_dm or not self.channel.peer_user_id:
            return False
        user = self.ctx.users.get(self.channel.peer_user_id)
        return bool(user and user.online)

    def _format_last(self) -> str:
        last = self.channel.last_message or "No messages yet"
        return last[:_LAST_MAX_LEN] + "…" if len(last) > _LAST_MAX_LEN else last

    def refresh_content(self, channel: Channel | None = None) -> None:
        if channel is not None:
            if channel.id != self.channel.id:
                self.invalidate_avatar()
            self.channel = channel

        # avatar: O(1) identity check on blob, not string comparison of markup
        source = get_cached_avatar(self.channel.id)
        if source is not self._avatar_source:
            self._avatar_w.update(self._render_avatar(source))
            self._avatar_source = source

        name = self.channel.name
        online = self._peer_online()
        if name != self._c_name_raw or online != self._c_online:
            dot = " [green]●[/]" if online else ""
            self._name_w.update(f"[bold white]{name}[/]{dot}")
            self._c_name_raw = name
            self._c_online = online

        last = self._format_last()
        if last != self._c_last_raw:
            self._last_w.update(f"[dim white]{last}[/]")
            self._c_last_raw = last

        self._update_badge()

    def _update_badge(self) -> None:
        unread = self.channel.unread
        accent = ACCENT_THEMES.get(self.ctx.accent_theme, _BADGE_DEFAULT_COLOR)
        if unread == self._c_unread and accent == self._c_accent:
            return
        self._c_unread = unread
        self._c_accent = accent
        self._badge_w.display = bool(unread)
        self._badge_w.update(f"[white on {accent}] {unread} [/]" if unread else "")
