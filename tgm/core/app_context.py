from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Sequence

from tgm.core.models.channel import Channel, ChannelInfo, ChannelSettings
from tgm.core.models.user import User

if TYPE_CHECKING:
    from tgm.core.protocol import ClientProtocol


class DisplaySettings(Protocol):
    accent_theme: str
    show_timestamps: bool
    big_msg_threshold: int
    message_density: str
    text_wrap: bool
    text_opacity: float


class InputSettings(Protocol):
    emoji_trigger: str
    enter_to_send: bool


class ChannelContext(Protocol):
    channels: Sequence[Channel]
    current_channel_id: str | None
    users: dict[str, User]
    current_user_id: str | None

    def get_channel(self, channel_id: str) -> Channel | None: ...


class AppActions(Protocol):
    def load_messages(self, channel_id: str | None) -> None: ...
    def send_file(self, file_path: str) -> None: ...
    def get_channel_settings(self, channel_id: str) -> ChannelSettings: ...
    async def get_channel_info(self, channel_id: str) -> ChannelInfo | None: ...


class AppContext(DisplaySettings, InputSettings, ChannelContext, AppActions, Protocol):
    client: ClientProtocol | None
    notifications: bool
