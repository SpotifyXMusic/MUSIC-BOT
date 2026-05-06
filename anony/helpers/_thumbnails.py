# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont)

from anony import config
from anony.helpers import Track


def _get_dominant_color(img: "Image.Image"):
    """
    Extract the dominant colour from an image.
    Skips near-black and near-white pixels so we get the
    most visually meaningful hue.
    """
    small = img.resize((100, 100)).convert("RGB")
    pixels = list(small.getdata())

    filtered = [
        (r, g, b) for r, g, b in pixels
        if not (r < 30 and g < 30 and b < 30)
        and not (r > 230 and g > 230 and b > 230)
    ]
    if not filtered:
        filtered = pixels

    r = sum(p[0] for p in filtered) // len(filtered)
    g = sum(p[1] for p in filtered) // len(filtered)
    b = sum(p[2] for p in filtered) // len(filtered)
    return (r, g, b)


def _lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class Thumbnail:
    def __init__(self):
        self.font_title   = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 48)
        self.font_channel = ImageFont.truetype("anony/helpers/Inter-Light.ttf",  30)
        self.font_time    = ImageFont.truetype("anony/helpers/Inter-Light.ttf",  26)
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with self.session.get(url) as resp:
            with open(output_path, "wb") as f:
                f.write(await resp.read())
        return output_path

    # ─────────────────────────────────────────────────────────────────────────
    # Internal drawing helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_skip_back(self, draw, x, y, size=40):
        """Draw a |<< (skip-back) button at (x, y)."""
        h = size
        W = (255, 255, 255, 255)
        draw.polygon([(x + size,      y),
                      (x + size // 2, y + h // 2),
                      (x + size,      y + h)], fill=W)
        draw.polygon([(x + size // 2, y),
                      (x,             y + h // 2),
                      (x + size // 2, y + h)], fill=W)
        draw.rounded_rectangle((x - 6, y, x, y + h), radius=2, fill=W)

    def _draw_skip_fwd(self, draw, x, y, size=40):
        """Draw a >>| (skip-forward) button at (x, y)."""
        h = size
        W = (255, 255, 255, 255)
        draw.polygon([(x,             y),
                      (x + size // 2, y + h // 2),
                      (x,             y + h)], fill=W)
        draw.polygon([(x + size // 2, y),
                      (x + size,      y + h // 2),
                      (x + size // 2, y + h)], fill=W)
        draw.rounded_rectangle((x + size, y, x + size + 6, y + h), radius=2, fill=W)

    # ─────────────────────────────────────────────────────────────────────────
    # Main generate
    # ─────────────────────────────────────────────────────────────────────────

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp   = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            W, H = 1280, 720
            art_src = Image.open(temp).convert("RGBA")

            # ── ADAPTIVE COLOUR ──────────────────────────────────────────────
            dominant = _get_dominant_color(art_src.convert("RGB"))

            # Background gradient: dark-tinted-dominant (left) → near-black (right)
            bg_left  = tuple(max(0, int(c * 0.35)) for c in dominant)
            bg_right = (10, 10, 15)

            # ── CANVAS ───────────────────────────────────────────────────────
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))

            pix = []
            for y in range(H):
                for x in range(W):
                    t = (x / W) ** 1.2
                    pix.append(_lerp(bg_left, bg_right, t) + (255,))
            canvas.putdata(pix)

            # Subtle blurred art overlay for depth
            bg_art = art_src.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")
            bg_art = bg_art.filter(ImageFilter.GaussianBlur(50))
            bg_art.putalpha(40)
            canvas.paste(bg_art, (0, 0), bg_art)

            # ── ALBUM ART ────────────────────────────────────────────────────
            art_size = 520
            art = art_src.resize((art_size, art_size), Image.Resampling.LANCZOS)

            mask = Image.new("L", (art_size, art_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, art_size, art_size), radius=20, fill=255
            )
            art.putalpha(mask)

            art_x = 60
            art_y = (H - art_size) // 2

            # Drop shadow
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for i in range(20, 0, -1):
                ImageDraw.Draw(shadow).rounded_rectangle(
                    (art_x - i, art_y + i,
                     art_x + art_size + i, art_y + art_size + i),
                    radius=20 + i, fill=(0, 0, 0, 8)
                )
            shadow = shadow.filter(ImageFilter.GaussianBlur(12))
            canvas.paste(shadow, (0, 0), shadow)
            canvas.paste(art, (art_x, art_y), art)

            draw = ImageDraw.Draw(canvas)

            # ── COLOURS ──────────────────────────────────────────────────────
            WHITE = (255, 255, 255, 255)
            LGRAY = (180, 180, 180, 255)
            DGRAY = (100, 100, 100, 180)

            rx    = art_x + art_size + 70
            RIGHT = W - 60

            title   = (song.title or "Unknown")[:44]
            channel = (song.channel_name or "")[:32]
            dur     = song.duration or "0:00"

            # Vertical centering
            ry = (H - (48 * 2 + 10 + 30 + 55 + 5 + 28 + 80 + 40)) // 2 - 10

            # Wrap title at ~22 chars
            if len(title) > 22:
                idx = title.rfind(" ", 0, 22)
                if idx == -1:
                    idx = 22
                title_disp = title[:idx] + "\n" + title[idx:].strip()
            else:
                title_disp = title

            draw.multiline_text((rx, ry), title_disp,
                                font=self.font_title, fill=WHITE, spacing=6)
            draw.text((rx, ry + 116), channel,
                      font=self.font_channel, fill=LGRAY)

            # ── PROGRESS BAR ─────────────────────────────────────────────────
            bar_y  = ry + 185
            bar_x1 = rx
            bar_x2 = RIGHT
            bar_h  = 5

            draw.rounded_rectangle(
                (bar_x1, bar_y, bar_x2, bar_y + bar_h),
                radius=3, fill=DGRAY
            )

            prog_end = bar_x1 + max(10, int((bar_x2 - bar_x1) * 0.005))
            draw.rounded_rectangle(
                (bar_x1, bar_y, prog_end, bar_y + bar_h),
                radius=3, fill=WHITE
            )

            kr = 9
            draw.ellipse(
                (prog_end - kr, bar_y - kr + bar_h // 2,
                 prog_end + kr, bar_y + kr + bar_h // 2),
                fill=WHITE
            )

            draw.text((bar_x1,      bar_y + 14), "0:01",
                      font=self.font_time, fill=LGRAY)
            draw.text((bar_x2 - 48, bar_y + 14), dur,
                      font=self.font_time, fill=LGRAY)

            # ── CONTROLS ─────────────────────────────────────────────────────
            ctrl_y = bar_y + 68
            cx     = (bar_x1 + bar_x2) // 2
            gap    = 105
            tri    = 40

            # Pause button – white circle with dark bars
            cr     = 38
            cy_ctr = ctrl_y + tri // 2
            draw.ellipse((cx - cr, cy_ctr - cr, cx + cr, cy_ctr + cr), fill=WHITE)
            bar_col = (15, 15, 25, 255)
            draw.rounded_rectangle(
                (cx - 14, cy_ctr - cr + 12, cx - 4, cy_ctr + cr - 12),
                radius=3, fill=bar_col
            )
            draw.rounded_rectangle(
                (cx + 4,  cy_ctr - cr + 12, cx + 14, cy_ctr + cr - 12),
                radius=3, fill=bar_col
            )

            # Skip buttons
            self._draw_skip_back(draw, cx - gap - tri, ctrl_y, tri)
            self._draw_skip_fwd(draw,  cx + gap,       ctrl_y, tri)

            # Shuffle icon (left of prev)
            sx, sy = cx - gap * 2 - 24, ctrl_y + 8
            sw = 26
            draw.line([(sx, sy), (sx + sw, sy + sw)],  fill=LGRAY, width=3)
            draw.line([(sx, sy + sw), (sx + sw, sy)],   fill=LGRAY, width=3)
            draw.polygon([(sx + sw - 2, sy - 5),
                          (sx + sw + 7, sy + 3),
                          (sx + sw + 2, sy + 9)],  fill=LGRAY)
            draw.polygon([(sx + sw - 2, sy + sw + 5),
                          (sx + sw + 7, sy + sw - 3),
                          (sx + sw + 2, sy + sw - 9)], fill=LGRAY)

            # Repeat icon (right of next)
            rep_x = cx + gap * 2 + tri + 14
            rep_y = ctrl_y + 6
            rw = 30
            draw.arc((rep_x, rep_y, rep_x + rw, rep_y + rw),
                     start=20, end=340, fill=LGRAY, width=3)
            draw.polygon(
                [(rep_x + rw - 4, rep_y + 2),
                 (rep_x + rw + 6, rep_y + 8),
                 (rep_x + rw + 6, rep_y - 4)],
                fill=LGRAY
            )

            # ── SAVE ─────────────────────────────────────────────────────────
            canvas.convert("RGB").save(output, quality=95)
            try:
                os.remove(temp)
            except Exception:
                pass
            return output

        except Exception:
            return config.DEFAULT_THUMB
