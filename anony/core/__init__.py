from pyrogram import Client
from config import Config
from anony.core.calls import CallManager

userbot = Client(
    name="MusicUserbot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.STRING_SESSION,
)

call_manager = CallManager(userbot)
