"""
Bot Client Initialization
"""

import asyncio
from pyrogram import Client
from config import Config


class MusicBot(Client):
    def __init__(self):
        super().__init__(
            name="MusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="anony/plugins"),
            workers=50,
            sleep_threshold=10,
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username = f"@{me.username}"
        self.id = me.id
        self.name = me.first_name
        print(f"[BOT] {self.name} started successfully!")
        if Config.LOG_GROUP_ID:
            try:
                await self.send_message(
                    Config.LOG_GROUP_ID,
                    f"**{Config.BOT_NAME}** started!\n"
                    f"**Version:** 2.0\n"
                    f"**Owner:** {Config.OWNER_NAME}"
                )
            except Exception:
                pass

    async def stop(self, *args):
        await super().stop()
        print("[BOT] Bot stopped.")


app = MusicBot()
