from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App

from tgm.config.settings_store import load_global as _load_global
from tgm.core import ClientProtocol
from tgm.screens import LoginScreen
from tgm.screens.login.events import (
    CodeSubmitted,
    PasswordSubmitted,
    PhoneSubmitted,
    SmsRequested,
)

if TYPE_CHECKING:
    from tgm.core.models.channel import Channel
    from tgm.core.models.messages import Message


_STYLE = Path(__file__).parent / "static" / "styles" / "style.tcss"


class TgmApp(App):
    CSS_PATH = _STYLE

    def __init__(self) -> None:
        super().__init__()
        self.client: ClientProtocol | None = None
        self.current_channel_id: str | None = None
        self.reply_to_msg: Message | None = None
        self._skip_login: bool = False

        s = _load_global()
        self.emoji_trigger: str = s["emoji_trigger"]
        self.enter_to_send: bool = s["enter_to_send"]
        self.show_timestamps: bool = s["show_timestamps"]
        self.accent_theme: str = s["accent_theme"]
        self.big_msg_threshold: int = s["big_msg_threshold"]

    @property
    def channels(self) -> list[Channel]:
        return self.client.channel_list if self.client else []

    def on_mount(self) -> None:
        if self._skip_login:
            return
        loading = self.client is not None
        if self.client:
            self.client._main_loop = asyncio.get_event_loop()
        self.push_screen(LoginScreen(loading=loading))

    def on_login_screen_phone_submitted(self, event: PhoneSubmitted) -> None:
        self.run_worker(self._send_code(event.phone), exclusive=True)

    def on_login_screen_code_submitted(self, event: CodeSubmitted) -> None:
        self.run_worker(self._verify_code(event.phone, event.code), exclusive=True)

    def on_login_screen_password_submitted(self, event: PasswordSubmitted) -> None:
        self.run_worker(self._verify_password(event.password), exclusive=True)

    def on_login_screen_sms_requested(self, event: SmsRequested) -> None:
        self.run_worker(self._resend_sms(event.phone), exclusive=True)

    def _login_screen(self) -> LoginScreen:
        return self.query_one(LoginScreen)

    async def _send_code(self, phone: str) -> None:
        if not self.client:
            return
        try:
            await self.client.send_code(phone)
            self._login_screen().advance_to_code(phone)
        except Exception as e:
            self._login_screen().show_error(str(e))

    async def _verify_code(self, phone: str, code: str) -> None:
        if not self.client:
            return
        try:
            await self.client.sign_in(phone, code)
            self._on_login_done()
        except Exception as e:
            if "password" in str(e).lower():
                self._login_screen().advance_to_password()
            else:
                self._login_screen().show_error(str(e))

    async def _verify_password(self, password: str) -> None:
        if not self.client:
            return
        try:
            await self.client.sign_in_with_password(password)
            self._on_login_done()
        except Exception as e:
            self._login_screen().show_error(str(e))

    async def _resend_sms(self, phone: str) -> None:
        if not self.client:
            return
        try:
            await self.client.resend_code_sms(phone)
            self._login_screen().advance_to_code(phone)
        except Exception as e:
            self._login_screen().show_error(str(e))

    def _on_login_done(self) -> None:
        from tgm.screens.chat.screen import ChatScreen

        if self.client and self.client.channel_list:
            self.current_channel_id = self.client.channel_list[0].id
        self.push_screen(ChatScreen())
