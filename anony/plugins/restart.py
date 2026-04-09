"""
Restart Plugin - /restart command
"""

import os
import sys
from pyrogram import Client, filters
from pyrogram.types import Message

from anony.helpers.admins import is_sudo


@Client.on_message(filters.command("restart"))
async def restart_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only command.**")

    await message.reply_text("**Restarting bot...**")
    os.execv(sys.executable, [sys.executable] + sys.argv)
