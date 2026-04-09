"""
Language Plugin
/lang - change bot language
"""

import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.admins import is_admin
from anony.core.mongo import set_setting, get_setting


LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ar": "Arabic",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "my": "Burmese",
    "pa": "Punjabi",
    "pt": "Portuguese",
    "ru": "Russian",
    "tr": "Turkish",
    "zh": "Chinese",
}


@Client.on_message(filters.command("lang") & filters.group)
async def lang_command(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admin(client, chat_id, user_id):
        return await message.reply_text("**Only admins can change the bot language.**")

    current = await get_setting(chat_id, "language", "en")

    buttons = []
    row = []
    for code, name in LANGUAGES.items():
        marker = " ✓" if code == current else ""
        row.append(InlineKeyboardButton(f"{name}{marker}", callback_data=f"setlang_{code}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Close", callback_data="close")])

    await message.reply_text(
        f"**Select Language**\n\nCurrent: `{LANGUAGES.get(current, 'English')}`",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^setlang_"))
async def set_lang_callback(client: Client, callback: CallbackQuery):
    lang_code = callback.data.split("_", 1)[1]
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    if not await is_admin(client, chat_id, user_id):
        return await callback.answer("Only admins can change language!", show_alert=True)

    if lang_code not in LANGUAGES:
        return await callback.answer("Invalid language!", show_alert=True)

    await set_setting(chat_id, "language", lang_code)
    lang_name = LANGUAGES[lang_code]
    await callback.answer(f"Language set to {lang_name}!", show_alert=False)
    await callback.message.edit(
        f"**Language changed to {lang_name}**\n\nBot will now respond in {lang_name}."
    )
