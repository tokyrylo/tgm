from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from tgm.screens.search.events import (
    ChannelChosen,
    GlobalSearchQuery,
    GlobalSearchResults,
)
from tgm.widgets.channels.events import ChannelSelected

if TYPE_CHECKING:
    from textual.app import App as _AppBase
    from tgm.core.models.channel import Channel
    from tgm.core.protocol import ClientProtocol
else:
    _AppBase = object


class _ChannelsMixin(_AppBase):
    client: ClientProtocol | None
    current_channel_id: str | None

    def on_channel_selected(self, event: ChannelSelected) -> None:
        event.stop()
        self.current_channel_id = event.channel_id
        self.load_messages(event.channel_id)

    def on_channel_chosen(self, event: ChannelChosen) -> None:
        event.stop()
        self.current_channel_id = event.channel_id
        self.load_messages(event.channel_id)

    def on_global_search_query(self, event: GlobalSearchQuery) -> None:
        event.stop()
        self.run_worker(self._do_search(event.query), exclusive=True, group="gs-search")

    async def _do_search(self, query: str) -> None:
        try:
            await asyncio.sleep(0.15)
        except asyncio.CancelledError:
            return
        query_stripped = query.strip()
        if not query_stripped or not self.client:
            self._post_search_results(query, [])
            return
        try:
            results = await self.client.search_global(query_stripped)
        except Exception:
            results = []
        self._post_search_results(query, results)

    def _post_search_results(self, query: str, results: list[Channel]) -> None:
        from tgm.screens.search.screen import GlobalSearchScreen

        for screen in self.screen_stack:
            if isinstance(screen, GlobalSearchScreen):
                screen.post_message(GlobalSearchResults(query, results))
                return

    def _refresh_channel_list(self) -> None:
        from tgm.screens.chat.events import RefreshChannelList
        from tgm.screens.chat.screen import ChatScreen

        for screen in self.screen_stack:
            if isinstance(screen, ChatScreen):
                screen.post_message(RefreshChannelList())
                return

    def _refresh_status_ui(self) -> None:
        from tgm.screens.chat.events import RefreshStatusUI
        from tgm.screens.chat.screen import ChatScreen

        for screen in self.screen_stack:
            if isinstance(screen, ChatScreen):
                screen.post_message(RefreshStatusUI())
                break
