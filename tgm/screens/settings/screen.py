from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import cast

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Input,
    ListView,
    Select,
    Static,
)

from tgm.config.keybindings import get_binding_objects, load_bindings
from tgm.config.settings_store import load_telegram
from tgm.config.themes import ACCENT_THEMES
from tgm.core.app_context import AppContext
from tgm.core.models.channel import Channel, ChannelSettings
from tgm.screens._base import TgmScreen
from tgm.screens.settings.channel_item_settings import ChannelSettingsItem
from tgm.screens.settings.events import (
    ChannelSettingChanged,
    ChannelSettingsOpened,
    GlobalSettingChanged,
    KeybindingChanged,
    SectionSelected,
    TelegramCredentialsSave,
)
from tgm.screens.settings.key_capture import KeyCaptureScreen
from tgm.screens.settings.settings_section import SETTINGS_SECTIONS, SettingsSection

_SectionRenderer = Callable[[Static, VerticalScroll], Awaitable[None]]

_SECTION_LABELS: dict[str, str] = {
    "app": "App",
    "chat": "Chat",
    "login": "Login",
    "settings": "Settings",
}


class SettingsScreen(TgmScreen):
    BINDINGS = get_binding_objects("settings")

    _editing_channel_id: str | None = None

    @property
    def ctx(self) -> AppContext:
        return cast(AppContext, self.app)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="settings-sidebar"):
                yield Static("[bold white]  Settings[/]", id="settings-sidebar-header")
                yield ListView(id="settings-sections")
            with Vertical(id="settings-content-area"):
                yield Static(id="settings-content-header")
                yield VerticalScroll(id="settings-content")
        yield Footer()

    async def on_mount(self) -> None:
        sections = self.query_one("#settings-sections", ListView)
        for sid, label in SETTINGS_SECTIONS:
            sections.append(SettingsSection(sid, label))
        sections.index = 0
        await self._show_section("account")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if hasattr(item, "section_id"):
            self.post_message(SectionSelected(item.section_id))
        elif hasattr(item, "channel"):
            self.post_message(ChannelSettingsOpened(item.channel.id))

    async def on_section_selected(self, event: SectionSelected) -> None:
        event.stop()
        await self._show_section(event.section_id)

    async def on_channel_settings_opened(self, event: ChannelSettingsOpened) -> None:
        event.stop()
        await self._show_chat_settings(event.channel_id)

    def _section_renderers(self) -> dict[str, _SectionRenderer]:
        return {
            "account":       self._render_account,
            "general":       self._render_general,
            "appearance":    self._render_appearance,
            "input":         self._render_input,
            "chats":         self._render_chats,
            "notifications": self._render_notifications,
            "keybindings":   self._render_keybindings,
            "about":         self._render_about,
        }

    async def _show_section(self, section_id: str) -> None:
        header = self.query_one("#settings-content-header", Static)
        content = self.query_one("#settings-content", VerticalScroll)
        await content.remove_children()
        renderer = self._section_renderers().get(section_id)
        if renderer:
            await renderer(header, content)

    async def _render_account(self, header: Static, content: VerticalScroll) -> None:
        await self._show_account(header, content)

    async def _render_general(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]General[/]")
        await content.mount(
            Checkbox("Enter to send", id="enter_to_send", value=self.ctx.enter_to_send),
            Checkbox("Show timestamps", id="show_timestamps", value=self.ctx.show_timestamps),
        )

    async def _render_appearance(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]Appearance[/]")
        accents = [(name, name) for name in ACCENT_THEMES]
        await content.mount(
            Static("[dim]Accent color[/]", classes="settings-option-label"),
            Select(accents, id="accent_color", value=self.ctx.accent_theme),
            Static("[dim]Message density[/]", classes="settings-option-label"),
            Select(
                [("Comfortable", "comfortable"), ("Compact", "compact"), ("Cozy", "cozy")],
                id="message_density",
                value=self.ctx.message_density,
            ),
            Static("", classes="settings-spacer"),
            Static("[bold]Text[/]", classes="settings-option-label"),
            Checkbox("Wrap long messages", id="text_wrap", value=self.ctx.text_wrap),
            Static("[dim]Text opacity[/]", classes="settings-option-label"),
            Select(
                [("100%", 1.0), ("90%", 0.9), ("80%", 0.8), ("70%", 0.7)],
                id="text_opacity",
                value=self.ctx.text_opacity,
            ),
            Static("", classes="settings-spacer"),
            Static("[bold]Message borders[/]", classes="settings-option-label"),
            Select([("Off", 0), ("On", 1)], id="big_msg_threshold", value=self.ctx.big_msg_threshold),
            Static("[dim]Draw a frame around each message[/]", classes="settings-hint"),
        )

    async def _render_input(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]Input[/]")
        await content.mount(
            Static("[dim]Emoji autocomplete trigger[/]", classes="settings-option-label"),
            Select(
                [("colon ( : )", ":"), ("at ( @ )", "@"), ("hash ( # )", "#"), ("semicolon ( ; )", ";")],
                id="emoji_trigger",
                value=self.ctx.emoji_trigger,
            ),
            Static("[dim]Choose a character that opens emoji suggestions[/]", classes="settings-hint"),
            Static("", classes="settings-spacer"),
            Checkbox("Enter to send", id="enter_to_send", value=self.ctx.enter_to_send),
        )

    async def _render_chats(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]Chats[/]")
        await self._show_chat_list(content)

    async def _render_notifications(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]Notifications[/]")
        await content.mount(
            Checkbox("Enable notifications", id="notifications", value=self.ctx.notifications),
            Static("[dim]Get notified about new messages[/]", classes="settings-hint"),
        )

    async def _render_keybindings(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]Keybindings[/]")
        await self._show_keybindings(content)

    async def _render_about(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]About[/]")
        await content.mount(
            Static("[bold]CliTel[/]", classes="settings-about-name"),
            Static("[dim]Telegram-style TUI Chat[/]", classes="settings-about-version"),
            Static("[dim]v0.1.0[/]", classes="settings-about-version"),
            Static("", classes="settings-spacer"),
            Static("[dim]Built with Textual[/]", classes="settings-about-version"),
        )

    async def _show_account(self, header: Static, content: VerticalScroll) -> None:
        header.update("[bold white]Account[/]")
        tg = load_telegram()
        api_id_input = Input(value=tg["api_id"], placeholder="12345678", id="tg-api-id")
        api_hash_input = Input(
            value=tg["api_hash"],
            placeholder="abcdef1234567890abcdef1234567890",
            id="tg-api-hash",
            password=True,
        )
        save_btn = Button("Save credentials", id="tg-save-btn", variant="primary")
        save_btn.styles.margin = (1, 0, 0, 0)
        await content.mount(
            Static("[bold]Telegram API[/]", classes="settings-option-label"),
            Static("[dim]Get credentials at my.telegram.org[/]", classes="settings-hint"),
            Static("", classes="settings-spacer"),
            Static("[dim]API ID[/]", classes="settings-option-label"),
            api_id_input,
            Static("[dim]API Hash[/]", classes="settings-option-label"),
            api_hash_input,
            save_btn,
            Static(
                "[dim]Changes take effect after restart[/]",
                id="tg-save-status",
                classes="settings-hint",
            ),
        )

    def _save_telegram_credentials(self) -> None:
        try:
            api_id = self.query_one("#tg-api-id", Input).value.strip()
            api_hash = self.query_one("#tg-api-hash", Input).value.strip()
        except Exception:
            return

        status = self.query_one("#tg-save-status", Static)
        if not api_id or not api_hash:
            status.update("[red]Both fields are required[/]")
            return
        try:
            int(api_id)
        except ValueError:
            status.update("[red]API ID must be a number[/]")
            return

        self.post_message(TelegramCredentialsSave(api_id, api_hash))
        status.update("[green]Saved! Restart the app to apply.[/]")

    async def _show_keybindings(self, content: VerticalScroll) -> None:
        bindings = load_bindings()
        for section, items in bindings.items():
            section_label = _SECTION_LABELS.get(section, section)
            await content.mount(
                Static(f"[bold]{section_label}[/]", classes="settings-option-label")
            )
            for key, action, desc, show in items:
                if not show:
                    continue
                short = action.split(".")[-1]
                row = Horizontal(id=f"kb-{section}-{short}")
                name_s = Static(f"  {desc}")
                name_s.styles.width = 28
                key_s = Static(f"[dim]{key}[/]", id=f"kbkey-{section}-{short}")
                key_s.styles.width = 16
                btn = Button("Change", id=f"chg-{section}-{short}", classes="kb-change-btn")
                await content.mount(row)
                await row.mount(name_s, key_s, btn)
            await content.mount(Static("", classes="settings-spacer"))

    async def _show_chat_list(self, content: VerticalScroll) -> None:
        lv = ListView()
        await content.mount(lv)
        for channel in self.ctx.channels:
            await lv.mount(ChannelSettingsItem(channel))
        lv.focus()

    async def _show_chat_settings(self, channel_id: str) -> None:
        content = self.query_one("#settings-content", VerticalScroll)
        await content.remove_children()
        channel = self.ctx.get_channel(channel_id)
        if not channel:
            return
        self._editing_channel_id = channel_id
        settings = self.ctx.get_channel_settings(channel_id)
        header = self.query_one("#settings-content-header", Static)
        header.update(f"[bold white]# {channel.name}[/]")
        accents = [("Default", "")] + [(name, name) for name in ACCENT_THEMES]
        current = settings.color if settings.color in ACCENT_THEMES else ""
        await content.mount(
            Static("[dim]Channel settings[/]", classes="settings-option-label"),
            Checkbox("Muted", id="ch-muted", value=settings.muted),
            Checkbox("Notifications", id="ch-notify", value=settings.notify),
            Static("[dim]Color[/]", classes="settings-option-label"),
            Select(accents, id="ch-color", value=current),
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        if btn_id == "tg-save-btn":
            self._save_telegram_credentials()
            return

        if not btn_id.startswith("chg-"):
            return

        _, section, short = btn_id.split("-", 2)
        bindings = load_bindings()
        action_name = short
        for _, action, desc, *_ in bindings.get(section, []):
            if action.split(".")[-1] == short:
                action_name = desc
                break

        self.app.push_screen(KeyCaptureScreen(section, action_name, self._on_key_captured))

    def _on_key_captured(self, section: str, action_name: str, key: str) -> None:
        bindings = load_bindings()
        short = None
        for _, action, desc, *_ in bindings.get(section, []):
            if desc == action_name:
                short = action.split(".")[-1]
                break
        if not short:
            return

        self.post_message(KeybindingChanged(section, short, key))

        try:
            key_label = self.query_one(f"#kbkey-{section}-{short}", Static)
            key_label.update(f"[dim]{key}[/]")
        except Exception:
            pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        cid = event.checkbox.id or ""

        if cid == "ch-muted" and self._editing_channel_id:
            self.post_message(ChannelSettingChanged(self._editing_channel_id, "muted", event.value))
            return
        if cid == "ch-notify" and self._editing_channel_id:
            self.post_message(ChannelSettingChanged(self._editing_channel_id, "notify", event.value))
            return

        _GLOBAL_CHECKBOXES = {"show_timestamps", "enter_to_send", "notifications", "text_wrap"}
        if cid in _GLOBAL_CHECKBOXES:
            self.post_message(GlobalSettingChanged(cid, event.value))

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.is_blank():
            return
        sid = event.select.id or ""

        if sid == "ch-color" and self._editing_channel_id:
            self.post_message(ChannelSettingChanged(self._editing_channel_id, "color", event.value))
            return

        _GLOBAL_SELECTS = {
            "message_density",
            "accent_color",
            "emoji_trigger",
            "text_opacity",
            "big_msg_threshold",
        }
        if sid in _GLOBAL_SELECTS:
            key = "accent_theme" if sid == "accent_color" else sid
            self.post_message(GlobalSettingChanged(key, event.value))
