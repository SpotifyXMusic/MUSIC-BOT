"""
Admin and Permission Checks
"""

from pyrogram import Client
from pyrogram.types import Message
from config import Config
from anony.core.mongo import is_authed, is_blacklisted, get_sudos


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """Check if user is admin in the chat"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status.name in ("ADMINISTRATOR", "OWNER")
    except Exception:
        return False


async def is_sudo(user_id: int) -> bool:
    """Check if user is in sudo list"""
    if user_id == Config.OWNER_ID:
        return True
    sudos = await get_sudos()
    if user_id in sudos:
        return True
    if user_id in Config.SUDO_USERS:
        return True
    return False


async def is_owner(user_id: int) -> bool:
    return user_id == Config.OWNER_ID


async def can_control_stream(client: Client, chat_id: int, user_id: int) -> bool:
    """Admin, Auth user, or Sudo can control the stream"""
    if await is_sudo(user_id):
        return True
    if await is_admin(client, chat_id, user_id):
        return True
    if await is_authed(chat_id, user_id):
        return True
    return False


async def check_blacklist(chat_id: int, user_id: int) -> bool:
    """Returns True if chat or user is blacklisted"""
    return await is_blacklisted(chat_id) or await is_blacklisted(user_id)


def admin_only(func):
    """Decorator: only admins can use this command"""
    async def wrapper(client: Client, message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        if not await can_control_stream(client, chat_id, user_id):
            await message.reply_text(
                "**Access Denied!**\nOnly admins and authorized users can use this command."
            )
            return
        return await func(client, message)
    return wrapper


def sudo_only(func):
    """Decorator: only sudo users"""
    async def wrapper(client: Client, message: Message):
        user_id = message.from_user.id
        if not await is_sudo(user_id):
            await message.reply_text("**This command is restricted to sudo users only.**")
            return
        return await func(client, message)
    return wrapper


def owner_only(func):
    """Decorator: only bot owner"""
    async def wrapper(client: Client, message: Message):
        if message.from_user.id != Config.OWNER_ID:
            await message.reply_text("**Owner only command.**")
            return
        return await func(client, message)
    return wrapper
