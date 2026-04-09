"""Active Plugin"""
from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import is_sudo
from anony.helpers.queue import queue

@Client.on_message(filters.command("active"))
async def active_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id): return await message.reply_text("**Sudo-only.**")
    from anony.core import call_manager as cm
    chats = cm.active_chats()
    if not chats: return await message.reply_text("**No active voice calls.**")
    text = f"**Active: `{len(chats)}`**\n\n"
    for cid in chats:
        try:
            chat = await client.get_chat(cid)
            t = queue.get_current(cid)
            text += f"**{chat.title}**\n  {t.title[:30] if t else '?'}\n\n"
        except Exception:
            text += f"`{cid}`\n\n"
    await message.reply_text(text)
