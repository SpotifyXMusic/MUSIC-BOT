import aiohttp, re
from urllib.parse import quote


async def get_lyrics(title: str, artist: str = "") -> str:
    title_c = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()
    artist_c = artist.strip() if artist else "unknown"
    try:
        url = f"https://api.lyrics.ovh/v1/{quote(artist_c)}/{quote(title_c)}"
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.json()
                    lyr = data.get("lyrics", "")
                    if lyr and len(lyr) > 50:
                        return lyr.strip()
    except Exception:
        pass
    return None


def chunk_lyrics(lyrics: str, max_len: int = 4000) -> list:
    chunks, current = [], ""
    for line in lyrics.split("\n"):
        if len(current) + len(line) + 1 > max_len:
            if current: chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip(): chunks.append(current.strip())
    return chunks or [lyrics[:max_len]]
