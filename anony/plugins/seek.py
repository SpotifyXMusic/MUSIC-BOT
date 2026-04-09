"""Seek Plugin V2"""
from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import can_control_stream

@Client.on_message(filters.command("seek") & filters.group)
async def seek_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can seek.**")
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/seek <seconds>`  Example: `/seek 30`")
    try:
        s = int(message.command[1])
    except ValueError:
        return await message.reply_text("**Invalid value. Use a number.**")
    from anony.core import call_manager as cm
    if await cm.seek(chat_id, s):
        await message.reply_text(f"**Seeked forward `{s}` seconds.**")
    else:
        await message.reply_text("**Seek failed. Is anything playing?**")

@Client.on_message(filters.command("seekback") & filters.group)
async def seekback_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can seek.**")
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/seekback <seconds>`")
    try:
        s = int(message.command[1])
    except ValueError:
        return await message.reply_text("**Invalid value.**")
    from anony.core import call_manager as cm
    if await cm.seek(chat_id, -abs(s)):
        await message.reply_text(f"**Seeked backward `{s}` seconds.**")
    else:
        await message.reply_text("**Seekback failed.**")
