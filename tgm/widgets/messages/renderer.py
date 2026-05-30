import re

from tgm.widgets.messages.markdown import to_textual as md_to_textual

_URL_RE = re.compile(r'https?://[^\s<>"\'(){}|\\^`\[\]]+')
_LINK_TAG = re.compile(r"(\[link=[^\]]+\].*?\[/\])", re.DOTALL)

# Sentinels survive linkify/markdown processing (no brackets, no markdown chars)
_HL_START = "\x00HS\x00"
_HL_END = "\x00HE\x00"


def linkify(text: str) -> str:
    parts = []
    last = 0
    for m in _URL_RE.finditer(text):
        start, end = m.start(), m.end()
        parts.append(text[last:start].replace("[", "[["))
        url = m.group(0)
        display = url.replace("[", "[[").replace("]", "]]")
        escaped = url.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f"[link={url} @click='open_url(\"{escaped}\")']{display}[/]")
        last = end
    parts.append(text[last:].replace("[", "[["))
    return "".join(parts)


def format_text(text: str) -> str:
    text = linkify(text)
    parts = _LINK_TAG.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = md_to_textual(parts[i])
    return "".join(parts)


def format_text_highlighted(text: str, query: str) -> str:
    """format_text with case-insensitive query highlighted in yellow."""
    marked = re.sub(
        re.escape(query),
        lambda m: f"{_HL_START}{m.group(0)}{_HL_END}",
        text,
        flags=re.IGNORECASE,
    )
    result = format_text(marked)
    result = result.replace(_HL_START, "[bold black on yellow]")
    result = result.replace(_HL_END, "[/]")
    return result
