# AI Moderation Plugin
# Features: Auto delete bad words, warn system, auto ban after 3 warnings

import asyncio
from pyrogram import filters, types, enums
from pyrogram.errors import UserAdminInvalid, ChatAdminRequired

from anony import app, db
from anony.core.ai import ai_check_text

# In-memory warning store: {chat_id: {user_id: warn_count}}
_warnings: dict[int, dict[int, int]] = {}

MAX_WARNINGS = 3


def get_warnings(chat_id: int, user_id: int) -> int:
    return _warnings.get(chat_id, {}).get(user_id, 0)


def add_warning(chat_id: int, user_id: int) -> int:
    if chat_id not in _warnings:
        _warnings[chat_id] = {}
    _warnings[chat_id][user_id] = _warnings[chat_id].get(user_id, 0) + 1
    return _warnings[chat_id][user_id]


def reset_warnings(chat_id: int, user_id: int):
    if chat_id in _warnings and user_id in _warnings[chat_id]:
        _warnings[chat_id][user_id] = 0


async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]
    except Exception:
        return False


@app.on_message(
    filters.group
    & filters.text
    & ~filters.bot
    & ~filters.service
)
async def moderation_handler(_, message: types.Message):
    """Auto-moderate bad words in group messages"""
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Skip admins
    if await is_admin(chat_id, user_id):
        return

    text = message.text or ""
    if not text.strip():
        return

    # Check for bad content
    is_bad, reason = await ai_check_text(text)
    if not is_bad:
        return

    # Delete the message
    try:
        await message.delete()
    except Exception:
        pass

    # Add warning
    warn_count = add_warning(chat_id, user_id)
    user_mention = message.from_user.mention
    remaining = MAX_WARNINGS - warn_count

    if warn_count >= MAX_WARNINGS:
        # Ban the user
        reset_warnings(chat_id, user_id)
        try:
            await app.ban_chat_member(chat_id, user_id)
            warn_msg = await app.send_message(
                chat_id,
                f"🚫 <b>{user_mention} has been banned!</b>\n\n"
                f"<i>Reason: Repeated use of inappropriate language ({MAX_WARNINGS} warnings reached)</i>",
            )
        except (UserAdminInvalid, ChatAdminRequired):
            warn_msg = await app.send_message(
                chat_id,
                f"⚠️ <b>{user_mention}</b> — Could not ban (insufficient permissions).\n"
                f"<i>Please make me admin with ban permissions.</i>",
            )
        except Exception:
            warn_msg = await app.send_message(
                chat_id,
                f"🚫 <b>{user_mention}</b> — Ban failed. Check my permissions.",
            )
    else:
        # Send warning
        warn_msg = await app.send_message(
            chat_id,
            f"⚠️ <b>Warning {warn_count}/{MAX_WARNINGS} — {user_mention}</b>\n\n"
            f"<i>Your message was deleted for inappropriate language.</i>\n"
            f"<b>{remaining} warning(s) left before ban.</b>",
        )

    # Auto delete warning message after 10 seconds
    await asyncio.sleep(10)
    try:
        await warn_msg.delete()
    except Exception:
        pass


@app.on_message(filters.command(["warns"]) & filters.group)
async def check_warns(_, message: types.Message):
    """Check warnings for a user"""
    chat_id = message.chat.id

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except Exception:
            return await message.reply_text("<b>User not found.</b>")
    else:
        return await message.reply_text("<b>Reply to a user or provide username/ID.</b>")

    warn_count = get_warnings(chat_id, user.id)
    await message.reply_text(
        f"<b>Warnings for {user.mention}:</b>\n"
        f"<code>{warn_count}/{MAX_WARNINGS}</code>"
    )


@app.on_message(filters.command(["resetwarn", "clearwarn"]) & filters.group)
async def reset_warn(_, message: types.Message):
    """Reset warnings for a user (admin only)"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("<b>Only admins can reset warnings.</b>")

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await app.get_users(message.command[1])
        except Exception:
            return await message.reply_text("<b>User not found.</b>")
    else:
        return await message.reply_text("<b>Reply to a user or provide username/ID.</b>")

    reset_warnings(message.chat.id, user.id)
    await message.reply_text(f"<b>Warnings reset for {user.mention}.</b>")
