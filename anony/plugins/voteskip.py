from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from anony.helpers.flood import add_vote, get_votes, clear_votes
from anony.helpers.queue import queue
from anony.core.mongo import get_setting
from config import Config


def cm():
    from anony.core import call_manager
    return call_manager


@Client.on_message(filters.command("voteskip") & filters.group)
async def voteskip_cmd(client: Client, message: Message):
    cid, uid = message.chat.id, message.from_user.id
    call = cm()
    if not call.is_active(cid): return await message.reply_text("**Nothing playing.**")
    vote_skip_on = await get_setting(cid, "vote_skip", False)
    if not vote_skip_on:
        return await message.reply_text("**Vote Skip is disabled.**\nEnable in `/settings`.")
    voters = add_vote(cid, uid)
    try:
        chat = await client.get_chat(cid)
        total = chat.members_count or 10
    except: total = 10
    needed = max(2, int(total * 51 / 100))
    current = len(voters)
    t = queue.get_current(cid)
    name = t.title[:40] if t else "current song"
    if current >= needed:
        clear_votes(cid)
        nxt = queue.next(cid)
        if not nxt:
            await call.stop(cid)
            return await message.reply_text(f"**Vote Skip Passed!** (`{current}/{needed}`)\nQueue ended.")
        from anony.helpers.youtube import download_audio, download_video
        status = await message.reply_text(f"**Vote Skip Passed!** `{current}/{needed}` — Skipping...")
        try:
            fp = await (download_video(nxt.url) if nxt.is_video else download_audio(nxt.url))
            if fp:
                nxt.file_path = fp
                await call.join_and_play(cid, fp, nxt.is_video)
                await status.edit(f"**Skipped!**\nNow Playing: {nxt.title}")
        except Exception as e: await status.edit(f"**Error:** `{str(e)[:100]}`")
    else:
        await message.reply_text(
            f"**Vote Skip** — `{name}`\nVotes: `{current}/{needed}`\nNeed `{needed-current}` more!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"👍 Vote ({current}/{needed})", callback_data=f"vs_{cid}")
            ]])
        )


@Client.on_callback_query(filters.regex(r"^vs_"))
async def vs_cb(client: Client, cb: CallbackQuery):
    cid = cb.message.chat.id
    uid = cb.from_user.id
    voters = add_vote(cid, uid)
    try:
        chat = await client.get_chat(cid)
        total = chat.members_count or 10
    except: total = 10
    needed = max(2, int(total * 51 / 100))
    current = len(voters)
    await cb.answer(f"Voted! {current}/{needed}")
    if current >= needed:
        clear_votes(cid)
        call = cm()
        nxt = queue.next(cid)
        if not nxt:
            await call.stop(cid)
            await cb.message.edit(f"**Vote Skip Passed!** Queue ended.")
        else:
            await cb.message.edit(f"**Vote Skip Passed!** `{current}/{needed}` — Skipping...")
    else:
        await cb.message.edit(
            f"**Vote Skip**\nVotes: `{current}/{needed}` | Need `{needed-current}` more",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"👍 Vote ({current}/{needed})", callback_data=f"vs_{cid}")
            ]])
        )
