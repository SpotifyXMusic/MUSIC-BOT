"""
Lyrics Plugin
/lyrics - Get lyrics of current or searched song
No API key needed - uses free lyrics.ovh
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.lyrics import get_lyrics, chunk_lyrics
from anony.helpers.queue import queue


@Client.on_message(filters.command("lyrics") & filters.group)
async def lyrics_command(client: Client, message: Message):
    chat_id = message.chat.id

    if len(message.command) > 1:
        song_name = " ".join(message.command[1:])
    else:
        track = queue.get_current(chat_id)
        if not track:
            return await message.reply_text(
                "**Nothing is playing.**\n\nUse: `/lyrics <song name>`"
            )
        song_name = track.title

    status = await message.reply_text(f"**Searching lyrics for:** `{song_name}`")

    lyrics = await get_lyrics(song_name)

    if not lyrics:
        return await status.edit(
            f"**Lyrics not found for:** `{song_name}`\n\n"
            "Try: `/lyrics <artist name> - <song name>`"
        )

    await status.delete()
    chunks = chunk_lyrics(lyrics)

    for i, chunk in enumerate(chunks):
        header = f"**Lyrics: {song_name[:40]}**\n" if i == 0 else ""
        footer = f"\n\n`Part {i+1}/{len(chunks)}`" if len(chunks) > 1 else ""

        await message.reply_text(
            f"{header}```\n{chunk}\n```{footer}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]]) if i == len(chunks) - 1 else None
        )


@Client.on_callback_query(filters.regex("^lyrics$"))
async def lyrics_callback(client: Client, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    track = queue.get_current(chat_id)

    if not track:
        return await callback.answer("Nothing is playing!", show_alert=True)

    await callback.answer("Fetching lyrics...")
    lyrics = await get_lyrics(track.title, track.channel)

    if not lyrics:
        return await callback.message.reply_text(
            f"**Lyrics not found for:** `{track.title}`"
        )

    chunks = chunk_lyrics(lyrics)
    for i, chunk in enumerate(chunks):
        header = f"**Lyrics: {track.title[:40]}**\n" if i == 0 else ""
        await callback.message.reply_text(f"{header}```\n{chunk}\n```")
