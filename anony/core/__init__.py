"""
Core module init - starts userbot and call manager
"""

from pyrogram import Client
from config import Config
from anony.core.calls import CallManager

# Userbot client (String Session for voice calls)
userbot = Client(
    name="MusicUserbot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.STRING_SESSION,
)

# Global call manager
call_manager = CallManager(userbot)
