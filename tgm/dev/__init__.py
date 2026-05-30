from tgm.app import TgmApp
from tgm.dev.mock_client import MockClient
from tgm.screens.chat.screen import ChatScreen


class DevApp(TgmApp):
    def __init__(self) -> None:
        super().__init__()
        self._skip_login = True
        client = MockClient()
        self.client = client  # type: ignore[assignment]
        if client.channel_list:
            self.current_channel_id = client.channel_list[0].id

    def on_mount(self) -> None:
        self.push_screen(ChatScreen())


def run_mock() -> None:
    DevApp().run()
