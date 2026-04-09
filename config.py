import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # === TELEGRAM ===
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    STRING_SESSION = os.getenv("STRING_SESSION", "")

    # === DATABASE ===
    MONGO_DB_URI = os.getenv("MONGO_DB_URI", "")

    # === BOT INFO ===
    BOT_NAME = os.getenv("BOT_NAME", "MusicBot")
    PREFIX = os.getenv("PREFIX", "/")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    OWNER_NAME = os.getenv("OWNER_NAME", "Owner")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")

    # === SUDO USERS ===
    SUDO_USERS = [
        int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.strip().isdigit()
    ]

    # === SUPPORT ===
    SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/Spotifyeupdates")
    SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/SpotifyeliteUpdates")

    # === COOKIES ===
    COOKIES_URL = os.getenv("COOKIES_URL", "")

    # === LIMITS ===
    DURATION_LIMIT = int(os.getenv("DURATION_LIMIT", 180))
    PLAYLIST_FETCH_LIMIT = int(os.getenv("PLAYLIST_FETCH_LIMIT", 25))
    AUTO_LEAVE_DELAY = int(os.getenv("AUTO_LEAVE_DELAY", 300))

    # === LOGGING ===
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", 0))

    # === FLOOD PROTECTION ===
    FLOOD_WAIT = 5  # seconds between play requests per user

    # === VOTE SKIP ===
    VOTE_SKIP_PERCENT = 51  # % of members needed to skip
