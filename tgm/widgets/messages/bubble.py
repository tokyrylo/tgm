"""Pure rendering functions — no widget state, no self.app access."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from tgm.config.themes import PALETTE
from tgm.core.models.messages import Message
from tgm.core.models.user import User
from tgm.widgets.messages.renderer import format_text, format_text_highlighted

_REPLY_COLOR = PALETTE["reply"]
_READ_COLOR = PALETTE["read"]
_OTHER_BG = PALETTE["bg_surface"]
_CURSOR_BG = "#1e3a50"  # slightly brighter than bg_surface for selected other
_CURSOR_OWN_BG = "#3a6fa0"  # slightly brighter than accent for selected own

_MARKUP_RE = re.compile(r"\[/?[^\]]*\]")


def visible_len(text: str) -> int:
    """Length of text after removing Rich markup tags and unescaping [[."""
    return len(_MARKUP_RE.sub("", text).replace("[[", "["))


@dataclass
class Bubble:
    lines: list[str]
    msg_id: str
    kind: Literal["own", "other", "media"]

    @property
    def height(self) -> int:
        return len(self.lines)


@dataclass(frozen=True)
class RenderContext:
    width: int
    accent: str
    show_ts: bool
    large: bool


def wrap_frame(
    lines: list[str], border_col: str, width: int, *, bright: bool = False
) -> list[str]:
    bar = "─" * max(0, width - 2)
    style = f"bold {border_col}" if bright else f"dim {border_col}"
    return [f"[{style}]╭{bar}╮[/]"] + lines + [f"[{style}]╰{bar}╯[/]"]


def render_date_sep(dt, width: int) -> str:
    today = date.today()
    if dt.date() == today:
        label = "Today"
    elif dt.date() == today - timedelta(days=1):
        label = "Yesterday"
    else:
        label = dt.strftime("%B %d, %Y")
    raw = f" ─── {label} ─── "
    pad = max(0, (width - len(raw)) // 2)
    return f"[dim white]{' ' * pad}{raw}[/]"


_photo_cache: dict[tuple[str, int], list[str]] = {}
_gallery_cache: dict[tuple[str | int, ...], list[str]] = {}


def render_photo(media_path: str, cols: int) -> list[str]:
    key = (media_path, cols)
    if key in _photo_cache:
        return _photo_cache[key]
    from tgm.media.avatar import avatar_markup

    markup = avatar_markup(Path(media_path), cols, cols)
    result = [markup] if markup else []
    _photo_cache[key] = result
    return result


def render_gallery(paths: list[str], width: int) -> list[str]:
    key = (*paths, width)
    if key in _gallery_cache:
        return _gallery_cache[key]

    if len(paths) == 1:
        result = render_photo(paths[0], min(40, width - 2))
        _gallery_cache[key] = result
        return result

    from tgm.media.avatar import _downsample, render_halfblock

    gap = 1
    main_cols = min(26, width * 2 // 3)
    remaining = width - main_cols - gap
    thumb_cols = min(8, remaining // 2)
    if thumb_cols < 3:
        result = render_photo(paths[0], min(40, width - 2))
        _gallery_cache[key] = result
        return result

    n_thumbs = len(paths) - 1
    thumb_grid_rows = (n_thumbs + 1) // 2
    main_rows = min(16, main_cols)
    thumb_rows = thumb_cols

    try:
        from PIL import Image

        main_px = _downsample(Image.open(Path(paths[0])), main_cols, main_rows)
        main_lines = render_halfblock(main_px).split("\n")
    except Exception:
        main_lines = [" " * main_cols] * main_rows

    thumbs: list[list[str]] = []
    for p in paths[1:]:
        try:
            from PIL import Image

            px = _downsample(Image.open(Path(p)), thumb_cols, thumb_rows)
            thumbs.append(render_halfblock(px).split("\n"))
        except Exception:
            thumbs.append([" " * thumb_cols] * thumb_rows)

    right_lines: list[str] = []
    for r in range(thumb_grid_rows):
        r1 = thumbs[r * 2] if r * 2 < n_thumbs else [" " * thumb_cols] * thumb_rows
        r2 = (
            thumbs[r * 2 + 1]
            if r * 2 + 1 < n_thumbs
            else [" " * thumb_cols] * thumb_rows
        )
        for t in range(thumb_rows):
            c1 = r1[t] if t < len(r1) else " " * thumb_cols
            c2 = r2[t] if t < len(r2) else " " * thumb_cols
            right_lines.append(f"{c1}  {c2}")

    max_r = max(len(main_lines), len(right_lines))
    result = [
        f"{main_lines[i] if i < len(main_lines) else ' ' * main_cols}"
        f"{' ' * gap}"
        f"{right_lines[i] if i < len(right_lines) else ' ' * (2 * thumb_cols + 2)}"
        for i in range(max_r)
    ]
    _gallery_cache[key] = result
    return result


def render_reply_quote(reply_to_id: str, msgs_by_id: dict[str, Message]) -> str | None:
    orig = msgs_by_id.get(reply_to_id)
    if not orig:
        return None
    sender = orig.username or "?"
    preview = (
        (orig.text[:60] if orig.text else "[Photo]")
        .replace("[", "[[")
        .replace("]", "]]")
    )
    return f"[dim {_REPLY_COLOR}]▎[/] [dim {_REPLY_COLOR}]{sender}[/] [dim white]{preview}[/]"


_bubble_cache: dict[tuple[str, int, str | None], Bubble] = {}


def _bubble_cache_key(msg: Message, ctx: RenderContext) -> tuple[str, int, str | None]:
    # include read status and text in key so edits/reads invalidate the cache
    return (f"{msg.id}:{msg.text}:{msg.read}", hash(ctx), msg.reply_to_msg_id)


def invalidate_bubble(msg_id: str) -> None:
    """Remove all cached bubbles for a given message ID."""
    for key in [k for k in _bubble_cache if k[0].startswith(f"{msg_id}:")]:
        del _bubble_cache[key]


def render_bubble(
    msg: Message,
    *,
    ctx: RenderContext,
    is_own: bool,
    user: User | None,
    msgs_by_id: dict[str, Message],
    highlight_query: str = "",
    is_cursor: bool = False,
) -> Bubble:
    cache_key = _bubble_cache_key(msg, ctx)
    if not highlight_query and not is_cursor and cache_key in _bubble_cache:
        return _bubble_cache[cache_key]

    ts = msg.timestamp.strftime("%H:%M")
    text = (
        format_text_highlighted(msg.text, highlight_query)
        if highlight_query and msg.text
        else (format_text(msg.text) if msg.text else "")
    )
    has_photo_type = "photo" in (msg.media_types or [])
    media_paths: list[str] = msg.media_paths or []
    has_media = bool(media_paths) and has_photo_type
    is_loading_photo = has_photo_type and not has_media
    is_gallery = has_media and len(media_paths) > 1
    border_col = (
        ctx.accent
        if is_own
        else (user.color if user and user.color != "text" else "text")
    )

    content: list[str] = []

    if is_loading_photo:
        content.append("[dim white]📷 Photo[/]")
    elif has_media:
        content.extend(
            render_gallery(media_paths, ctx.width)
            if is_gallery
            else render_photo(media_paths[0], min(40, ctx.width - 2))
        )

    if msg.reply_to_msg_id:
        quote = render_reply_quote(msg.reply_to_msg_id, msgs_by_id)
        if quote:
            content.append(quote)

    # media-only message (includes loading placeholder)
    if not msg.text and (has_media or is_loading_photo):
        lines = (
            wrap_frame(content, border_col, ctx.width, bright=is_cursor)
            if ctx.large
            else content
        )
        bubble = Bubble(lines=lines, msg_id=msg.id, kind="media")
        if not is_cursor:
            _bubble_cache[cache_key] = bubble
        return bubble

    if is_own:
        read_styled = f"[{_READ_COLOR}]✓✓[/]" if msg.read else "[dim white]✓[/]"
        ts_plain = f"  {ts}" if ctx.show_ts else ""
        ts_styled = f"  [dim white]{ts}[/]" if ctx.show_ts else ""
        raw_read = "✓✓" if msg.read else "✓"
        raw_vis = f"You: {msg.text or ''} {raw_read}{ts_plain}"
        left_pad = max(0, ctx.width - visible_len(raw_vis) - 2)
        own_bg = _CURSOR_OWN_BG if is_cursor else ctx.accent
        content.append(
            f"[white on {own_bg}]{' ' * left_pad} "
            f"[bold white]You[/]: {text} {read_styled}{ts_styled}[/]"
        )
        kind: Literal["own", "other", "media"] = "own"
    else:
        color = user.color if user and user.color != "text" else "text"
        initial = msg.username[0].upper() if msg.username else "?"
        safe_name = (msg.username or "?").replace("[", "[[")
        unread_dot = " [bold #0D9488]●[/]" if not msg.read else ""
        other_bg = _CURSOR_BG if is_cursor else _OTHER_BG
        if ctx.show_ts:
            plain = f" {initial}  {msg.username or ''}: {msg.text or ''}"
            pad = max(0, ctx.width - visible_len(plain) - len(f"  {ts}") - 3)
            ts_styled = f"{' ' * pad}  [dim white]{ts}[/]"
        else:
            ts_styled = ""
        content.append(
            f"[white on {other_bg}] [white on {color}] {initial} [/]  "
            f"{safe_name}: {text}{ts_styled}{unread_dot}[/]"
        )
        kind = "other"

    lines = (
        wrap_frame(content, border_col, ctx.width, bright=is_cursor)
        if ctx.large
        else content
    )
    bubble = Bubble(lines=lines, msg_id=msg.id, kind=kind)
    if not is_cursor:
        _bubble_cache[cache_key] = bubble
    return bubble
