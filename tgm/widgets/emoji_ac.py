from __future__ import annotations

from textual.widget import Widget


class EmojiAutocomplete(Widget):

    is_showing: bool = False

    _results: list[str]
    _selected: int

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._results = []
        self._selected = 0

    def get_selected_emoji(self) -> str | None:
        if self._results and 0 <= self._selected < len(self._results):
            return self._results[self._selected]
        return None

    def show_results(self, _text: str) -> None:
        pass

    def hide(self) -> None:
        self.is_showing = False
        self.display = False

    def select_next(self) -> None:
        if self._results:
            self._selected = (self._selected + 1) % len(self._results)

    def select_prev(self) -> None:
        if self._results:
            self._selected = (self._selected - 1) % len(self._results)
