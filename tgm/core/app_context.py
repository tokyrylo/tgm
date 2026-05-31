from __future__ import annotations

from typing import Protocol, Sequence

from tgm.core.models.channel import Channel, ChannelInfo, ChannelSettings
from tgm.core.models.user import User
from tgm.core.protocol import ClientProtocol


class AppContext(Protocol):
    client: ClientProtocol | None
    current_channel_id: str | None

    # store projections
    channels: Sequence[Channel]
    users: dict[str, User]
    current_user_id: str | None

    # display settings
    show_timestamps: bool
    accent_theme: str
    big_msg_threshold: int
    enter_to_send: bool
    emoji_trigger: str
    notifications: bool
    message_density: str
    text_wrap: bool
    text_opacity: float

    def get_channel(self, channel_id: str) -> Channel | None: ...
    async def get_channel_info(self, channel_id: str) -> ChannelInfo | None: ...
    def load_messages(self, channel_id: str | None) -> None: ...
    def send_file(self, file_path: str) -> None: ...
    def get_channel_settings(self, channel_id: str) -> ChannelSettings: ...
