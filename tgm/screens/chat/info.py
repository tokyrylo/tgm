from __future__ import annotations

from typing import Protocol, cast

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Static

from tgm.core.models.channel import ChannelInfo
from tgm.core.models.user import format_last_seen
from tgm.core.protocol import ClientProtocol
from tgm.screens._base import TgmModalScreen


class AppContext(Protocol):
    client: ClientProtocol


class ChannelInfoModal(TgmModalScreen[None]):
    def __init__(self, channel_id: str) -> None:
        super().__init__()
        self._channel_id = channel_id

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    def compose(self) -> ComposeResult:
        with Vertical(id="ci-container"):
            yield Static("", id="ci-avatar")
            yield Static("", id="ci-name")
            yield Static("", id="ci-subtitle")
            yield VerticalScroll(id="ci-body")
            yield Button("Close", id="ci-close", variant="default")

    async def on_mount(self) -> None:
        self.run_worker(self._load(), exclusive=True)

    async def _load(self) -> None:
        info = await self.ctx.client.get_channel_info(self._channel_id)
        await self._display_info(info)

    async def _display_info(self, info: ChannelInfo) -> None:
        ch = info.channel
        initial = ch.name[0].upper()

        self.query_one("#ci-avatar", Static).update(
            f"[bold white on #2B5278]  {initial}  [/]"
        )

        if info.is_dm and info.user:
            u = info.user
            self.query_one("#ci-name", Static).update(f"[bold white]{u.name}[/]")
            handle = f"@{u.username}" if u.username else ""
            self.query_one("#ci-subtitle", Static).update(f"[dim]{handle}[/]")
            status = format_last_seen(u)
            status_color = "green" if u.online else "dim white"
            await self._mount_info_rows([
                ("Status", f"[{status_color}]{status}[/]"),
                ("Phone",  u.phone or "—"),
                ("Bio",    u.bio   or "—"),
            ])
        else:
            self.query_one("#ci-name", Static).update(f"[bold white]{ch.name}[/]")
            count = info.members_count
            self.query_one("#ci-subtitle", Static).update(
                f"[dim]Group · {count} member{'s' if count != 1 else ''}[/]"
            )
            rows: list[tuple[str, str]] = []
            if ch.topic:
                rows.append(("Description", ch.topic))
            if info.members:
                names = ", ".join(m.name for m in info.members)
                rows.append(("Members", names))
            await self._mount_info_rows(rows)

    async def _mount_info_rows(self, rows: list[tuple[str, str]]) -> None:
        body = self.query_one("#ci-body", VerticalScroll)
        for label, value in rows:
            await body.mount(
                Static(f"[dim]{label}[/]", classes="ci-label"),
                Static(value, classes="ci-value"),
                Static("", classes="ci-spacer"),
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ci-close":
            self.dismiss()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss()
