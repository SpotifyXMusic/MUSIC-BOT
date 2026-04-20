from pyrogram import Client
from config import Config
from anony.core.mongo import is_authed, get_sudos


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id == Config.OWNER_ID: return True
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status.name in ("ADMINISTRATOR", "OWNER")
    except Exception:
        return False


async def is_sudo(user_id: int) -> bool:
    if user_id == Config.OWNER_ID: return True
    if user_id in Config.SUDO_USERS: return True
    sudos = await get_sudos()
    return user_id in sudos


async def can_control(client: Client, chat_id: int, user_id: int) -> bool:
    if await is_sudo(user_id): return True
    if await is_admin(client, chat_id, user_id): return True
    if await is_authed(chat_id, user_id): return True
    return False
