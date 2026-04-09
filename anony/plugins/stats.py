"""Stats Plugin V2"""
import time, psutil
from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import is_sudo
from anony.core.mongo import get_user_count, get_chat_count, get_play_count

@Client.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only.**")
    users = await get_user_count()
    chats = await get_chat_count()
    plays = await get_play_count()
    from anony.core import call_manager as cm
    active = cm.active_count()
    proc = psutil.Process()
    mem = proc.memory_info().rss/(1024*1024)
    cpu = psutil.cpu_percent(interval=0.5)
    h, rem = divmod(int(time.time()-proc.create_time()), 3600)
    m, s = divmod(rem, 60)
    await message.reply_text(
        f"**Bot Statistics**\n\n"
        f"**Users:** `{users}`\n**Chats:** `{chats}`\n"
        f"**Total Plays:** `{plays}`\n**Active Calls:** `{active}`\n\n"
        f"**System:**\nCPU: `{cpu}%` | RAM: `{mem:.1f} MB`\n"
        f"Uptime: `{h}h {m}m {s}s`"
    )
