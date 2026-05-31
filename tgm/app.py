from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App

from tgm.config.keybindings import get_binding_objects
from tgm.config.settings_store import load_channel_settings as _load_channel_settings
from tgm.config.settings_store import load_global as _load_global
from tgm.controllers import _AuthMixin, _ChannelsMixin, _MessagingMixin, _SettingsMixin
from tgm.core import ClientProtocol
from tgm.core.models.channel import ChannelSettings

if TYPE_CHECKING:
    from tgm.core.models.channel import Channel
    from tgm.core.models.user import User


_STYLE = Path(__file__).parent / "static" / "styles" / "style.tcss"


class TgmApp(_AuthMixin, _MessagingMixin, _ChannelsMixin, _SettingsMixin, App):

    CSS_PATH = _STYLE
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = get_binding_objects("app")

    def __init__(self) -> None:
        super().__init__()
        self.client: ClientProtocol | None = None
        self.current_channel_id: str | None = None
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

    @property
    def users(self) -> dict[str, User]:
        return self.client.users if self.client else {}

    @property
    def current_user_id(self) -> str | None:
        return self.client.current_user_id if self.client else None

    def get_channel(self, channel_id: str) -> Channel | None:
        return self.client.channels.get(channel_id) if self.client else None

    async def get_channel_info(self, channel_id: str):
        if not self.client:
            return None
        return await self.client.get_channel_info(channel_id)
