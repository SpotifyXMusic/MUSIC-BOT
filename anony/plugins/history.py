"""
History & Top Songs Plugin
/history /topsongs /toprequests
"""

import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from anony.core.mongo import get_history, get_top_songs, get_top_requesters


@Client.on_message(filters.command("history") & filters.group)
async def history_command(client: Client, message: Message):
    chat_id = message.chat.id
    docs = await get_history(chat_id, limit=10)

    if not docs:
        return await message.reply_text(
            "**No history yet.**\nPlay some songs first!"
        )

    text = "**Recently Played** (last 10)\n\n"
    for i, doc in enumerate(docs, 1):
        ts = doc.get("timestamp", 0)
        from datetime import datetime
        dt = datetime.fromtimestamp(ts).strftime("%d/%m %H:%M") if ts else "?"
        text += f"`{i}.` **{doc['title'][:40]}**\n"
        text += f"    `{doc['duration']}` | {dt}\n\n"

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏆 Top Songs", callback_data="topsongs"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ]])
    )


@Client.on_message(filters.command("topsongs") & filters.group)
async def topsongs_command(client: Client, message: Message):
    chat_id = message.chat.id
    docs = await get_top_songs(chat_id, limit=10)

    if not docs:
        return await message.reply_text("**No songs played yet in this group.**")

    text = "**Top Songs in This Group**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, doc in enumerate(docs, 1):
        medal = medals[i-1] if i <= 3 else f"`{i}.`"
        text += f"{medal} **{doc['_id'][:40]}**\n"
        text += f"    Played `{doc['count']}` times\n\n"

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📜 History", callback_data="history"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ]])
    )


@Client.on_message(filters.command("toprequests") & filters.group)
async def toprequests_command(client: Client, message: Message):
    chat_id = message.chat.id
    docs = await get_top_requesters(chat_id, limit=10)

    if not docs:
        return await message.reply_text("**No data yet.**")

    text = "**Top Requesters in This Group**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, doc in enumerate(docs, 1):
        medal = medals[i-1] if i <= 3 else f"`{i}.`"
        uid = doc["_id"]
        try:
            user = await client.get_users(uid)
            name = user.first_name[:25]
        except Exception:
            name = f"User {uid}"
        text += f"{medal} **{name}**\n    `{doc['count']}` songs requested\n\n"

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Close", callback_data="close")
    ]]))


@Client.on_callback_query(filters.regex("^(topsongs|history)$"))
async def history_callbacks(client: Client, callback):
    if callback.data == "topsongs":
        await topsongs_command(client, callback.message)
    else:
        await history_command(client, callback.message)
    await callback.answer()
