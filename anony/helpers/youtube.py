"""
YouTube Helper - Search, Download Audio/Video
Uses yt-dlp with cookie support to bypass VPS blocks
"""

import asyncio
import os
import re
import aiohttp
import aiofiles
from yt_dlp import YoutubeDL
from config import Config


COOKIES_FILE = "cookies/cookies.txt"
DOWNLOAD_DIR = "downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs("cookies", exist_ok=True)


def _get_ydl_opts(video: bool = False, cookies: bool = True) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "socket_timeout": 10,
        "retries": 3,
    }

    # Cookie support
    if cookies and os.path.exists(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE

    if video:
        opts.update({
            "format": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
            "outtmpl": f"{DOWNLOAD_DIR}%(id)s.%(ext)s",
            "merge_output_format": "mp4",
        })
    else:
        opts.update({
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}%(id)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })

    return opts


# ─── SETUP COOKIES ───────────────────────────────────────────────────────────

async def setup_cookies():
    """Download cookies from COOKIES_URL if set"""
    if not Config.COOKIES_URL:
        return
    try:
        async with aiohttp.ClientSession() as session:
            urls = Config.COOKIES_URL.split(" ")
            for i, url in enumerate(urls):
                url = url.strip()
                if not url:
                    continue
                async with session.get(url) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        fname = f"cookies/cookies{'_'+str(i) if i > 0 else ''}.txt"
                        async with aiofiles.open(fname, "w") as f:
                            await f.write(content)
                        print(f"[COOKIES] Downloaded cookie file: {fname}")
    except Exception as e:
        print(f"[COOKIES] Failed to download cookies: {e}")


# ─── SEARCH ──────────────────────────────────────────────────────────────────

async def youtube_search(query: str, limit: int = 5) -> list:
    """
    Search YouTube and return list of results
    Returns: [{"title", "url", "duration", "views", "thumbnail", "channel"}]
    """
    def _search():
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "default_search": f"ytsearch{limit}",
            "skip_download": True,
        }
        if os.path.exists(COOKIES_FILE):
            opts["cookiefile"] = COOKIES_FILE

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            results = []
            for entry in info.get("entries", []):
                duration_s = entry.get("duration", 0)
                mins, secs = divmod(duration_s or 0, 60)
                results.append({
                    "title": entry.get("title", "Unknown"),
                    "url": f"https://youtube.com/watch?v={entry.get('id')}",
                    "video_id": entry.get("id", ""),
                    "duration": f"{mins}:{secs:02d}",
                    "duration_s": duration_s,
                    "views": entry.get("view_count", 0),
                    "thumbnail": entry.get("thumbnail", ""),
                    "channel": entry.get("uploader", "Unknown"),
                })
            return results

    return await asyncio.get_event_loop().run_in_executor(None, _search)


async def get_video_info(url: str) -> dict:
    """Get info about a YouTube URL"""
    def _get_info():
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        if os.path.exists(COOKIES_FILE):
            opts["cookiefile"] = COOKIES_FILE

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration_s = info.get("duration", 0)
            mins, secs = divmod(duration_s or 0, 60)
            return {
                "title": info.get("title", "Unknown"),
                "url": url,
                "video_id": info.get("id", ""),
                "duration": f"{mins}:{secs:02d}",
                "duration_s": duration_s,
                "thumbnail": info.get("thumbnail", ""),
                "channel": info.get("uploader", "Unknown"),
                "views": info.get("view_count", 0),
            }

    return await asyncio.get_event_loop().run_in_executor(None, _get_info)


# ─── DOWNLOAD ────────────────────────────────────────────────────────────────

async def download_audio(url: str) -> str:
    """Download audio and return file path"""
    def _download():
        opts = _get_ydl_opts(video=False)
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id", "")
            # Find downloaded file
            for f in os.listdir(DOWNLOAD_DIR):
                if video_id in f:
                    return os.path.join(DOWNLOAD_DIR, f)
        return None

    return await asyncio.get_event_loop().run_in_executor(None, _download)


async def download_video(url: str) -> str:
    """Download video (<=480p) and return file path"""
    def _download():
        opts = _get_ydl_opts(video=True)
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id", "")
            for f in os.listdir(DOWNLOAD_DIR):
                if video_id in f:
                    return os.path.join(DOWNLOAD_DIR, f)
        return None

    return await asyncio.get_event_loop().run_in_executor(None, _download)


def is_youtube_url(text: str) -> bool:
    pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
    return bool(re.match(pattern, text))


def format_views(views: int) -> str:
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    elif views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


async def fetch_playlist(url: str, limit: int = 25) -> list:
    """Fetch tracks from YouTube playlist"""
    def _fetch():
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "playlistend": limit,
        }
        import os
        if os.path.exists("cookies/cookies.txt"):
            opts["cookiefile"] = "cookies/cookies.txt"
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            results = []
            for entry in info.get("entries", [])[:limit]:
                if not entry:
                    continue
                d = entry.get("duration", 0) or 0
                m, s = divmod(int(d), 60)
                results.append({
                    "title": entry.get("title", "Unknown"),
                    "url": f"https://youtube.com/watch?v={entry.get('id', '')}",
                    "video_id": entry.get("id", ""),
                    "duration": f"{m}:{s:02d}",
                    "duration_s": d,
                    "thumbnail": entry.get("thumbnail", ""),
                    "channel": entry.get("uploader", "YouTube"),
                })
            return results
    import asyncio
    return await asyncio.get_event_loop().run_in_executor(None, _fetch)
