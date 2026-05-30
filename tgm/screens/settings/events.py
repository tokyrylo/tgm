from __future__ import annotations

from typing import Any

from textual.message import Message


class SectionSelected(Message):
    def __init__(self, section_id: str) -> None:
        super().__init__()
        self.section_id = section_id


class ChannelSettingsOpened(Message):
    def __init__(self, channel_id: str) -> None:
        super().__init__()
        self.channel_id = channel_id


class GlobalSettingChanged(Message):
    def __init__(self, key: str, value: Any) -> None:
        super().__init__()
        self.key = key
        self.value = value


class ChannelSettingChanged(Message):
    def __init__(self, channel_id: str, key: str, value: Any) -> None:
        super().__init__()
        self.channel_id = channel_id
        self.key = key
        self.value = value


class KeybindingChanged(Message):
    def __init__(self, section: str, short: str, key: str) -> None:
        super().__init__()
        self.section = section
        self.short = short
        self.key = key


class TelegramCredentialsSave(Message):
    def __init__(self, api_id: str, api_hash: str) -> None:
        super().__init__()
        self.api_id = api_id
        self.api_hash = api_hash
