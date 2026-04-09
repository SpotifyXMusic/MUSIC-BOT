"""
Sudo Users Plugin
/addsudo /rmsudo /sudolist
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from anony.helpers.admins import is_sudo, is_owner
from anony.core.mongo import add_sudo, remove_sudo, get_sudos


@Client.on_message(filters.command("addsudo"))
async def add_sudo_cmd(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        return await message.reply_text("**Owner only command.**")

    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(int(message.command[1]))
        except Exception:
            return await message.reply_text("**Invalid user ID.**")

    if not target:
        return await message.reply_text("**Reply to a user or provide a user ID.**")

    await add_sudo(target.id)
    await message.reply_text(
        f"**{target.first_name}** (`{target.id}`) added to sudo users."
    )


@Client.on_message(filters.command("rmsudo"))
async def rm_sudo_cmd(client: Client, message: Message):
    if not await is_owner(message.from_user.id):
        return await message.reply_text("**Owner only command.**")

    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(int(message.command[1]))
        except Exception:
            return await message.reply_text("**Invalid user ID.**")

    if not target:
        return await message.reply_text("**Reply to a user or provide a user ID.**")

    await remove_sudo(target.id)
    await message.reply_text(f"**{target.first_name}** removed from sudo users.")


@Client.on_message(filters.command("sudolist"))
async def sudo_list(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only command.**")

    sudo_ids = await get_sudos()
    sudo_ids = list(set(sudo_ids + Config.SUDO_USERS))  # merge env sudos

    if not sudo_ids:
        return await message.reply_text(
            f"**Sudo Users:**\n\nOnly owner: {Config.OWNER_NAME} (`{Config.OWNER_ID}`)"
        )

    text = f"**Sudo Users:**\n\nOwner: {Config.OWNER_NAME} (`{Config.OWNER_ID}`)\n\n"
    for uid in sudo_ids:
        try:
            user = await client.get_users(uid)
            text += f"  - {user.first_name} (`{uid}`)\n"
        except Exception:
            text += f"  - `{uid}`\n"

    await message.reply_text(text)
