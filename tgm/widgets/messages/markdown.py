import re

from tgm.config.themes import PALETTE

_CODE_BLOCK = re.compile(r"```(.+?)```", re.DOTALL)
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*(.+?)\*")
_ITALIC = re.compile(r"\b_(.+?)_\b")
_STRIKE = re.compile(r"~~(.+?)~~")

_CODE_STYLE = f"{PALETTE['fg_code']} on {PALETTE['bg_code']}"
_INLINE_REPL = f"[{_CODE_STYLE}]\\1[/]"


def to_textual(text: str) -> str:
    text = _CODE_BLOCK.sub(_code_block_repl, text)
    text = _INLINE_CODE.sub(_INLINE_REPL, text)
    text = _STRIKE.sub(r"[strike]\1[/]", text)
    text = _BOLD.sub(r"[bold]\1[/]", text)
    text = _ITALIC.sub(r"[italic]\1[/]", text)
    return text


def _code_block_repl(m: re.Match) -> str:
    content = m.group(1).strip("\n")
    lines = content.split("\n")
    styled = "\n".join(f"[dim {_CODE_STYLE}]  {line}[/]" for line in lines)
    return "\n" + styled + "\n"
