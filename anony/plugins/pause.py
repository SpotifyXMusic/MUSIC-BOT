"""
Pause Plugin V2 + all playback callback handlers
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.admins import can_control_stream
from anony.helpers.queue import queue
from anony.helpers.autoleave import schedule_leave, cancel_leave


def get_cm():
    from anony.core import call_manager
    return call_manager


@Client.on_message(filters.command("pause") & filters.group)
async def pause_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can pause.**")
    cm = get_cm()
    if not cm.is_active(chat_id):
        return await message.reply_text("**Nothing is playing.**")
    if cm.is_paused(chat_id):
        return await message.reply_text("**Already paused.** Use `/resume`.")
    if await cm.pause(chat_id):
        schedule_leave(chat_id)
        await message.reply_text(
            "**Stream Paused.**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶ Resume", callback_data="resume"),
                InlineKeyboardButton("⏹ Stop",   callback_data="stop"),
            ]])
        )
    else:
        await message.reply_text("**Failed to pause.**")


@Client.on_message(filters.command("mute") & filters.group)
async def mute_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can mute.**")
    if await get_cm().mute(chat_id):
        await message.reply_text("**Muted.**")
    else:
        await message.reply_text("**Failed to mute.**")


@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can unmute.**")
    if await get_cm().unmute(chat_id):
        await message.reply_text("**Unmuted.**")
    else:
        await message.reply_text("**Failed to unmute.**")


@Client.on_message(filters.command("loop") & filters.group)
async def loop_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can change loop mode.**")
    enabled = queue.toggle_loop(chat_id)
    await message.reply_text(f"**Queue Loop {'Enabled' if enabled else 'Disabled'}.**")


@Client.on_message(filters.command("repeat") & filters.group)
async def repeat_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can change repeat mode.**")
    enabled = queue.toggle_repeat(chat_id)
    await message.reply_text(f"**Repeat {'Enabled' if enabled else 'Disabled'}.**")


# ── ALL CONTROL CALLBACKS ────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^(pause|resume|skip|stop|loop|repeat|close|queue|effects)$"))
async def control_callback(client: Client, callback: CallbackQuery):
    action   = callback.data
    chat_id  = callback.message.chat.id
    user_id  = callback.from_user.id
    cm       = get_cm()

    if action == "close":
        await callback.message.delete()
        return

    if action == "effects":
        from anony.plugins.effects import effect_menu
        await effect_menu(client, callback.message)
        await callback.answer()
        return

    if action == "queue":
        text = queue.format_queue(chat_id)
        await callback.answer()
        await callback.message.reply_text(text)
        return

    if not await can_control_stream(client, chat_id, user_id):
        return await callback.answer("Only admins/auth users can control!", show_alert=True)

    if action == "pause":
        await cm.pause(chat_id)
        schedule_leave(chat_id)
        await callback.answer("Paused!")

    elif action == "resume":
        await cm.resume(chat_id)
        cancel_leave(chat_id)
        await callback.answer("Resumed!")

    elif action == "stop":
        await cm.stop(chat_id)
        queue.clear(chat_id)
        await callback.answer("Stopped!")
        await callback.message.edit("**Stream stopped. Queue cleared.**")

    elif action == "skip":
        next_t = queue.next(chat_id)
        if not next_t:
            await cm.stop(chat_id)
            await callback.answer("Queue ended!", show_alert=True)
            await callback.message.edit("**Queue ended.**")
        else:
            await callback.answer("Skipping...")
            from anony.helpers.youtube import download_audio, download_video
            try:
                fp = await (download_video(next_t.url) if next_t.is_video else download_audio(next_t.url))
                if fp:
                    next_t.file_path = fp
                    await cm.join_and_play(chat_id, fp, video=next_t.is_video)
                    cancel_leave(chat_id)
                    await callback.message.edit(
                        f"**Now Playing**\n\n**{next_t.title}**\n"
                        f"`{next_t.duration}` | {next_t.requested_by_name}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⏸ Pause", callback_data="pause"),
                            InlineKeyboardButton("⏭ Skip",  callback_data="skip"),
                            InlineKeyboardButton("⏹ Stop",  callback_data="stop"),
                        ]])
                    )
            except Exception:
                pass

    elif action == "loop":
        enabled = queue.toggle_loop(chat_id)
        await callback.answer(f"Loop {'ON' if enabled else 'OFF'}")

    elif action == "repeat":
        enabled = queue.toggle_repeat(chat_id)
        await callback.answer(f"Repeat {'ON' if enabled else 'OFF'}")
