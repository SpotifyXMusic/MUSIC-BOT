"""
Broadcast Plugin
/broadcast - Send message to all chats/users
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

from anony.helpers.admins import is_sudo
from anony.core.mongo import get_all_chats, get_user_count, get_chat_count


@Client.on_message(filters.command("broadcast"))
async def broadcast_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only command.**")

    if not message.reply_to_message:
        return await message.reply_text(
            "**Usage:** Reply to a message with `/broadcast`\n\n"
            "**Flags:**\n"
            "`-nochat` - Exclude groups from broadcast\n"
            "`-user` - Include users in broadcast\n"
            "`-copy` - Remove forwarded tag from message\n\n"
            "**Example:** `/broadcast -user -copy`"
        )

    args = message.command[1:] if len(message.command) > 1 else []
    no_chat = "-nochat" in args
    include_user = "-user" in args
    copy_msg = "-copy" in args

    status_msg = await message.reply_text("**Broadcasting...**")

    sent = 0
    failed = 0
    target_ids = []

    if not no_chat:
        chats = await get_all_chats()
        target_ids.extend(chats)

    if include_user:
        from anony.core.mongo import users_col
        user_docs = await users_col.find({}, {"user_id": 1}).to_list(length=None)
        target_ids.extend([d["user_id"] for d in user_docs])

    target_ids = list(set(target_ids))

    for target_id in target_ids:
        try:
            if copy_msg:
                await message.reply_to_message.copy(target_id)
            else:
                await message.reply_to_message.forward(target_id)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # avoid flood

    await status_msg.edit(
        f"**Broadcast Complete**\n\n"
        f"**Sent:** `{sent}`\n"
        f"**Failed:** `{failed}`\n"
        f"**Total Targets:** `{len(target_ids)}`"
    )
