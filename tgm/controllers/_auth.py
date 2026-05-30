from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from tgm.screens.login.events import (
    CodeSubmitted,
    PasswordSubmitted,
    PhoneSubmitted,
    SmsRequested,
)

if TYPE_CHECKING:
    from tgm.core.protocol import ClientProtocol
    from tgm.screens import LoginScreen as _LoginScreen


class _AuthMixin:
    client: ClientProtocol | None
    current_channel_id: str | None
    _skip_login: bool

    def on_mount(self) -> None:
        if self._skip_login:
            return
        from tgm.screens import LoginScreen

        loading = self.client is not None
        self.push_screen(LoginScreen(loading=loading))  # type: ignore[attr-defined]

    def on_login_screen_phone_submitted(self, event: PhoneSubmitted) -> None:
        self.run_worker(self._send_code(event.phone), exclusive=True)  # type: ignore[attr-defined]

    def on_login_screen_code_submitted(self, event: CodeSubmitted) -> None:
        self.run_worker(self._verify_code(event.phone, event.code), exclusive=True)  # type: ignore[attr-defined]

    def on_login_screen_password_submitted(self, event: PasswordSubmitted) -> None:
        self.run_worker(self._verify_password(event.password), exclusive=True)  # type: ignore[attr-defined]

    def on_login_screen_sms_requested(self, event: SmsRequested) -> None:
        self.run_worker(self._resend_sms(event.phone), exclusive=True)  # type: ignore[attr-defined]

    def _login_screen(self) -> _LoginScreen:
        from tgm.screens import LoginScreen

        return self.query_one(LoginScreen)  # type: ignore[attr-defined]

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

        if self.client:
            if self.client.channel_list:
                self.current_channel_id = self.client.channel_list[0].id
            self.run_worker(self._client_event_reader(), exclusive=False, group="client-events")  # type: ignore[attr-defined]
        self.push_screen(ChatScreen())  # type: ignore[attr-defined]

    async def _client_event_reader(self) -> None:
        from tgm.core.client_events import NewMessageEvent, StatusChangeEvent
        from tgm.screens.chat.events import MessageSent

        try:
            while self.client:
                event = await self.client.event_queue.get()
                if isinstance(event, NewMessageEvent):
                    msg = event.msg
                    if msg.channel_id == self.current_channel_id:
                        self._post_to_chat(MessageSent(msg.channel_id, msg))  # type: ignore[attr-defined]
                    self._refresh_channel_list()  # type: ignore[attr-defined]
                elif isinstance(event, StatusChangeEvent):
                    self._refresh_status_ui()  # type: ignore[attr-defined]
        except asyncio.CancelledError:
            pass
