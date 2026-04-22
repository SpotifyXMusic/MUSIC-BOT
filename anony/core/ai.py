# AI Core Module - Groq API Integration
# Features: Chat, Mood Detection, Song Recommendations, Text Moderation

import re
import aiohttp
from anony import config, logger


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

# Bad words list for moderation (Hindi + English)
BAD_WORDS = [
    "bc", "mc", "bkl", "bhosdi", "chutiya", "madarchod", "behenchod",
    "randi", "harami", "gandu", "lawda", "lund", "gaand", "chut",
    "fuck", "shit", "bitch", "asshole", "bastard", "whore", "slut",
    "nigger", "faggot", "cunt", "dick", "pussy", "cock",
    "maa ki", "behen ki", "teri maa", "teri behen",
]


async def groq_request(messages: list, system: str = None, max_tokens: int = 500) -> str | None:
    """Make a request to Groq API"""
    if not config.GROQ_API_KEY:
        return None

    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    payload = {
        "model": GROQ_MODEL,
        "messages": payload_messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.warning(f"Groq API error: {resp.status}")
                    return None
    except Exception as e:
        logger.warning(f"Groq request failed: {e}")
        return None


async def ai_chat(user_message: str, user_name: str = "User") -> str:
    """AI Chat - Answer any question"""
    system = (
        "You are a friendly Telegram music bot assistant. "
        "Keep responses short (2-3 lines max). "
        "You help users with music, song recommendations, and general queries. "
        "Be fun and engaging. Respond in the same language the user writes in."
    )
    response = await groq_request(
        messages=[{"role": "user", "content": user_message}],
        system=system,
        max_tokens=300,
    )
    return response or "Sorry, AI is unavailable right now. Try again later!"


async def detect_mood(text: str) -> str:
    """Detect mood from user message"""
    system = (
        "You are a mood detector. Analyze the text and return ONLY one word from this list: "
        "happy, sad, romantic, energetic, calm, angry, party, devotional, motivational, chill. "
        "No explanation. Just one word."
    )
    response = await groq_request(
        messages=[{"role": "user", "content": f"Detect mood: {text}"}],
        system=system,
        max_tokens=10,
    )
    if response:
        mood = response.strip().lower().split()[0]
        valid_moods = ["happy", "sad", "romantic", "energetic", "calm", "angry", "party", "devotional", "motivational", "chill"]
        if mood in valid_moods:
            return mood
    return "happy"


async def get_song_recommendation(title: str, artist: str = "", mood: str = "") -> str:
    """Get related song recommendation based on current song"""
    context = f"Song: {title}"
    if artist:
        context += f", Artist: {artist}"
    if mood:
        context += f", Mood: {mood}"

    system = (
        "You are a music expert. Given a song, suggest ONE similar song to play next. "
        "Return ONLY the song name and artist in this format: 'Song Name by Artist Name'. "
        "No explanation. Just the song recommendation."
    )
    response = await groq_request(
        messages=[{"role": "user", "content": f"Suggest next song after: {context}"}],
        system=system,
        max_tokens=50,
    )
    return response or None


async def get_mood_songs(mood: str, language: str = "Hindi") -> list[str]:
    """Get list of songs based on mood"""
    system = (
        f"You are a music expert specializing in {language} music. "
        "Return ONLY a numbered list of 5 song names with artist. "
        "Format: 1. Song Name - Artist\nNo extra text."
    )
    response = await groq_request(
        messages=[{"role": "user", "content": f"Give me 5 {language} {mood} mood songs"}],
        system=system,
        max_tokens=200,
    )
    if response:
        songs = []
        for line in response.strip().split("\n"):
            line = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if line:
                songs.append(line)
        return songs[:5]
    return []


async def get_song_info(title: str, artist: str = "") -> str:
    """Get information about a song"""
    query = f"{title} {artist}".strip()
    system = (
        "You are a music encyclopedia. Give brief info about a song: "
        "release year, album, genre, and one interesting fact. "
        "Keep it under 4 lines. Be accurate."
    )
    response = await groq_request(
        messages=[{"role": "user", "content": f"Tell me about the song: {query}"}],
        system=system,
        max_tokens=200,
    )
    return response or "Could not fetch song info right now."


async def translate_text(text: str, target_lang: str = "English") -> str:
    """Translate text to target language"""
    system = (
        f"You are a translator. Translate the given text to {target_lang}. "
        "Return ONLY the translation. No explanation."
    )
    response = await groq_request(
        messages=[{"role": "user", "content": text}],
        system=system,
        max_tokens=300,
    )
    return response or text


def check_bad_words(text: str) -> tuple[bool, str]:
    """Check if text contains bad words - returns (found, word)"""
    text_lower = text.lower()
    # Remove special characters for better detection
    clean_text = re.sub(r'[^a-z0-9\s]', ' ', text_lower)
    words = clean_text.split()

    for bad_word in BAD_WORDS:
        bad_word_clean = bad_word.lower()
        # Check exact word match
        if bad_word_clean in words:
            return True, bad_word
        # Check if bad word is substring (for compound words)
        if bad_word_clean in clean_text and len(bad_word_clean) > 3:
            return True, bad_word
    return False, ""


async def ai_check_text(text: str) -> tuple[bool, str]:
    """Use AI to check if text is abusive/inappropriate"""
    # First do quick local check
    found, word = check_bad_words(text)
    if found:
        return True, word

    # Then use AI for context-aware detection if API available
    if not config.GROQ_API_KEY:
        return False, ""

    system = (
        "You are a content moderator. Check if the text contains abuse, harassment, "
        "sexual content, extreme hate speech, or very offensive language. "
        "Reply ONLY with: YES or NO"
    )
    response = await groq_request(
        messages=[{"role": "user", "content": f"Is this abusive: '{text}'"}],
        system=system,
        max_tokens=5,
    )
    if response and "YES" in response.upper():
        return True, "inappropriate content"
    return False, ""
