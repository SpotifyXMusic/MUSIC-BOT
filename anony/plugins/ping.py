"""Ping Plugin V2"""
import time, psutil
from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import is_sudo

@Client.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    start = time.time()
    msg = await message.reply_text("Pinging...")
    ms = round((time.time() - start) * 1000, 2)
    proc = psutil.Process()
    mem = proc.memory_info().rss / (1024*1024)
    cpu = psutil.cpu_percent(interval=0.5)
    await msg.edit(
        f"**Pong!**\n\n**Latency:** `{ms}ms`\n**CPU:** `{cpu}%`\n**RAM:** `{mem:.1f} MB`"
    )

@Client.on_message(filters.command("ac"))
async def ac_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only.**")
    from anony.core import call_manager as cm
    await message.reply_text(f"**Active Voice Calls:** `{cm.active_count()}`")

@Client.on_message(filters.command("activevc"))
async def activevc_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only.**")
    from anony.core import call_manager as cm
    from anony.helpers.queue import queue
    chats = cm.active_chats()
    if not chats:
        return await message.reply_text("**No active voice calls.**")
    text = f"**Active Voice Calls: `{len(chats)}`**\n\n"
    for cid in chats:
        try:
            chat = await client.get_chat(cid)
            t = queue.get_current(cid)
            text += f"**{chat.title}**\n  `{t.title[:30] if t else 'Unknown'}`\n\n"
        except Exception:
            text += f"`{cid}`\n\n"
    await message.reply_text(text)

@Client.on_message(filters.command("reload") & filters.group)
async def reload_command(client: Client, message: Message):
    from anony.helpers.admins import can_control_stream
    if not await can_control_stream(client, message.chat.id, message.from_user.id):
        return await message.reply_text("**Only admins can reload.**")
    await message.reply_text("**Admin cache reloaded.**")
