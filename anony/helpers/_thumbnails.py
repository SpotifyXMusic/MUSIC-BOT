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
        self.font_title   = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf",  50)
        self.font_channel = ImageFont.truetype("anony/helpers/Inter-Light.ttf",   32)
        self.font_time    = ImageFont.truetype("anony/helpers/Inter-Light.ttf",   28)
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
            art_src = Image.open(temp).convert("RGBA")

            # BACKGROUND: full blurred + darkened thumbnail
            bg = art_src.resize((W, H), Image.Resampling.LANCZOS).convert("RGB")
            bg = bg.filter(ImageFilter.GaussianBlur(35))
            bg = ImageEnhance.Brightness(bg).enhance(0.38)
            canvas = bg.convert("RGBA")

            # LEFT: album art with rounded corners
            art_size = 460
            art = art_src.resize((art_size, art_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (art_size, art_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, art_size, art_size), radius=30, fill=255
            )
            art.putalpha(mask)
            art_x = 80
            art_y = (H - art_size) // 2
            canvas.paste(art, (art_x, art_y), art)

            draw = ImageDraw.Draw(canvas)

            # RIGHT content
            rx = art_x + art_size + 80
            ry = 170
            WHITE = (255, 255, 255)
            LGRAY = (200, 200, 200)

            title = (song.title or "Unknown")[:22]
            draw.text((rx, ry),      title,  font=self.font_title,   fill=WHITE)
            draw.text((rx, ry + 72), (song.channel_name or "")[:28], font=self.font_channel, fill=LGRAY)

            # Progress bar
            bar_y  = ry + 148
            bar_x1 = rx
            bar_x2 = W - 65
            bar_h  = 8
            draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y+bar_h), radius=4, fill=(120,120,120,160))
            prog_end = bar_x1 + int((bar_x2-bar_x1)*0.02)
            draw.rounded_rectangle((bar_x1, bar_y, prog_end, bar_y+bar_h), radius=4, fill=WHITE)
            draw.ellipse((prog_end-11, bar_y-7, prog_end+11, bar_y+bar_h+7), fill=WHITE)
            draw.text((bar_x1,      bar_y+20), "0:01",        font=self.font_time, fill=LGRAY)
            draw.text((bar_x2 - 70, bar_y+20), song.duration, font=self.font_time, fill=LGRAY)

            # Controls << || >>
            ctrl_y = bar_y + 90
            cx     = (bar_x1 + bar_x2) // 2
            gap    = 120
            tri    = 46

            def tri_left(x, y):
                draw.polygon([(x+tri,y),(x+tri//2,y+tri//2),(x+tri,y+tri)], fill=WHITE)
                draw.polygon([(x+tri//2,y),(x,y+tri//2),(x+tri//2,y+tri)], fill=WHITE)

            def tri_right(x, y):
                draw.polygon([(x,y),(x+tri//2,y+tri//2),(x,y+tri)], fill=WHITE)
                draw.polygon([(x+tri//2,y),(x+tri,y+tri//2),(x+tri//2,y+tri)], fill=WHITE)

            tri_left(cx - gap - tri, ctrl_y)
            tri_right(cx + gap,      ctrl_y)
            draw.rounded_rectangle((cx-22, ctrl_y, cx-6,  ctrl_y+tri), radius=5, fill=WHITE)
            draw.rounded_rectangle((cx+6,  ctrl_y, cx+22, ctrl_y+tri), radius=5, fill=WHITE)

            canvas.convert("RGB").save(output, quality=95)
            try: os.remove(temp)
            except Exception: pass
            return output

        except Exception:
            return config.DEFAULT_THUMB
