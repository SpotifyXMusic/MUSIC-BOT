from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import is_sudo
from anony.core.mongo import blacklist_add, blacklist_remove, get_blacklist


@Client.on_message(filters.command("blacklist"))
async def bl_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo only.**")
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/blacklist <chat_id|user_id>`")
    try: tid = int(message.command[1])
    except: return await message.reply_text("**Invalid ID.**")
    t = "chat" if tid < 0 else "user"
    await blacklist_add(tid, t)
    await message.reply_text(f"**{t.title()} `{tid}` blacklisted.**")


@Client.on_message(filters.command("unblacklist"))
async def ubl_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo only.**")
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/unblacklist <id>`")
    try: tid = int(message.command[1])
    except: return await message.reply_text("**Invalid.**")
    await blacklist_remove(tid)
    await message.reply_text(f"**`{tid}` removed from blacklist.**")


@Client.on_message(filters.command("blacklistlist"))
async def bll_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo only.**")
    docs = await get_blacklist()
    if not docs: return await message.reply_text("**No blacklisted entries.**")
    text = "**Blacklist:**\n\n"
    for d in docs:
        text += f"• `{d['id']}` ({d['type']})\n"
    await message.reply_text(text)
