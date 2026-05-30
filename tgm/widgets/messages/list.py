from __future__ import annotations

from datetime import date as date_cls
from typing import Protocol, cast

from textual.widgets import RichLog

from tgm.config.themes import ACCENT_THEMES, PALETTE
from tgm.core.models.messages import Message
from tgm.core.protocol import ClientProtocol

from .bubble import Bubble, RenderContext, render_bubble, render_date_sep

_ACCENT_DEFAULT = PALETTE["accent_default"]


class AppContext(Protocol):
    show_timestamps: bool
    accent_theme: str
    big_msg_threshold: int
    client: ClientProtocol


class MessageList(RichLog):

    def __init__(self, **kwargs) -> None:
        super().__init__(highlight=True, markup=True, wrap=True, max_lines=None, **kwargs)
        self._msgs: list[Message] = []
        self._msgs_by_id: dict[str, Message] = {}
        self._rendered: list[Bubble] = []
        self._search_query: str = ""
        self._match_indices: list[int] = []
        self._current_match: int = -1

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    # ── public API ────────────────────────────────────────────────────────────

    def load_messages(self, messages: list[Message]) -> None:
        self.clear()
        self._msgs = list(messages)
        self._msgs_by_id = {m.id: m for m in messages}
        self._rendered = []
        self._render_all(self._msgs, self._search_query)
        self.scroll_end(animate=False)

    def append_message(self, msg: Message) -> None:
        self._msgs.append(msg)
        self._msgs_by_id[msg.id] = msg
        if self._search_query:
            q = self._search_query.lower()
            if msg.text and q in msg.text.lower():
                self._match_indices.append(len(self._msgs) - 1)
        rctx = self._render_ctx()
        bubble = self._write_bubble(msg, self._search_query, rctx)
        self._rendered.append(bubble)
        self.scroll_end(animate=False)

    def search(self, query: str) -> tuple[int, int]:
        """Re-render with highlights. Returns (current_match, total_matches)."""
        self._search_query = query
        self._match_indices = []
        self._current_match = -1

        if query:
            q = query.lower()
            self._match_indices = [
                i for i, m in enumerate(self._msgs) if m.text and q in m.text.lower()
            ]

        self.clear()
        self._render_all(self._msgs, query)

        if self._match_indices:
            self._current_match = 0
            self._scroll_to_match(0)
            return 1, len(self._match_indices)

        if not query:
            self.scroll_end(animate=False)
        return 0, 0

    def next_match(self) -> tuple[int, int]:
        if not self._match_indices:
            return 0, 0
        self._current_match = (self._current_match + 1) % len(self._match_indices)
        self._scroll_to_match(self._current_match)
        return self._current_match + 1, len(self._match_indices)

    def prev_match(self) -> tuple[int, int]:
        if not self._match_indices:
            return 0, 0
        self._current_match = (self._current_match - 1) % len(self._match_indices)
        self._scroll_to_match(self._current_match)
        return self._current_match + 1, len(self._match_indices)

    # ── internals ─────────────────────────────────────────────────────────────

    def _avail(self) -> int:
        return max(80, self.size.width - 2) if self.size.width > 0 else 80

    def _render_ctx(self) -> RenderContext:
        ctx = self.ctx
        return RenderContext(
            width=self._avail(),
            accent=ACCENT_THEMES.get(ctx.accent_theme, _ACCENT_DEFAULT),
            show_ts=ctx.show_timestamps,
            large=ctx.big_msg_threshold > 0,
        )

    def _scroll_to_match(self, match_pos: int) -> None:
        msg_idx = self._match_indices[match_pos]
        total = max(len(self._msgs) - 1, 1)
        frac = msg_idx / total
        max_scroll = max(0, self.virtual_size.height - self.size.height)
        self.scroll_to(y=int(frac * max_scroll), animate=False)

    def _render_all(self, messages: list[Message], highlight_query: str = "") -> None:
        rctx = self._render_ctx()
        last_date: date_cls | None = None
        for msg in messages:
            msg_date = msg.timestamp.date()
            if last_date != msg_date:
                self.write(render_date_sep(msg.timestamp, rctx.width))
                last_date = msg_date
            bubble = self._write_bubble(msg, highlight_query, rctx)
            if not highlight_query:
                self._rendered.append(bubble)

    def _write_bubble(self, msg: Message, highlight_query: str, rctx: RenderContext) -> Bubble:
        ctx = self.ctx
        is_own = msg.user_id == ctx.client.current_user_id
        user = ctx.client.users.get(msg.user_id)
        bubble = render_bubble(
            msg,
            ctx=rctx,
            is_own=is_own,
            user=user,
            msgs_by_id=self._msgs_by_id,
            highlight_query=highlight_query,
        )
        for line in bubble.lines:
            self.write(line)
        return bubble
