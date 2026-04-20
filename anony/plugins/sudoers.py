from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import is_sudo
from anony.core.mongo import add_sudo, remove_sudo, get_sudos
from config import Config


@Client.on_message(filters.command("addsudo"))
async def addsudo_cmd(client: Client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("**Owner only.**")
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        try: target = await client.get_users(int(message.command[1]))
        except: return await message.reply_text("**Invalid.**")
    if not target: return await message.reply_text("**Reply or provide ID.**")
    await add_sudo(target.id)
    await message.reply_text(f"**{target.first_name}** added to sudo.")


@Client.on_message(filters.command("rmsudo"))
async def rmsudo_cmd(client: Client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply_text("**Owner only.**")
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        try: target = await client.get_users(int(message.command[1]))
        except: return await message.reply_text("**Invalid.**")
    if not target: return await message.reply_text("**Reply or provide ID.**")
    await remove_sudo(target.id)
    await message.reply_text(f"**{target.first_name}** removed from sudo.")


@Client.on_message(filters.command("sudolist"))
async def sudolist_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo only.**")
    sudos = list(set(await get_sudos() + Config.SUDO_USERS))
    text = f"**Sudo Users:**\n\nOwner: {Config.OWNER_NAME} (`{Config.OWNER_ID}`)\n\n"
    for uid in sudos:
        try:
            u = await client.get_users(uid)
            text += f"• {u.first_name} (`{uid}`)\n"
        except: text += f"• `{uid}`\n"
    await message.reply_text(text)
