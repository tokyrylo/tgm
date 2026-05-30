from __future__ import annotations

import asyncio
from typing import Protocol, cast

from textual.containers import Horizontal
from textual.widgets import Static

from tgm.widgets.emoji.data import search_emojis


class AppContext(Protocol):
    emoji_trigger: str


class EmojiAutocomplete(Horizontal):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._results: list[tuple[str, str, str]] = []
        self._selected = 0
        self._gen = 0
        self._widgets: list[Static] = []

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    @property
    def is_showing(self) -> bool:
        return self.has_class("visible")

    def _extract_term(self, query: str) -> str | None:
        trigger = self.ctx.emoji_trigger
        idx = query.rfind(trigger)
        if idx < 0 or idx == len(query) - 1:
            return None
        return query[idx + len(trigger) :].strip() or None

    def show_results(self, query: str) -> None:
        self._gen += 1
        gen = self._gen
        term = self._extract_term(query)
        if not term:
            self.hide()
            return
        self.run_worker(self._fetch(term, gen), exclusive=True, group="emoji-ac")

    async def _fetch(self, term: str, gen: int) -> None:
        results = await asyncio.to_thread(search_emojis, term, 12)
        self.call_after_refresh(self._apply, results, gen)

    def _apply(self, results: list[tuple[str, str, str]], gen: int) -> None:
        if gen != self._gen:
            return
        if not results:
            self.hide()
            return

        prev_name = (
            self._results[self._selected][1]
            if self._results and self._selected < len(self._results)
            else None
        )

        self._results = results
        self._selected = (
            next(
                (i for i, (_, name, _) in enumerate(results) if name == prev_name),
                0,
            )
            if prev_name
            else 0
        )
        self._selected = min(self._selected, len(results) - 1)

        self._sync_widgets()
        self.call_after_refresh(self._finalize_render)

    def _sync_widgets(self) -> None:
        if len(self._widgets) == len(self._results):
            for widget, (emoji, name, _) in zip(self._widgets, self._results):
                widget.update(f"{emoji} :{name}:")
        else:
            for w in self._widgets:
                w.remove()
            self._widgets = [
                Static(f"{emoji} :{name}:")
                for emoji, name, _ in self._results
            ]
            self.mount_all(self._widgets)

    def _finalize_render(self) -> None:
        self._update_selection()
        self.add_class("visible")
        self.scroll_home(animate=False)

    def hide(self) -> None:
        self._gen += 1
        self._results = []
        self._selected = 0
        for w in self._widgets:
            w.remove()
        self._widgets = []
        self.remove_class("visible")

    def select_next(self) -> None:
        if not self._results:
            return
        self._selected = (self._selected + 1) % len(self._results)
        self._update_selection()

    def select_prev(self) -> None:
        if not self._results:
            return
        self._selected = (self._selected - 1) % len(self._results)
        self._update_selection()

    def get_selected_emoji(self) -> str | None:
        if not self._results or self._selected >= len(self._results):
            return None
        return self._results[self._selected][0]

    def _update_selection(self) -> None:
        if not self._widgets:
            return
        for i, w in enumerate(self._widgets):
            w.set_class(i == self._selected, "highlighted")
        self._widgets[self._selected].scroll_visible(animate=False)
