from __future__ import annotations

from typing import TYPE_CHECKING

from tgm.config.keybindings import reload as _reload_bindings
from tgm.config.keybindings import save_binding as _save_binding
from tgm.config.settings_store import save_channel_settings as _save_channel_settings
from tgm.config.settings_store import save_global as _save_global
from tgm.config.settings_store import save_telegram as _save_telegram
from tgm.core.models.channel import ChannelSettings
from tgm.screens.settings.events import (
    ChannelSettingChanged,
    GlobalSettingChanged,
    KeybindingChanged,
    TelegramCredentialsSave,
)

if TYPE_CHECKING:
    from textual.app import App as _AppBase
else:
    _AppBase = object


class _SettingsMixin(_AppBase):
    _channel_settings: dict[str, ChannelSettings]
    current_channel_id: str | None

    def save_global_settings(self, **kwargs: object) -> None:
        _save_global(**kwargs)

    def get_channel_settings(self, channel_id: str) -> ChannelSettings:
        return self._channel_settings.get(channel_id, ChannelSettings())

    def update_channel_settings(self, channel_id: str, **kwargs: object) -> None:
        settings = self._channel_settings.setdefault(channel_id, ChannelSettings())
        for k, v in kwargs.items():
            setattr(settings, k, v)
        _save_channel_settings(channel_id, **kwargs)

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
