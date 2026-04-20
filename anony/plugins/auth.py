from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import is_admin
from anony.core.mongo import auth_user, unauth_user, get_auth_users, is_authed


@Client.on_message(filters.command("auth") & filters.group)
async def auth_cmd(client: Client, message: Message):
    cid, uid = message.chat.id, message.from_user.id
    if not await is_admin(client, cid, uid):
        return await message.reply_text("**Only admins can authorize users.**")
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        try: target = await client.get_users(int(message.command[1]))
        except: return await message.reply_text("**Invalid user ID.**")
    if not target:
        return await message.reply_text("**Reply to a user or provide user ID.**")
    if await is_authed(cid, target.id):
        return await message.reply_text(f"**{target.first_name} is already authorized.**")
    await auth_user(cid, target.id)
    await message.reply_text(f"**{target.first_name}** can now control music.")


@Client.on_message(filters.command("unauth") & filters.group)
async def unauth_cmd(client: Client, message: Message):
    cid, uid = message.chat.id, message.from_user.id
    if not await is_admin(client, cid, uid):
        return await message.reply_text("**Only admins.**")
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        try: target = await client.get_users(int(message.command[1]))
        except: return await message.reply_text("**Invalid.**")
    if not target: return await message.reply_text("**Reply to user or provide ID.**")
    await unauth_user(cid, target.id)
    await message.reply_text(f"**{target.first_name}** de-authorized.")


@Client.on_message(filters.command("authlist") & filters.group)
async def authlist_cmd(client: Client, message: Message):
    cid = message.chat.id
    users = await get_auth_users(cid)
    if not users: return await message.reply_text("**No authorized users.**")
    text = "**Authorized Users:**\n\n"
    for uid in users:
        try:
            u = await client.get_users(uid)
            text += f"• {u.first_name} (`{uid}`)\n"
        except: text += f"• `{uid}`\n"
    await message.reply_text(text)


@Client.on_message(filters.command("reload") & filters.group)
async def reload_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("**Only admins.**")
    await message.reply_text("**Admin cache reloaded.**")
