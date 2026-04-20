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
        print(f"[BOT] @{me.username} started!")
        if Config.LOG_GROUP_ID:
            try:
                await self.send_message(Config.LOG_GROUP_ID,
                    f"**{Config.BOT_NAME} Started!**\nVersion: 3.0")
            except Exception:
                pass

    async def stop(self, *args):
        await super().stop()

app = MusicBot()
