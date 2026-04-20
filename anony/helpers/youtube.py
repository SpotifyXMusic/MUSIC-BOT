import asyncio, os, re, aiohttp, aiofiles
from yt_dlp import YoutubeDL
from urllib.parse import quote
from config import Config

COOKIES_FILE = "cookies/cookies.txt"
DL_DIR = "downloads/"
os.makedirs(DL_DIR, exist_ok=True)
os.makedirs("cookies", exist_ok=True)


def _opts(video=False):
    opts = {"quiet": True, "no_warnings": True, "geo_bypass": True,
            "socket_timeout": 15, "retries": 3, "noplaylist": True}
    if os.path.exists(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE
    if video:
        opts.update({"format": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                     "outtmpl": f"{DL_DIR}%(id)s.%(ext)s",
                     "merge_output_format": "mp4"})
    else:
        opts.update({"format": "bestaudio/best",
                     "outtmpl": f"{DL_DIR}%(id)s.%(ext)s",
                     "postprocessors": [{"key": "FFmpegExtractAudio",
                                         "preferredcodec": "mp3",
                                         "preferredquality": "192"}]})
    return opts


async def setup_cookies():
    if not Config.COOKIES_URL:
        return
    try:
        async with aiohttp.ClientSession() as s:
            for i, url in enumerate(Config.COOKIES_URL.split()):
                async with s.get(url.strip(), timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        fname = f"cookies/cookies{'_'+str(i) if i else ''}.txt"
                        async with aiofiles.open(fname, "w") as f:
                            await f.write(await r.text())
                        print(f"[COOKIES] Downloaded: {fname}")
    except Exception as e:
        print(f"[COOKIES] Error: {e}")


async def youtube_search(query: str, limit: int = 5) -> list:
    def _search():
        opts = {"quiet": True, "no_warnings": True,
                "extract_flat": True, "skip_download": True}
        if os.path.exists(COOKIES_FILE):
            opts["cookiefile"] = COOKIES_FILE
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            results = []
            for e in info.get("entries", []):
                d = e.get("duration", 0) or 0
                m, s = divmod(int(d), 60)
                results.append({
                    "title": e.get("title", "Unknown"),
                    "url": f"https://youtube.com/watch?v={e.get('id','')}",
                    "video_id": e.get("id", ""),
                    "duration": f"{m}:{s:02d}",
                    "duration_s": d,
                    "thumbnail": e.get("thumbnail", ""),
                    "channel": e.get("uploader", "YouTube"),
                    "views": e.get("view_count", 0),
                })
            return results
    return await asyncio.get_event_loop().run_in_executor(None, _search)


async def get_video_info(url: str) -> dict:
    def _info():
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        if os.path.exists(COOKIES_FILE):
            opts["cookiefile"] = COOKIES_FILE
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            d = info.get("duration", 0) or 0
            m, s = divmod(int(d), 60)
            return {
                "title": info.get("title", "Unknown"),
                "url": url, "video_id": info.get("id", ""),
                "duration": f"{m}:{s:02d}", "duration_s": d,
                "thumbnail": info.get("thumbnail", ""),
                "channel": info.get("uploader", "YouTube"),
                "views": info.get("view_count", 0),
            }
    return await asyncio.get_event_loop().run_in_executor(None, _info)


async def download_audio(url: str) -> str:
    def _dl():
        opts = _opts(video=False)
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            vid = info.get("id", "")
            for f in os.listdir(DL_DIR):
                if vid in f:
                    return os.path.join(DL_DIR, f)
        return None
    return await asyncio.get_event_loop().run_in_executor(None, _dl)


async def download_video(url: str) -> str:
    def _dl():
        opts = _opts(video=True)
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            vid = info.get("id", "")
            for f in os.listdir(DL_DIR):
                if vid in f:
                    return os.path.join(DL_DIR, f)
        return None
    return await asyncio.get_event_loop().run_in_executor(None, _dl)


async def fetch_playlist(url: str, limit: int = 25) -> list:
    def _fetch():
        opts = {"quiet": True, "no_warnings": True,
                "extract_flat": True, "skip_download": True, "playlistend": limit}
        if os.path.exists(COOKIES_FILE):
            opts["cookiefile"] = COOKIES_FILE
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            results = []
            for e in (info.get("entries") or [])[:limit]:
                if not e: continue
                d = e.get("duration", 0) or 0
                m, s = divmod(int(d), 60)
                results.append({
                    "title": e.get("title", "Unknown"),
                    "url": f"https://youtube.com/watch?v={e.get('id','')}",
                    "video_id": e.get("id", ""),
                    "duration": f"{m}:{s:02d}", "duration_s": d,
                    "thumbnail": e.get("thumbnail", ""),
                    "channel": e.get("uploader", "YouTube"),
                })
            return results
    return await asyncio.get_event_loop().run_in_executor(None, _fetch)


def is_url(text: str) -> bool:
    return bool(re.match(r"https?://(www\.)?(youtube\.com|youtu\.be)/.+", text))

def fmt_views(v: int) -> str:
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000: return f"{v/1_000:.1f}K"
    return str(v)
