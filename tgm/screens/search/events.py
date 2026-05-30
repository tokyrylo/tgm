from __future__ import annotations

from textual.message import Message

from tgm.core.models.channel import Channel


class SearchEvent(Message):
    NAMESPACE = "global_search"


class ChannelChosen(SearchEvent):
    def __init__(self, channel_id: str) -> None:
        super().__init__()
        self.channel_id = channel_id


class GlobalSearchQuery(SearchEvent):
    def __init__(self, query: str) -> None:
        super().__init__()
        self.query = query


class GlobalSearchResults(SearchEvent):
    def __init__(self, query: str, results: list[Channel]) -> None:
        super().__init__()
        self.query = query
        self.results = results
