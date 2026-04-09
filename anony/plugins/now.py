"""
Now Playing Plugin with Progress Bar
/now - Shows current song with visual progress bar
"""

import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from anony.helpers.queue import queue
from anony.helpers.thumbnail import make_progress_text, generate_now_playing_thumb


_start_times: dict = {}  # chat_id -> unix timestamp when current song started


def set_play_start(chat_id: int):
    _start_times[chat_id] = time.time()


def get_elapsed(chat_id: int) -> int:
    start = _start_times.get(chat_id, time.time())
    return int(time.time() - start)


@Client.on_message(filters.command(["now", "np"]) & filters.group)
async def now_playing(client: Client, message: Message):
    chat_id = message.chat.id
    track = queue.get_current(chat_id)

    if not track:
        return await message.reply_text("**Nothing is playing right now.**")

    try:
        from anony.core import call_manager
        paused = call_manager.is_paused(chat_id)
    except Exception:
        paused = False

    elapsed_s = get_elapsed(chat_id)
    total_s = track.duration_s or 300
    pct = min(elapsed_s / total_s, 1.0)

    progress = make_progress_text(elapsed_s, total_s, width=22)
    status = "⏸ Paused" if paused else "▶ Playing"
    mode = "🎬 Video" if track.is_video else "🎵 Audio"

    # Try thumbnail card
    try:
        thumb_path = await generate_now_playing_thumb(
            title=track.title,
            channel=track.channel,
            duration=track.duration,
            requested_by=track.requested_by_name,
            thumbnail_url=track.thumbnail,
            current_pct=pct,
            is_paused=paused,
            queue_pos=queue.get_current_index(chat_id) + 1,
            total_queue=queue.queue_length(chat_id),
            mode="VIDEO" if track.is_video else "AUDIO",
        )
        caption = (
            f"**{status}** | {mode}\n\n"
            f"**{track.title}**\n"
            f"{progress}\n\n"
            f"**Channel:** {track.channel}\n"
            f"**Requested by:** {track.requested_by_name}\n"
            f"**Queue:** {queue.get_current_index(chat_id)+1}/{queue.queue_length(chat_id)}"
        )
        await message.reply_photo(
            photo=thumb_path,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏸ Pause" if not paused else "▶ Resume",
                                         callback_data="pause" if not paused else "resume"),
                    InlineKeyboardButton("⏭ Skip", callback_data="skip"),
                    InlineKeyboardButton("⏹ Stop", callback_data="stop"),
                ],
                [
                    InlineKeyboardButton("📋 Queue",  callback_data="queue"),
                    InlineKeyboardButton("🎵 Lyrics", callback_data="lyrics"),
                    InlineKeyboardButton("🎚 Effects", callback_data="effects"),
                ],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
    except Exception:
        # Fallback text
        await message.reply_text(
            f"**{status}** | {mode}\n\n"
            f"**{track.title}**\n"
            f"{progress}\n\n"
            f"Channel: {track.channel}\n"
            f"Requested by: {track.requested_by_name}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏸ Pause" if not paused else "▶ Resume",
                                         callback_data="pause" if not paused else "resume"),
                    InlineKeyboardButton("⏭ Skip", callback_data="skip"),
                    InlineKeyboardButton("⏹ Stop", callback_data="stop"),
                ],
                [
                    InlineKeyboardButton("📋 Queue",  callback_data="queue"),
                    InlineKeyboardButton("🎵 Lyrics", callback_data="lyrics"),
                ],
            ])
        )
