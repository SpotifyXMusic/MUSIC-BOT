"""
MusicBot V2 - Main Entry Point
Advanced Telegram Music Bot
"""

import asyncio
import logging
import os

from anony.core.bot import app
from anony.core import userbot, call_manager
from anony.helpers.youtube import setup_cookies
from anony.helpers.cleanup import start_cleanup
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pytgcalls").setLevel(logging.WARNING)

os.makedirs("downloads", exist_ok=True)
os.makedirs("downloads/thumbs", exist_ok=True)
os.makedirs("cookies", exist_ok=True)
os.makedirs("assets", exist_ok=True)


async def main():
    print("=" * 55)
    print(f"  {Config.BOT_NAME} V2 - Advanced Telegram Music Bot")
    print(f"  Owner: {Config.OWNER_NAME}")
    print("=" * 55)

    print("[1/5] Setting up YouTube cookies...")
    await setup_cookies()

    print("[2/5] Starting userbot...")
    await userbot.start()

    print("[3/5] Starting PyTgCalls...")
    await call_manager.start()

    print("[4/5] Starting bot...")
    await app.start()

    print("[5/5] Starting cleanup scheduler...")
    start_cleanup()

    me = await app.get_me()
    print(f"\n[OK] @{me.username} is running!")
    print(f"[OK] All features active: Lyrics, Thumbnail, Effects, VoteSkip, History, AutoLeave")
    print("=" * 55)

    if Config.LOG_GROUP_ID:
        try:
            await app.send_message(
                Config.LOG_GROUP_ID,
                f"**{Config.BOT_NAME} V2 Started!**\n"
                f"Owner: {Config.OWNER_NAME}\n"
                f"Features: Lyrics, Thumbnail, Effects, VoteSkip, History, AutoLeave, Playlist"
            )
        except Exception:
            pass

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Bot stopped.")
