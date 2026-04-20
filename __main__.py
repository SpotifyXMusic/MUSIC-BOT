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
    print("=" * 50)
    print(f"  {Config.BOT_NAME} V3 - Telegram Music Bot")
    print(f"  Owner: {Config.OWNER_NAME}")
    print("=" * 50)

    print("[1/4] Setting up cookies...")
    await setup_cookies()

    print("[2/4] Starting userbot...")
    await userbot.start()

    print("[3/4] Starting PyTgCalls...")
    await call_manager.start()

    print("[4/4] Starting bot...")
    await app.start()

    start_cleanup()

    me = await app.get_me()
    print(f"\n✅ @{me.username} is RUNNING!")
    print("=" * 50)

    if Config.LOG_GROUP_ID:
        try:
            await app.send_message(
                Config.LOG_GROUP_ID,
                f"**{Config.BOT_NAME} V3 Started!**\n"
                f"Owner: {Config.OWNER_NAME}"
            )
        except Exception:
            pass

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Stopped.")
