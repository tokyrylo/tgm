from __future__ import annotations

from typing import TypeVar

from textual.screen import ModalScreen, Screen

_RT = TypeVar("_RT")


class TgmScreen(Screen):
    @property
    def app(self):
        return super().app


class TgmModalScreen(ModalScreen[_RT]):
    @property
    def app(self):
        return super().app
