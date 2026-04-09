"""
Group Settings Plugin
/settings - Interactive settings panel with toggle buttons
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.admins import is_admin
from anony.core.mongo import get_group_settings, update_group_setting
from anony.helpers.autoleave import toggle_auto_leave, is_auto_leave_on


async def _settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    s = await get_group_settings(chat_id)

    def toggle_btn(label, key, val):
        status = "✅ ON" if val else "❌ OFF"
        return InlineKeyboardButton(f"{label}: {status}", callback_data=f"setting_{key}")

    return InlineKeyboardMarkup([
        [toggle_btn("Auto Leave",  "auto_leave",   s.get("auto_leave", True))],
        [toggle_btn("Vote Skip",   "vote_skip",    s.get("vote_skip", False))],
        [toggle_btn("Thumbnail",   "thumbnail",    s.get("thumbnail", True))],
        [toggle_btn("Announce",    "announce",     s.get("announce", True))],
        [InlineKeyboardButton("🌍 Language", callback_data="help_language"),
         InlineKeyboardButton("❌ Close",    callback_data="close")],
    ])


@Client.on_message(filters.command("settings") & filters.group)
async def settings_command(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admin(client, chat_id, user_id):
        return await message.reply_text("**Only admins can change settings.**")

    s = await get_group_settings(chat_id)
    kb = await _settings_keyboard(chat_id)

    await message.reply_text(
        "**Group Settings**\n\n"
        "Tap a button to toggle on/off:",
        reply_markup=kb
    )


@Client.on_callback_query(filters.regex("^setting_"))
async def setting_callback(client: Client, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    if not await is_admin(client, chat_id, user_id):
        return await callback.answer("Only admins can change settings!", show_alert=True)

    key = callback.data.replace("setting_", "")
    s = await get_group_settings(chat_id)
    current = s.get(key, True)
    new_val = not current
    await update_group_setting(chat_id, key, new_val)

    # Extra actions
    if key == "auto_leave":
        toggle_auto_leave(chat_id)

    status = "ON" if new_val else "OFF"
    await callback.answer(f"{key.replace('_', ' ').title()}: {status}", show_alert=False)

    kb = await _settings_keyboard(chat_id)
    await callback.message.edit_reply_markup(kb)
