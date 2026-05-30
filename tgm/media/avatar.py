from pathlib import Path

from PIL import Image

from tgm.config import CHANNEL_COLORS, PALETTE
from tgm.config.dirs import AVATAR_DIR


def _fallback_color(uid: str) -> str:
    return CHANNEL_COLORS[hash(uid) % len(CHANNEL_COLORS)]


def color_from_avatar(user_id: str) -> str:
    try:
        cache_path = AVATAR_DIR / f"{user_id}.jpg"
        if not cache_path.exists():
            return _fallback_color(user_id)
        img = Image.open(cache_path).resize((1, 1))
        r, g, b = img.getpixel((0, 0))[:3]  # type: ignore[index]
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return _fallback_color(user_id)


def _downsample(
    img: Image.Image, cols: int, rows: int
) -> list[list[tuple[int, int, int]]]:
    img = img.convert("RGB").resize((cols, rows), Image.LANCZOS)  # type: ignore[attr-defined]
    pixels = []
    for y in range(rows):
        row = []
        for x in range(cols):
            row.append(img.getpixel((x, y)))  # type: ignore[arg-type]
        pixels.append(row)
    return pixels  # type: ignore[return-value]


def render_halfblock(
    pixels: list[list[tuple[int, int, int]]], bg: str = PALETTE["bg_avatar"]
) -> str:
    lines = []
    h = len(pixels)
    cols = len(pixels[0]) if pixels else 0
    for y in range(0, h, 2):
        line = ""
        for x in range(cols):
            tr, tg, tb = pixels[y][x]
            if y + 1 < h:
                br, bgc, bb = pixels[y + 1][x]
                line += f"[#{tr:02x}{tg:02x}{tb:02x} on #{br:02x}{bgc:02x}{bb:02x}]▀[/]"
            else:
                line += f"[on #{tr:02x}{tg:02x}{tb:02x}] [/]"
        lines.append(line)
    return "\n".join(lines)


def avatar_markup(path: Path, cols: int = 6, rows: int = 4) -> str | None:
    if not path.exists():
        return None
    try:
        pixels = _downsample(Image.open(path), cols, rows)
        return render_halfblock(pixels)
    except Exception:
        return None


def get_cached_avatar(entity_id: str) -> Path | None:
    for ext in ("jpg", "png", "jpeg", "webp"):
        p = AVATAR_DIR / f"{entity_id}.{ext}"
        if p.exists():
            return p
    return None


def placeholder_avatar_markup(hex_color: str, cols: int = 6, rows: int = 4) -> str:
    bg = hex_color.lstrip("#")
    r, g, b = int(bg[:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    pixels = [[(r, g, b) for _ in range(cols)] for _ in range(rows)]
    fg = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
    radius = min(cols, rows) // 2
    cx, cy = cols // 2, rows // 2
    for y in range(rows):
        for x in range(cols):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
                pixels[y][x] = fg
    return render_halfblock(pixels)
