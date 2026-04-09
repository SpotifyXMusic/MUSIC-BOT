"""
Auth Plugin
/auth /unauth - manage authorized users who can control streams without being admin
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from anony.helpers.admins import is_admin
from anony.core.mongo import auth_user, unauth_user, get_auth_users, is_authed


@Client.on_message(filters.command("auth") & filters.group)
async def auth_command(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admin(client, chat_id, user_id):
        return await message.reply_text("**Only admins can authorize users.**")

    target_user = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
            target_user = await client.get_users(target_id)
        except Exception:
            return await message.reply_text("**Invalid user ID.**")
    else:
        return await message.reply_text(
            "**Usage:** Reply to a user's message or `/auth <user_id>`"
        )

    if not target_user:
        return await message.reply_text("**User not found.**")

    if await is_admin(client, chat_id, target_user.id):
        return await message.reply_text("**User is already an admin!**")

    if await is_authed(chat_id, target_user.id):
        return await message.reply_text(f"**{target_user.first_name} is already authorized.**")

    await auth_user(chat_id, target_user.id)
    await message.reply_text(
        f"**Authorized!**\n\n"
        f"**{target_user.first_name}** can now control music streams in this chat."
    )


@Client.on_message(filters.command("unauth") & filters.group)
async def unauth_command(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_admin(client, chat_id, user_id):
        return await message.reply_text("**Only admins can remove authorization.**")

    target_user = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
            target_user = await client.get_users(target_id)
        except Exception:
            return await message.reply_text("**Invalid user ID.**")
    else:
        return await message.reply_text("**Usage:** Reply to a user or `/unauth <user_id>`")

    if not target_user:
        return await message.reply_text("**User not found.**")

    await unauth_user(chat_id, target_user.id)
    await message.reply_text(f"**{target_user.first_name}** has been de-authorized.")


@Client.on_message(filters.command("authlist") & filters.group)
async def authlist_command(client: Client, message: Message):
    chat_id = message.chat.id
    auth_users = await get_auth_users(chat_id)

    if not auth_users:
        return await message.reply_text("**No authorized users in this chat.**")

    text = "**Authorized Users:**\n\n"
    for uid in auth_users:
        try:
            user = await client.get_users(uid)
            text += f"  - {user.first_name} (`{uid}`)\n"
        except Exception:
            text += f"  - `{uid}`\n"

    await message.reply_text(text)
