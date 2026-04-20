from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from anony.helpers.admins import is_admin, is_sudo
from anony.helpers.lyrics import get_lyrics, chunk_lyrics
from anony.helpers.queue import queue
from anony.core.mongo import get_history, get_top_songs, get_setting, set_setting


# ─── LYRICS ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("lyrics") & filters.group)
async def lyrics_cmd(client: Client, message: Message):
    if len(message.command) > 1:
        song = " ".join(message.command[1:])
    else:
        t = queue.get_current(message.chat.id)
        if not t: return await message.reply_text("**Nothing playing.**\nUse: `/lyrics <song name>`")
        song = t.title
    status = await message.reply_text(f"**Searching lyrics for:** `{song}`")
    lyr = await get_lyrics(song)
    if not lyr:
        return await status.edit(f"**Lyrics not found for:** `{song}`")
    await status.delete()
    chunks = chunk_lyrics(lyr)
    for i, chunk in enumerate(chunks):
        hdr = f"**{song[:40]}**\n" if i == 0 else ""
        ftr = f"\n`Part {i+1}/{len(chunks)}`" if len(chunks) > 1 else ""
        await message.reply_text(f"{hdr}```\n{chunk}\n```{ftr}")


# ─── HISTORY ────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("history") & filters.group)
async def history_cmd(client: Client, message: Message):
    docs = await get_history(message.chat.id, 10)
    if not docs: return await message.reply_text("**No history yet.**")
    from datetime import datetime
    text = "**Recently Played:**\n\n"
    for i, d in enumerate(docs, 1):
        dt = datetime.fromtimestamp(d.get("ts", 0)).strftime("%d/%m %H:%M")
        text += f"`{i}.` **{d['title'][:35]}**\n   `{d['duration']}` | {dt}\n\n"
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🏆 Top Songs", callback_data="topsongs"),
        InlineKeyboardButton("❌ Close", callback_data="close"),
    ]]))


@Client.on_message(filters.command("topsongs") & filters.group)
async def topsongs_cmd(client: Client, message: Message):
    docs = await get_top_songs(message.chat.id, 10)
    if not docs: return await message.reply_text("**No songs played yet.**")
    medals = ["🥇", "🥈", "🥉"]
    text = "**Top Songs:**\n\n"
    for i, d in enumerate(docs, 1):
        m = medals[i-1] if i <= 3 else f"`{i}.`"
        text += f"{m} **{d['_id'][:35]}**\n   Played `{d['count']}` times\n\n"
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("📜 History", callback_data="history"),
        InlineKeyboardButton("❌ Close", callback_data="close"),
    ]]))


@Client.on_callback_query(filters.regex("^(topsongs|history)$"))
async def hist_cb(client: Client, cb: CallbackQuery):
    if cb.data == "topsongs": await topsongs_cmd(client, cb.message)
    else: await history_cmd(client, cb.message)
    await cb.answer()


# ─── SETTINGS ────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("settings") & filters.group)
async def settings_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await is_admin(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins.**")
    auto_leave = await get_setting(cid, "auto_leave", True)
    vote_skip  = await get_setting(cid, "vote_skip",  False)
    announce   = await get_setting(cid, "announce",   True)
    await message.reply_text(
        "**Group Settings**\nTap to toggle:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Auto Leave: {'✅ ON' if auto_leave else '❌ OFF'}", callback_data="set_auto_leave")],
            [InlineKeyboardButton(f"Vote Skip: {'✅ ON' if vote_skip else '❌ OFF'}",   callback_data="set_vote_skip")],
            [InlineKeyboardButton(f"Announce: {'✅ ON' if announce else '❌ OFF'}",     callback_data="set_announce")],
            [InlineKeyboardButton("❌ Close", callback_data="close")],
        ])
    )


@Client.on_callback_query(filters.regex("^set_"))
async def settings_cb(client: Client, cb: CallbackQuery):
    cid = cb.message.chat.id
    if not await is_admin(client, cid, cb.from_user.id):
        return await cb.answer("Only admins!", show_alert=True)
    key = cb.data.replace("set_", "")
    curr = await get_setting(cid, key, True)
    await set_setting(cid, key, not curr)
    await cb.answer(f"{key.replace('_',' ').title()}: {'ON' if not curr else 'OFF'}")
    auto_leave = await get_setting(cid, "auto_leave", True)
    vote_skip  = await get_setting(cid, "vote_skip",  False)
    announce   = await get_setting(cid, "announce",   True)
    await cb.message.edit_reply_markup(InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Auto Leave: {'✅ ON' if auto_leave else '❌ OFF'}", callback_data="set_auto_leave")],
        [InlineKeyboardButton(f"Vote Skip: {'✅ ON' if vote_skip else '❌ OFF'}",   callback_data="set_vote_skip")],
        [InlineKeyboardButton(f"Announce: {'✅ ON' if announce else '❌ OFF'}",     callback_data="set_announce")],
        [InlineKeyboardButton("❌ Close", callback_data="close")],
    ]))


# ─── LANGUAGE ────────────────────────────────────────────────────────────────

LANGS = {"en": "English", "hi": "Hindi", "ar": "Arabic", "de": "German",
         "es": "Spanish", "fr": "French", "ja": "Japanese", "ru": "Russian",
         "tr": "Turkish", "zh": "Chinese", "pt": "Portuguese"}


@Client.on_message(filters.command("lang") & filters.group)
async def lang_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await is_admin(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins.**")
    curr = await get_setting(cid, "language", "en")
    btns = []
    row = []
    for code, name in LANGS.items():
        mark = " ✓" if code == curr else ""
        row.append(InlineKeyboardButton(f"{name}{mark}", callback_data=f"lang_{code}"))
        if len(row) == 3: btns.append(row); row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton("❌ Close", callback_data="close")])
    await message.reply_text(f"**Select Language**\nCurrent: `{LANGS.get(curr,'English')}`",
                              reply_markup=InlineKeyboardMarkup(btns))


@Client.on_callback_query(filters.regex("^lang_"))
async def lang_cb(client: Client, cb: CallbackQuery):
    cid = cb.message.chat.id
    if not await is_admin(client, cid, cb.from_user.id):
        return await cb.answer("Only admins!", show_alert=True)
    code = cb.data.split("_")[1]
    if code not in LANGS: return await cb.answer("Invalid.", show_alert=True)
    await set_setting(cid, "language", code)
    await cb.answer(f"Language set to {LANGS[code]}!")
    await cb.message.edit(f"**Language set to {LANGS[code]}.**")
