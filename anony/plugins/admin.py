import time, psutil, os, sys, asyncio, io, traceback
from pyrogram import Client, filters
from pyrogram.types import Message
from anony.helpers.admins import is_sudo
from anony.core.mongo import get_user_count, get_chat_count, get_plays, get_all_chats


@Client.on_message(filters.command("ping"))
async def ping_cmd(client: Client, message: Message):
    s = time.time()
    msg = await message.reply_text("Pinging...")
    ms = round((time.time() - s) * 1000, 2)
    proc = psutil.Process()
    mem = proc.memory_info().rss / (1024 * 1024)
    cpu = psutil.cpu_percent(interval=0.5)
    await msg.edit(f"**Pong!**\n\nLatency: `{ms}ms`\nCPU: `{cpu}%`\nRAM: `{mem:.1f} MB`")


@Client.on_message(filters.command("stats"))
async def stats_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id):
        return await message.reply_text("**Sudo only.**")
    users = await get_user_count()
    chats = await get_chat_count()
    plays = await get_plays()
    from anony.core import call_manager
    active = call_manager.active_count()
    proc = psutil.Process()
    mem = proc.memory_info().rss / (1024 * 1024)
    cpu = psutil.cpu_percent(interval=0.5)
    h, rem = divmod(int(time.time() - proc.create_time()), 3600)
    m, s = divmod(rem, 60)
    await message.reply_text(
        f"**Bot Stats**\n\nUsers: `{users}`\nChats: `{chats}`\n"
        f"Total Plays: `{plays}`\nActive Calls: `{active}`\n\n"
        f"CPU: `{cpu}%` | RAM: `{mem:.1f}MB`\nUptime: `{h}h {m}m {s}s`"
    )


@Client.on_message(filters.command("ac"))
async def ac_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id): return await message.reply_text("**Sudo only.**")
    from anony.core import call_manager
    await message.reply_text(f"**Active Calls:** `{call_manager.active_count()}`")


@Client.on_message(filters.command("activevc"))
async def activevc_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id): return await message.reply_text("**Sudo only.**")
    from anony.core import call_manager
    from anony.helpers.queue import queue
    chats = call_manager.active_chats()
    if not chats: return await message.reply_text("**No active calls.**")
    text = f"**Active: `{len(chats)}`**\n\n"
    for cid in chats:
        try:
            chat = await client.get_chat(cid)
            t = queue.get_current(cid)
            text += f"**{chat.title}**\n  {t.title[:30] if t else '?'}\n\n"
        except: text += f"`{cid}`\n\n"
    await message.reply_text(text)


@Client.on_message(filters.command("broadcast"))
async def broadcast_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id): return await message.reply_text("**Sudo only.**")
    if not message.reply_to_message:
        return await message.reply_text("**Reply to a message.**\nFlags: `-nochat` `-user` `-copy`")
    args = message.command[1:] if len(message.command) > 1 else []
    no_chat = "-nochat" in args
    inc_user = "-user" in args
    do_copy = "-copy" in args
    status = await message.reply_text("**Broadcasting...**")
    sent = failed = 0
    targets = []
    if not no_chat: targets.extend(await get_all_chats())
    if inc_user:
        from anony.core.mongo import users_col
        docs = await users_col.find({}, {"user_id": 1}).to_list(length=None)
        targets.extend([d["user_id"] for d in docs])
    targets = list(set(targets))
    for tid in targets:
        try:
            if do_copy: await message.reply_to_message.copy(tid)
            else: await message.reply_to_message.forward(tid)
            sent += 1
        except: failed += 1
        await asyncio.sleep(0.05)
    await status.edit(f"**Broadcast Done**\nSent: `{sent}` | Failed: `{failed}`")


@Client.on_message(filters.command("eval"))
async def eval_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id): return await message.reply_text("**Sudo only.**")
    code = " ".join(message.command[1:]) if len(message.command) > 1 else (
        message.reply_to_message.text if message.reply_to_message else None)
    if not code: return await message.reply_text("**Provide code.**")
    try:
        exec_globals = {"client": client, "message": message, "asyncio": asyncio}
        old = sys.stdout; sys.stdout = io.StringIO()
        try:
            exec(f"async def _e():\n" + "\n".join(f"    {l}" for l in code.split("\n")), exec_globals)
            result = await exec_globals["_e"]()
        finally:
            out = sys.stdout.getvalue(); sys.stdout = old
        reply = ""
        if out: reply += f"**Output:**\n```\n{out}\n```\n"
        if result is not None: reply += f"**Result:**\n```\n{result}\n```"
        await message.reply_text(reply or "**Done. No output.**")
    except Exception:
        await message.reply_text(f"**Error:**\n```\n{traceback.format_exc()[:2000]}\n```")


@Client.on_message(filters.command("logs"))
async def logs_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id): return await message.reply_text("**Sudo only.**")
    if os.path.exists("bot.log"): await message.reply_document("bot.log")
    else: await message.reply_text("**No log file.**")


@Client.on_message(filters.command("restart"))
async def restart_cmd(client: Client, message: Message):
    if not await is_sudo(message.from_user.id): return await message.reply_text("**Sudo only.**")
    await message.reply_text("**Restarting...**")
    os.execv(sys.executable, [sys.executable] + sys.argv)
