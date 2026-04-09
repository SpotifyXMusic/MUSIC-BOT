"""
Eval, Logs, Restart Plugin
/eval /logs /logger /restart
"""

import io
import os
import sys
import asyncio
import logging
import traceback
from pyrogram import Client, filters
from pyrogram.types import Message

from anony.helpers.admins import is_sudo, is_owner

logger = logging.getLogger(__name__)
_logger_enabled = False


@Client.on_message(filters.command("eval"))
async def eval_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only command.**")

    if len(message.command) < 2:
        if not message.reply_to_message:
            return await message.reply_text("**Usage:** `/eval <code>`")
        code = message.reply_to_message.text
    else:
        code = message.text.split(None, 1)[1]

    try:
        exec_globals = {"client": client, "message": message, "asyncio": asyncio}
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            exec(f"async def _eval():\n" + "\n".join(f"    {line}" for line in code.split("\n")), exec_globals)
            result = await exec_globals["_eval"]()
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        reply = ""
        if output:
            reply += f"**Output:**\n```\n{output}\n```\n"
        if result is not None:
            reply += f"**Result:**\n```\n{result}\n```"
        if not reply:
            reply = "**Executed successfully. No output.**"

        await message.reply_text(reply[:4000])

    except Exception:
        error = traceback.format_exc()
        await message.reply_text(f"**Error:**\n```\n{error[:3000]}\n```")


@Client.on_message(filters.command("logs"))
async def logs_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only command.**")

    if os.path.exists("bot.log"):
        await message.reply_document("bot.log", caption="**Bot Log File**")
    else:
        await message.reply_text("**No log file found.**")


@Client.on_message(filters.command("logger"))
async def logger_command(client: Client, message: Message):
    global _logger_enabled
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only command.**")

    if len(message.command) < 2:
        status = "ON" if _logger_enabled else "OFF"
        return await message.reply_text(f"**Logger is currently:** `{status}`")

    arg = message.command[1].lower()
    if arg == "on":
        _logger_enabled = True
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
        )
        await message.reply_text("**Logger enabled.** Logs will be saved to `bot.log`.")
    elif arg == "off":
        _logger_enabled = False
        await message.reply_text("**Logger disabled.**")
    else:
        await message.reply_text("**Usage:** `/logger on` or `/logger off`")


@Client.on_message(filters.command("restart"))
async def restart_command(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo-only command.**")

    await message.reply_text("**Restarting bot...**")
    os.execv(sys.executable, [sys.executable] + sys.argv)
