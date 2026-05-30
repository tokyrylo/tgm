from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App

from tgm.config.keybindings import (
    get_binding_objects,
    reload as _reload_bindings,
    save_binding as _save_binding,
)
from tgm.config.settings_store import (
    load_channel_settings as _load_channel_settings,
    load_global as _load_global,
    save_channel_settings as _save_channel_settings,
    save_global as _save_global,
    save_telegram as _save_telegram,
)
from tgm.core import ClientProtocol
from tgm.core.models.channel import ChannelSettings
from tgm.screens import LoginScreen
from tgm.screens.chat.events import MessageDeleted, MessageEdited, MessageSent, MessagesLoaded, MessagesLoading
from tgm.widgets.input.events import DeleteMessage, EditMessage
from tgm.screens.search.events import ChannelChosen
from tgm.screens.settings.events import (
    ChannelSettingChanged,
    GlobalSettingChanged,
    KeybindingChanged,
    TelegramCredentialsSave,
)
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
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = get_binding_objects("app")

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
        self.notifications: bool = s["notifications"]
        self.message_density: str = s["message_density"]
        self.text_wrap: bool = s["text_wrap"]
        self.text_opacity: float = s["text_opacity"]
        self._channel_settings: dict[str, ChannelSettings] = _load_channel_settings()

    @property
    def channels(self) -> list[Channel]:
        return self.client.channel_list if self.client else []

    def save_global_settings(self, **kwargs) -> None:
        _save_global(**kwargs)

    def get_channel_settings(self, channel_id: str) -> ChannelSettings:
        return self._channel_settings.get(channel_id, ChannelSettings())

    def update_channel_settings(self, channel_id: str, **kwargs) -> None:
        settings = self._channel_settings.setdefault(channel_id, ChannelSettings())
        for k, v in kwargs.items():
            setattr(settings, k, v)
        _save_channel_settings(channel_id, **kwargs)

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

    def load_messages(self, channel_id: str | None) -> None:
        if not channel_id or not self.client or channel_id not in self.client.channels:
            return
        self.run_worker(self._fetch_messages(channel_id), exclusive=True, group="msg-load")

    def send_message(self, channel_id: str, text: str, reply_to_id: str | None) -> None:
        self.run_worker(
            self._do_send(channel_id, text, reply_to_id), exclusive=False, group="msg-send"
        )

    async def _fetch_messages(self, channel_id: str) -> None:
        self._post_to_chat(MessagesLoading(channel_id))
        try:
            messages = await self.client.get_channel_messages(channel_id)  # type: ignore[union-attr]
        except Exception:
            messages = []
        self._post_to_chat(MessagesLoaded(channel_id, messages))

    async def _do_send(self, channel_id: str, text: str, reply_to_id: str | None) -> None:
        if not self.client:
            return
        try:
            msg = await self.client.add_message(text, channel_id, reply_to_msg_id=reply_to_id)
            self._post_to_chat(MessageSent(channel_id, msg))
        except Exception:
            pass

    def _post_to_chat(self, message) -> None:
        from tgm.screens.chat.screen import ChatScreen

        for screen in self.screen_stack:
            if isinstance(screen, ChatScreen):
                screen.post_message(message)
                return

    def action_open_settings(self) -> None:
        from tgm.screens.settings.screen import SettingsScreen

        self.push_screen(SettingsScreen())

    def action_open_chat_settings(self) -> None:
        from tgm.screens.chat.info import ChannelInfoModal

        if self.current_channel_id:
            self.push_screen(ChannelInfoModal(self.current_channel_id))

    def on_global_setting_changed(self, event: GlobalSettingChanged) -> None:
        setattr(self, event.key, event.value)
        _save_global(**{event.key: event.value})

    def on_channel_setting_changed(self, event: ChannelSettingChanged) -> None:
        self.update_channel_settings(event.channel_id, **{event.key: event.value})

    def on_keybinding_changed(self, event: KeybindingChanged) -> None:
        _save_binding(event.section, event.short, event.key)
        _reload_bindings()

    def on_telegram_credentials_save(self, event: TelegramCredentialsSave) -> None:
        _save_telegram(event.api_id, event.api_hash)

    def on_delete_message(self, event: DeleteMessage) -> None:
        event.stop()
        if self.current_channel_id:
            self.run_worker(
                self._do_delete(self.current_channel_id, event.msg_id),
                exclusive=False, group="msg-delete",
            )

    def on_edit_message(self, event: EditMessage) -> None:
        event.stop()
        if self.current_channel_id:
            self.run_worker(
                self._do_edit(self.current_channel_id, event.msg_id, event.text),
                exclusive=False, group="msg-edit",
            )

    async def _do_delete(self, channel_id: str, msg_id: str) -> None:
        if not self.client:
            return
        try:
            await self.client.delete_message(channel_id, msg_id)
            self._post_to_chat(MessageDeleted(channel_id, msg_id))
        except Exception:
            pass

    async def _do_edit(self, channel_id: str, msg_id: str, text: str) -> None:
        if not self.client:
            return
        try:
            await self.client.edit_message(channel_id, msg_id, text)
            self._post_to_chat(MessageEdited(channel_id, msg_id, text))
        except Exception:
            pass

    def on_channel_chosen(self, event: ChannelChosen) -> None:
        event.stop()
        self.current_channel_id = event.channel_id
        self.load_messages(event.channel_id)

    def _on_login_done(self) -> None:
        from tgm.screens.chat.screen import ChatScreen

        if self.client:
            self.client.on_status_change = self._on_status_change_cb
            if self.client.channel_list:
                self.current_channel_id = self.client.channel_list[0].id
        self.push_screen(ChatScreen())

    def _on_status_change_cb(self, user_id: str, online: bool, last_seen) -> None:
        self.call_later(self._refresh_status_ui)

    def _refresh_status_ui(self) -> None:
        from tgm.screens.chat.screen import ChatScreen
        from tgm.widgets.channels.list import ChannelList

        for screen in self.screen_stack:
            if isinstance(screen, ChatScreen):
                try:
                    screen.query_one(ChannelList).refresh_previews()
                    screen._refresh_top_bar()
                except Exception:
                    pass
                break
