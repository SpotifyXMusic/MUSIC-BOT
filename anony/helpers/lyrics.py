"""
Lyrics Fetcher - No API key needed
Uses free lyrics sources: lyrics.ovh API (completely free, no signup)
"""

import asyncio
import aiohttp
import re


async def get_lyrics(song_name: str, artist: str = "") -> str:
    """
    Fetch lyrics using free lyrics.ovh API - no API key needed.
    Returns lyrics string or error message.
    """
    query = f"{artist} {song_name}".strip() if artist else song_name

    # Method 1: lyrics.ovh (free, no key)
    lyrics = await _fetch_lyricsovh(song_name, artist)
    if lyrics:
        return lyrics

    # Method 2: try with cleaned title
    clean = re.sub(r"\(.*?\)|\[.*?\]|feat\.|ft\.|official|video|audio|hd|4k", "", query, flags=re.IGNORECASE).strip()
    parts = clean.split(" - ", 1)
    if len(parts) == 2:
        lyrics = await _fetch_lyricsovh(parts[1].strip(), parts[0].strip())
        if lyrics:
            return lyrics

    return None


async def _fetch_lyricsovh(title: str, artist: str = "") -> str:
    """lyrics.ovh free API"""
    try:
        # Clean title
        title_clean = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()
        artist_clean = artist.strip() if artist else "unknown"

        url = f"https://api.lyrics.ovh/v1/{aiohttp.helpers.quote(artist_clean)}/{aiohttp.helpers.quote(title_clean)}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lyrics = data.get("lyrics", "")
                    if lyrics and len(lyrics) > 50:
                        return lyrics.strip()
    except Exception:
        pass
    return None


def chunk_lyrics(lyrics: str, max_len: int = 4000) -> list:
    """Split lyrics into chunks for Telegram message limit"""
    chunks = []
    lines = lyrics.split("\n")
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            if current:
                chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [lyrics[:max_len]]
