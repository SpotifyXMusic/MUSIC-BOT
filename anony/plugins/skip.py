"""Skip Plugin V2"""
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from anony.helpers.admins import can_control_stream
from anony.helpers.queue import queue
from anony.helpers.youtube import download_audio, download_video
from anony.helpers.autoleave import cancel_leave, schedule_leave


@Client.on_message(filters.command("skip") & filters.group)
async def skip_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can skip.**")
    from anony.core import call_manager as cm
    if not cm.is_active(chat_id):
        return await message.reply_text("**Nothing is playing.**")
    next_track = queue.next(chat_id)
    if not next_track:
        await cm.stop(chat_id)
        return await message.reply_text("**Queue ended.** Bot left voice chat.")
    status = await message.reply_text("**Skipping...**")
    try:
        fp = await (download_video(next_track.url) if next_track.is_video else download_audio(next_track.url))
        if not fp:
            return await status.edit("**Failed to download next track.**")
        next_track.file_path = fp
        await cm.join_and_play(chat_id, fp, video=next_track.is_video)
        cancel_leave(chat_id)
        await status.edit(
            f"**Skipped!**\n\n**Now Playing:** {next_track.title}\n"
            f"`{next_track.duration}` | {next_track.requested_by_name}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏸ Pause", callback_data="pause"),
                InlineKeyboardButton("⏭ Skip",  callback_data="skip"),
                InlineKeyboardButton("⏹ Stop",  callback_data="stop"),
            ]])
        )
    except Exception as e:
        await status.edit(f"**Error:** `{str(e)[:150]}`")
