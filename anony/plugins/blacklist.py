"""
Blacklist Plugin
/blacklist /unblacklist - block chats/users from using the bot
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from anony.helpers.admins import is_sudo
from anony.core.mongo import blacklist_chat, blacklist_user, unblacklist, get_blacklist, is_blacklisted


@Client.on_message(filters.command("blacklist"))
async def blacklist_command(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_sudo(user_id):
        return await message.reply_text("**Sudo-only command.**")

    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/blacklist <chat_id|user_id>`\n"
            "Blacklisted chats/users cannot use the bot."
        )

    try:
        target_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("**Invalid ID.** Provide a numeric chat/user ID.")

    if target_id < 0:
        await blacklist_chat(target_id)
        await message.reply_text(f"**Chat `{target_id}` blacklisted.**")
    else:
        await blacklist_user(target_id)
        await message.reply_text(f"**User `{target_id}` blacklisted.**")


@Client.on_message(filters.command("unblacklist"))
async def unblacklist_command(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_sudo(user_id):
        return await message.reply_text("**Sudo-only command.**")

    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/unblacklist <chat_id|user_id>`")

    try:
        target_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("**Invalid ID.**")

    await unblacklist(target_id)
    await message.reply_text(f"**`{target_id}` removed from blacklist.**")


@Client.on_message(filters.command("blacklistlist"))
async def blacklist_list(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_sudo(user_id):
        return await message.reply_text("**Sudo-only command.**")

    docs = await get_blacklist()
    if not docs:
        return await message.reply_text("**No blacklisted chats/users.**")

    chats = [d["id"] for d in docs if d["type"] == "chat"]
    users = [d["id"] for d in docs if d["type"] == "user"]

    text = "**Blacklist**\n\n"
    if chats:
        text += "**Chats:**\n" + "\n".join(f"  `{c}`" for c in chats) + "\n\n"
    if users:
        text += "**Users:**\n" + "\n".join(f"  `{u}`" for u in users)

    await message.reply_text(text)
