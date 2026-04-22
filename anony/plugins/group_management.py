# Group Management Plugin
# Features: Welcome/Goodbye, Ban, Kick, Mute, Unmute, Purge, UserInfo

from pyrogram import filters, types, enums
from pyrogram.errors import UserAdminInvalid, ChatAdminRequired, UserNotParticipant

from anony import app, config


async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]
    except Exception:
        return False


async def is_owner(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status == enums.ChatMemberStatus.OWNER
    except Exception:
        return False


# ─── WELCOME / GOODBYE ───────────────────────────────────────────────────────

@app.on_message(filters.new_chat_members & filters.group)
async def welcome_member(_, message: types.Message):
    """Welcome new members"""
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        try:
            await message.reply_text(
                f"<b>Welcome to {message.chat.title}!</b>\n"
                f"<code>━━━━━━━━━━━━━━━━</code>\n"
                f"Hey {member.mention}, glad you joined us!\n\n"
                f"<i>Use /aihelp to see AI features\n"
                f"Use /play [song] to play music</i>",
            )
        except Exception:
            pass


@app.on_message(filters.left_chat_member & filters.group)
async def goodbye_member(_, message: types.Message):
    """Goodbye message when member leaves"""
    member = message.left_chat_member
    if member and not member.is_bot:
        try:
            await message.reply_text(
                f"<b>{member.mention} has left the group.</b>\n"
                f"<i>Goodbye! See you next time.</i>"
            )
        except Exception:
            pass


# ─── BAN / KICK / MUTE ───────────────────────────────────────────────────────

@app.on_message(filters.command(["ban"]) & filters.group)
async def ban_user(_, message: types.Message):
    """Ban a user"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>Only admins can ban users.</b>")

    user = None
    reason = "No reason provided"

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if len(message.command) > 1:
            reason = " ".join(message.command[1:])
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
            if len(message.command) > 2:
                reason = " ".join(message.command[2:])
        except Exception:
            return await message.reply_text("<b>User not found.</b>")

    if not user:
        return await message.reply_text("<b>Reply to a user or provide username/ID.</b>")

    if await is_admin(message.chat.id, user.id):
        return await message.reply_text("<b>Cannot ban an admin.</b>")

    try:
        await app.ban_chat_member(message.chat.id, user.id)
        await message.reply_text(
            f"<b>Banned: {user.mention}</b>\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>By:</b> {message.from_user.mention}"
        )
    except (UserAdminInvalid, ChatAdminRequired):
        await message.reply_text("<b>I need ban permissions to do this.</b>")
    except Exception as e:
        await message.reply_text(f"<b>Failed:</b> {e}")


@app.on_message(filters.command(["unban"]) & filters.group)
async def unban_user(_, message: types.Message):
    """Unban a user"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>Only admins can unban users.</b>")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except Exception:
            return await message.reply_text("<b>User not found.</b>")
    else:
        return await message.reply_text("<b>Reply to a user or provide username/ID.</b>")

    try:
        await app.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(f"<b>Unbanned: {user.mention}</b>")
    except Exception as e:
        await message.reply_text(f"<b>Failed:</b> {e}")


@app.on_message(filters.command(["kick"]) & filters.group)
async def kick_user(_, message: types.Message):
    """Kick a user"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>Only admins can kick users.</b>")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
        reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason"
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason"
        except Exception:
            return await message.reply_text("<b>User not found.</b>")
    else:
        return await message.reply_text("<b>Reply to a user or provide username/ID.</b>")

    if await is_admin(message.chat.id, user.id):
        return await message.reply_text("<b>Cannot kick an admin.</b>")

    try:
        await app.ban_chat_member(message.chat.id, user.id)
        await app.unban_chat_member(message.chat.id, user.id)
        await message.reply_text(
            f"<b>Kicked: {user.mention}</b>\n"
            f"<b>Reason:</b> {reason}"
        )
    except (UserAdminInvalid, ChatAdminRequired):
        await message.reply_text("<b>I need kick permissions to do this.</b>")
    except Exception as e:
        await message.reply_text(f"<b>Failed:</b> {e}")


@app.on_message(filters.command(["mute"]) & filters.group)
async def mute_user(_, message: types.Message):
    """Mute a user"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>Only admins can mute users.</b>")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except Exception:
            return await message.reply_text("<b>User not found.</b>")
    else:
        return await message.reply_text("<b>Reply to a user or provide username/ID.</b>")

    if await is_admin(message.chat.id, user.id):
        return await message.reply_text("<b>Cannot mute an admin.</b>")

    try:
        await app.restrict_chat_member(
            message.chat.id,
            user.id,
            types.ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
            ),
        )
        await message.reply_text(f"<b>Muted: {user.mention}</b>")
    except (UserAdminInvalid, ChatAdminRequired):
        await message.reply_text("<b>I need restrict permissions to do this.</b>")
    except Exception as e:
        await message.reply_text(f"<b>Failed:</b> {e}")


@app.on_message(filters.command(["unmute"]) & filters.group)
async def unmute_user(_, message: types.Message):
    """Unmute a user"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>Only admins can unmute users.</b>")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except Exception:
            return await message.reply_text("<b>User not found.</b>")
    else:
        return await message.reply_text("<b>Reply to a user or provide username/ID.</b>")

    try:
        await app.restrict_chat_member(
            message.chat.id,
            user.id,
            types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.reply_text(f"<b>Unmuted: {user.mention}</b>")
    except Exception as e:
        await message.reply_text(f"<b>Failed:</b> {e}")


# ─── PURGE ───────────────────────────────────────────────────────────────────

@app.on_message(filters.command(["purge"]) & filters.group)
async def purge_messages(_, message: types.Message):
    """Purge messages from replied message to current"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>Only admins can purge messages.</b>")

    if not message.reply_to_message:
        return await message.reply_text("<b>Reply to the message you want to start purging from.</b>")

    start_id = message.reply_to_message.id
    end_id = message.id
    msg_ids = list(range(start_id, end_id + 1))

    deleted = 0
    for i in range(0, len(msg_ids), 100):
        chunk = msg_ids[i:i+100]
        try:
            await app.delete_messages(message.chat.id, chunk)
            deleted += len(chunk)
        except Exception:
            pass

    sent = await app.send_message(message.chat.id, f"<b>Purged {deleted} messages.</b>")
    import asyncio
    await asyncio.sleep(3)
    try:
        await sent.delete()
    except Exception:
        pass


# ─── USER INFO ───────────────────────────────────────────────────────────────

@app.on_message(filters.command(["userinfo", "info", "whois"]) & ~app.bl_users)
async def user_info(_, message: types.Message):
    """Get user information"""
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except Exception:
            return await message.reply_text("<b>User not found.</b>")
    else:
        user = message.from_user

    try:
        member = await app.get_chat_member(message.chat.id, user.id)
        status = str(member.status).split(".")[-1].title()
    except Exception:
        status = "Unknown"

    text = (
        f"<b>User Info</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"<b>Name:</b> {user.first_name} {user.last_name or ''}\n"
        f"<b>Username:</b> @{user.username or 'None'}\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Bot:</b> {'Yes' if user.is_bot else 'No'}\n"
        f"<b>Premium:</b> {'Yes' if getattr(user, 'is_premium', False) else 'No'}"
    )
    await message.reply_text(text)


# ─── GROUP INFO ──────────────────────────────────────────────────────────────

@app.on_message(filters.command(["groupinfo", "chatinfo"]) & filters.group & ~app.bl_users)
async def group_info(_, message: types.Message):
    """Get group information"""
    chat = message.chat
    try:
        count = await app.get_chat_members_count(chat.id)
    except Exception:
        count = "Unknown"

    text = (
        f"<b>Group Info</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"<b>Name:</b> {chat.title}\n"
        f"<b>ID:</b> <code>{chat.id}</code>\n"
        f"<b>Username:</b> @{chat.username or 'Private'}\n"
        f"<b>Members:</b> {count}\n"
        f"<b>Type:</b> {str(chat.type).split('.')[-1].title()}"
    )
    await message.reply_text(text)
