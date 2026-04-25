# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from anony import config
from anony.helpers import Track


class Thumbnail:
    def __init__(self):
        self.font_title  = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf",  42)
        self.font_label  = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf",  28)
        self.font_sub    = ImageFont.truetype("anony/helpers/Inter-Light.ttf",   30)
        self.font_small  = ImageFont.truetype("anony/helpers/Inter-Light.ttf",   26)
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

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp   = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            W, H = 1280, 720

            # ── Dark navy background ──────────────────────────────────────────
            image = Image.new("RGBA", (W, H), (10, 15, 40, 255))

            # ── Album art (left side, square with rounded corners) ────────────
            art_size = 420
            art = Image.open(temp).convert("RGBA").resize(
                (art_size, art_size), Image.Resampling.LANCZOS
            )
            # Rounded-corner mask
            mask = Image.new("L", (art_size, art_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, art_size, art_size), radius=22, fill=255
            )
            art.putalpha(mask)
            art_x = 70
            art_y = (H - art_size) // 2
            image.paste(art, (art_x, art_y), art)

            draw = ImageDraw.Draw(image)

            # ── Right side content ────────────────────────────────────────────
            rx = art_x + art_size + 60   # content left edge
            ry = 145                      # content top

            # "| Started streaming" label
            draw.text(
                (rx, ry),
                "| Started streaming",
                font=self.font_sub,
                fill=(100, 200, 255),
            )

            # Thin separator line
            draw.line(
                [(rx, ry + 48), (W - 55, ry + 48)],
                fill=(35, 55, 110),
                width=2,
            )

            # Song title (max 28 chars to fit)
            title = song.title[:28] if song.title else "Unknown"
            draw.text(
                (rx, ry + 62),
                title,
                font=self.font_title,
                fill=(255, 255, 255),
            )

            # Duration row
            draw.text((rx, ry + 140), "⏱ Duration:", font=self.font_label, fill=(180, 180, 220))
            draw.text((rx + 210, ry + 140), f"{song.duration} min", font=self.font_sub, fill=(255, 255, 255))

            # Requested by row
            user = str(song.user) if song.user else "Unknown"
            draw.text((rx, ry + 198), "👤 Requested by:", font=self.font_label, fill=(180, 180, 220))
            draw.text((rx + 260, ry + 198), user[:22], font=self.font_sub, fill=(100, 200, 255))

            # ── Progress bar (bottom right area) ─────────────────────────────
            bar_y  = H - 108
            bar_x1 = rx
            bar_x2 = W - 55

            # Track (background)
            draw.rounded_rectangle(
                (bar_x1, bar_y, bar_x2, bar_y + 8),
                radius=4,
                fill=(45, 60, 100),
            )
            # Progress fill (~5% played — "just started")
            prog_end = bar_x1 + int((bar_x2 - bar_x1) * 0.05)
            draw.rounded_rectangle(
                (bar_x1, bar_y, prog_end, bar_y + 8),
                radius=4,
                fill=(100, 180, 255),
            )
            # Dot at progress position
            draw.ellipse(
                (prog_end - 9, bar_y - 7, prog_end + 9, bar_y + 15),
                fill=(255, 255, 255),
            )

            # Time labels
            draw.text((bar_x1, bar_y + 18), "0:01", font=self.font_small, fill=(190, 195, 220))
            draw.text((bar_x2 - 65, bar_y + 18), song.duration, font=self.font_small, fill=(190, 195, 220))

            image.convert("RGB").save(output, quality=95)
            try:
                os.remove(temp)
            except Exception:
                pass
            return output

        except Exception:
            return config.DEFAULT_THUMB
