from textual.app import ComposeResult
from textual.widgets import ListItem, Static

from tgm.config.themes import CHANNEL_COLORS


class ChannelSettingsItem(ListItem):
    def __init__(self, channel, **kwargs):
        super().__init__(id=f"ch-settings-{channel.id}", **kwargs)
        self.channel = channel

    def compose(self) -> ComposeResult:
        color = CHANNEL_COLORS[hash(self.channel.id) % len(CHANNEL_COLORS)]
        initial = self.channel.name[0].upper()
        yield Static(f"[{color} on {color}] {initial} [/]", classes="channel-initial")
