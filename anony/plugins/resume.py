"""Resume Plugin V2"""
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from anony.helpers.admins import can_control_stream
from anony.helpers.queue import queue
from anony.helpers.autoleave import cancel_leave

@Client.on_message(filters.command("resume") & filters.group)
async def resume_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can resume.**")
    from anony.core import call_manager as cm
    if not cm.is_active(chat_id):
        return await message.reply_text("**Nothing is playing.**")
    if await cm.resume(chat_id):
        cancel_leave(chat_id)
        track = queue.get_current(chat_id)
        await message.reply_text(
            f"**Resumed**\nPlaying: **{track.title if track else 'Unknown'}**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏸ Pause", callback_data="pause"),
                InlineKeyboardButton("⏭ Skip",  callback_data="skip"),
                InlineKeyboardButton("⏹ Stop",  callback_data="stop"),
            ]])
        )
    else:
        await message.reply_text("**Failed to resume.**")
