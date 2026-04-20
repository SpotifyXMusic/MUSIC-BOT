from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from anony.helpers.admins import can_control
from anony.helpers.queue import queue
from anony.helpers.youtube import download_audio, download_video


def cm():
    from anony.core import call_manager
    return call_manager


def player_btns(paused=False):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause" if not paused else "▶ Resume",
                                 callback_data="pause" if not paused else "resume"),
            InlineKeyboardButton("⏭ Skip",  callback_data="skip"),
            InlineKeyboardButton("⏹ Stop",  callback_data="stop"),
        ],
        [
            InlineKeyboardButton("📋 Queue",  callback_data="queue"),
            InlineKeyboardButton("🔁 Loop",   callback_data="loop"),
            InlineKeyboardButton("🎵 Lyrics", callback_data="lyrics"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close")],
    ])


@Client.on_message(filters.command("pause") & filters.group)
async def pause_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth users.**")
    call = cm()
    if not call.is_active(cid): return await message.reply_text("**Nothing playing.**")
    if call.is_paused(cid): return await message.reply_text("**Already paused.**")
    if await call.pause(cid):
        await message.reply_text("**Paused.**", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("▶ Resume", callback_data="resume"),
            InlineKeyboardButton("⏹ Stop",  callback_data="stop"),
        ]]))
    else: await message.reply_text("**Failed.**")


@Client.on_message(filters.command("resume") & filters.group)
async def resume_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth users.**")
    call = cm()
    if not call.is_active(cid): return await message.reply_text("**Nothing playing.**")
    if await call.resume(cid):
        t = queue.get_current(cid)
        await message.reply_text(
            f"**Resumed:** {t.title if t else 'Unknown'}",
            reply_markup=player_btns(False)
        )
    else: await message.reply_text("**Failed.**")


@Client.on_message(filters.command("skip") & filters.group)
async def skip_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth users.**")
    call = cm()
    if not call.is_active(cid): return await message.reply_text("**Nothing playing.**")
    nxt = queue.next(cid)
    if not nxt:
        await call.stop(cid)
        return await message.reply_text("**Queue ended.**")
    status = await message.reply_text("**Skipping...**")
    try:
        fp = await (download_video(nxt.url) if nxt.is_video else download_audio(nxt.url))
        if fp:
            nxt.file_path = fp
            await call.join_and_play(cid, fp, nxt.is_video)
            await status.edit(
                f"**Now Playing:** {nxt.title}\n`{nxt.duration}` | {nxt.requested_by_name}",
                reply_markup=player_btns()
            )
        else: await status.edit("**Download failed.**")
    except Exception as e: await status.edit(f"**Error:** `{str(e)[:150]}`")


@Client.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth users.**")
    await cm().stop(cid)
    queue.clear(cid)
    await message.reply_text("**Stopped. Queue cleared.**")


@Client.on_message(filters.command("seek") & filters.group)
async def seek_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth users.**")
    if len(message.command) < 2: return await message.reply_text("**Usage:** `/seek <seconds>`")
    try: s = int(message.command[1])
    except: return await message.reply_text("**Invalid number.**")
    ok = await cm().seek(cid, s)
    await message.reply_text(f"**Seeked {s}s.**" if ok else "**Failed.**")


@Client.on_message(filters.command("seekback") & filters.group)
async def seekback_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth users.**")
    if len(message.command) < 2: return await message.reply_text("**Usage:** `/seekback <seconds>`")
    try: s = int(message.command[1])
    except: return await message.reply_text("**Invalid.**")
    ok = await cm().seek(cid, -abs(s))
    await message.reply_text(f"**Seeked back {s}s.**" if ok else "**Failed.**")


@Client.on_message(filters.command("mute") & filters.group)
async def mute_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id): return await message.reply_text("**Only admins.**")
    ok = await cm().mute(cid)
    await message.reply_text("**Muted.**" if ok else "**Failed.**")


@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id): return await message.reply_text("**Only admins.**")
    ok = await cm().unmute(cid)
    await message.reply_text("**Unmuted.**" if ok else "**Failed.**")


@Client.on_message(filters.command("loop") & filters.group)
async def loop_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id): return await message.reply_text("**Only admins.**")
    on = queue.toggle_loop(cid)
    await message.reply_text(f"**Loop {'ON' if on else 'OFF'}.**")


@Client.on_message(filters.command("repeat") & filters.group)
async def repeat_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id): return await message.reply_text("**Only admins.**")
    on = queue.toggle_repeat(cid)
    await message.reply_text(f"**Repeat {'ON' if on else 'OFF'}.**")


# ── CALLBACKS ────────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^(pause|resume|skip|stop|loop|repeat|close|queue|lyrics)$"))
async def ctrl_cb(client: Client, cb: CallbackQuery):
    action = cb.data
    cid = cb.message.chat.id
    uid = cb.from_user.id
    call = cm()

    if action == "close":
        await cb.message.delete(); return

    if action == "queue":
        text = queue.format_queue(cid)
        await cb.answer()
        await cb.message.reply_text(text); return

    if action == "lyrics":
        t = queue.get_current(cid)
        if not t: return await cb.answer("Nothing playing!", show_alert=True)
        await cb.answer("Fetching lyrics...")
        from anony.helpers.lyrics import get_lyrics, chunk_lyrics
        lyr = await get_lyrics(t.title, t.channel)
        if lyr:
            for chunk in chunk_lyrics(lyr):
                await cb.message.reply_text(f"**{t.title}**\n```\n{chunk}\n```")
        else:
            await cb.message.reply_text(f"**Lyrics not found for:** `{t.title}`")
        return

    if not await can_control(client, cid, uid):
        return await cb.answer("Only admins can control!", show_alert=True)

    if action == "pause":
        await call.pause(cid); await cb.answer("Paused!")
    elif action == "resume":
        await call.resume(cid); await cb.answer("Resumed!")
    elif action == "stop":
        await call.stop(cid); queue.clear(cid)
        await cb.answer("Stopped!")
        await cb.message.edit("**Stream stopped.**")
    elif action == "skip":
        nxt = queue.next(cid)
        if not nxt:
            await call.stop(cid)
            await cb.answer("Queue ended!", show_alert=True)
            await cb.message.edit("**Queue ended.**")
        else:
            await cb.answer("Skipping...")
            try:
                fp = await (download_video(nxt.url) if nxt.is_video else download_audio(nxt.url))
                if fp:
                    nxt.file_path = fp
                    await call.join_and_play(cid, fp, nxt.is_video)
                    await cb.message.edit(
                        f"**Now Playing:** {nxt.title}\n`{nxt.duration}`",
                        reply_markup=player_btns()
                    )
            except Exception: pass
    elif action == "loop":
        on = queue.toggle_loop(cid); await cb.answer(f"Loop {'ON' if on else 'OFF'}")
    elif action == "repeat":
        on = queue.toggle_repeat(cid); await cb.answer(f"Repeat {'ON' if on else 'OFF'}")
