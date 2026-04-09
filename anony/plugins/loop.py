"""Loop Plugin"""
from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import can_control_stream
from anony.helpers.queue import queue

@Client.on_message(filters.command("loopqueue") & filters.group)
async def loopqueue_command(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control_stream(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth users.**")
    enabled = queue.toggle_loop(cid)
    await message.reply_text(f"**Queue Loop {'Enabled' if enabled else 'Disabled'}.**")
