"""
Thumbnail Generator
Creates beautiful "Now Playing" cards using Pillow
No external API needed - works fully offline
"""

import os
import io
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ASSETS_DIR = "assets"
THUMB_DIR = "downloads/thumbs"
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

# Colors matching the bot theme
COLORS = {
    "bg_dark":    (13, 17, 23),
    "card":       (22, 27, 34),
    "blue":       (29, 155, 240),
    "red":        (180, 70, 70),
    "white":      (255, 255, 255),
    "gray":       (139, 148, 158),
    "light_gray": (201, 209, 217),
    "green":      (63, 185, 80),
    "overlay":    (0, 0, 0, 160),
}

W, H = 800, 300  # card size


def _load_font(size: int, bold: bool = False):
    """Try system fonts, fallback to default"""
    font_paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVu{'Sans-Bold' if bold else 'Sans'}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _make_progress_bar(current_pct: float, width: int = 420, height: int = 6) -> Image.Image:
    bar = Image.new("RGBA", (width, height), (50, 60, 70, 255))
    draw = ImageDraw.Draw(bar)
    filled = int(width * current_pct)
    if filled > 0:
        draw.rectangle([0, 0, filled, height], fill=COLORS["blue"])
    # Circle at current position
    cx = max(6, min(filled, width - 6))
    draw.ellipse([cx - 6, -3, cx + 6, height + 3], fill=COLORS["blue"])
    return bar


async def _download_thumb(url: str, path: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(path, "wb") as f:
                        f.write(data)
                    return True
    except Exception:
        pass
    return False


def _create_default_bg() -> Image.Image:
    """Create gradient background when no thumbnail"""
    img = Image.new("RGB", (W, H), COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)
    # Simple gradient effect
    for i in range(H):
        alpha = int(255 * (1 - i / H) * 0.3)
        draw.line([(0, i), (W, i)], fill=(29, 155, 240, alpha))
    return img


async def generate_now_playing_thumb(
    title: str,
    channel: str,
    duration: str,
    requested_by: str,
    thumbnail_url: str = "",
    current_pct: float = 0.0,
    is_paused: bool = False,
    queue_pos: int = 0,
    total_queue: int = 0,
    mode: str = "AUDIO",
) -> str:
    """
    Generate Now Playing thumbnail card.
    Returns file path of generated image.
    """

    out_path = os.path.join(THUMB_DIR, f"np_{hash(title)}.png")

    def _generate():
        # ── Background ──────────────────────────────────────────────
        card = Image.new("RGB", (W, H), COLORS["card"])
        draw = ImageDraw.Draw(card, "RGBA")

        # Left side thumbnail
        thumb_size = (H, H)  # 300x300 square
        thumb_placed = False

        if thumbnail_url:
            thumb_path = os.path.join(THUMB_DIR, f"raw_{hash(thumbnail_url)}.jpg")
            if os.path.exists(thumb_path):
                try:
                    th = Image.open(thumb_path).convert("RGB")
                    th = th.resize(thumb_size, Image.LANCZOS)
                    # Darken left side
                    enhancer = ImageEnhance.Brightness(th)
                    th = enhancer.enhance(0.6)
                    card.paste(th, (0, 0))
                    # Gradient overlay on thumbnail
                    gradient = Image.new("RGBA", thumb_size, (0, 0, 0, 0))
                    gd = ImageDraw.Draw(gradient)
                    for x in range(thumb_size[0]):
                        alpha = int(255 * (x / thumb_size[0]) * 0.8)
                        gd.line([(x, 0), (x, thumb_size[1])], fill=(22, 27, 34, alpha))
                    card.paste(gradient, (0, 0), gradient)
                    thumb_placed = True
                except Exception:
                    pass

        if not thumb_placed:
            # Music note placeholder
            draw.rectangle([0, 0, H, H], fill=(30, 40, 55))
            fn = _load_font(80)
            draw.text((H // 2, H // 2), "♪", font=fn, fill=COLORS["blue"], anchor="mm")

        # ── Right panel ─────────────────────────────────────────────
        px = H + 20  # text start x
        tw = W - px - 20  # text area width

        # Mode badge (AUDIO / VIDEO)
        mode_color = COLORS["blue"] if mode == "AUDIO" else COLORS["red"]
        badge_w = 70
        draw.rounded_rectangle([px, 18, px + badge_w, 40], radius=10, fill=mode_color)
        mf = _load_font(13, bold=True)
        draw.text((px + badge_w // 2, 29), mode, font=mf, fill=COLORS["white"], anchor="mm")

        # Status badge
        status_txt = "⏸ PAUSED" if is_paused else "▶ PLAYING"
        status_col = (100, 100, 100) if is_paused else COLORS["green"]
        sx = px + badge_w + 10
        draw.rounded_rectangle([sx, 18, sx + 95, 40], radius=10, fill=status_col)
        draw.text((sx + 47, 29), status_txt, font=mf, fill=COLORS["white"], anchor="mm")

        # Title
        title_font = _load_font(22, bold=True)
        title_short = title[:38] + "…" if len(title) > 38 else title
        draw.text((px, 55), title_short, font=title_font, fill=COLORS["white"])

        # Channel
        ch_font = _load_font(15)
        draw.text((px, 86), channel[:45], font=ch_font, fill=COLORS["gray"])

        # Divider line
        draw.line([(px, 112), (W - 20, 112)], fill=(50, 60, 70), width=1)

        # Progress bar
        bar = _make_progress_bar(current_pct, width=tw)
        card.paste(bar, (px, 125), bar)

        # Time labels
        tf = _load_font(13)
        elapsed_s = int(current_pct * _duration_to_seconds(duration))
        elapsed = f"{elapsed_s // 60}:{elapsed_s % 60:02d}"
        draw.text((px, 138), elapsed, font=tf, fill=COLORS["gray"])
        draw.text((px + tw, 138), duration, font=tf, fill=COLORS["gray"], anchor="ra")

        # Requested by
        draw.text((px, 168), f"Requested by: {requested_by[:25]}", font=tf, fill=COLORS["gray"])

        # Queue info
        if total_queue > 0:
            draw.text(
                (px + tw, 168),
                f"Queue: {queue_pos}/{total_queue}",
                font=tf, fill=COLORS["blue"], anchor="ra"
            )

        # Bottom decorative bar
        draw.rectangle([0, H - 4, int(W * current_pct), H], fill=COLORS["blue"])

        return card

    # Download thumbnail in background
    if thumbnail_url:
        thumb_path = os.path.join(THUMB_DIR, f"raw_{hash(thumbnail_url)}.jpg")
        if not os.path.exists(thumb_path):
            await _download_thumb(thumbnail_url, thumb_path)

    card = await asyncio.get_event_loop().run_in_executor(None, _generate)
    card.save(out_path, "PNG", quality=95)
    return out_path


def _duration_to_seconds(duration: str) -> int:
    try:
        parts = duration.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except Exception:
        pass
    return 300


def make_progress_text(current_s: int, total_s: int, width: int = 20) -> str:
    """Make ASCII progress bar for text messages"""
    if total_s == 0:
        return "━" * width
    pct = min(current_s / total_s, 1.0)
    filled = int(width * pct)
    bar = "█" * filled + "─" * (width - filled)
    elapsed = f"{current_s // 60}:{current_s % 60:02d}"
    total = f"{total_s // 60}:{total_s % 60:02d}"
    return f"`{elapsed}` {bar} `{total}`"
