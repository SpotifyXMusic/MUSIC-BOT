"""Stop Plugin V2"""
from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import can_control_stream
from anony.helpers.queue import queue
from anony.helpers.autoleave import cancel_leave

@Client.on_message(filters.command("stop") & filters.group)
async def stop_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can stop.**")
    from anony.core import call_manager as cm
    await cm.stop(chat_id)
    queue.clear(chat_id)
    cancel_leave(chat_id)
    await message.reply_text("**Stream Stopped.** Queue cleared. Bot left voice chat.")
