"""
Play Plugin V2
/play /vplay /search /stream /playlist
With: Thumbnail cards, flood protection, history tracking, auto-leave cancel
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from anony.core.mongo import add_chat, add_user, increment_play_count, is_blacklisted, add_to_history
from anony.helpers.youtube import youtube_search, get_video_info, download_audio, download_video, is_youtube_url, format_views, fetch_playlist
from anony.helpers.queue import queue, Track
from anony.helpers.admins import can_control_stream
from anony.helpers.flood import check_flood
from anony.helpers.autoleave import cancel_leave
from anony.helpers.thumbnail import generate_now_playing_thumb


def get_call_manager():
    from anony.core import call_manager
    return call_manager


# ── BUTTONS (blue + red theme like original) ─────────────────────────────────

def player_buttons(paused: bool = False) -> InlineKeyboardMarkup:
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
            InlineKeyboardButton("🔂 Repeat", callback_data="repeat"),
        ],
        [
            InlineKeyboardButton("🎵 Lyrics", callback_data="lyrics"),
            InlineKeyboardButton("🎚 Effects", callback_data="effects"),
            InlineKeyboardButton("❌ Close",  callback_data="close"),
        ],
    ])


async def _send_now_playing(message: Message, track: Track, paused: bool = False, queue_pos: int = 1, total: int = 1):
    """Send thumbnail card + now playing message"""
    try:
        thumb_path = await generate_now_playing_thumb(
            title=track.title,
            channel=track.channel,
            duration=track.duration,
            requested_by=track.requested_by_name,
            thumbnail_url=track.thumbnail,
            current_pct=0.0,
            is_paused=paused,
            queue_pos=queue_pos,
            total_queue=total,
            mode="VIDEO" if track.is_video else "AUDIO",
        )
        caption = (
            f"**Now {'Streaming' if track.is_video else 'Playing'}**\n\n"
            f"**{track.title}**\n"
            f"**Duration:** `{track.duration}`\n"
            f"**Channel:** {track.channel}\n"
            f"**Requested by:** {track.requested_by_name}"
        )
        await message.reply_photo(
            photo=thumb_path,
            caption=caption,
            reply_markup=player_buttons(paused)
        )
    except Exception:
        # Fallback to text if thumbnail fails
        await message.reply_text(
            f"**Now Playing**\n\n**{track.title}**\n"
            f"Duration: `{track.duration}` | By: {track.requested_by_name}",
            reply_markup=player_buttons(paused)
        )


async def _play_track(client: Client, message: Message, track: Track, video: bool = False):
    chat_id = message.chat.id
    call = get_call_manager()

    pos = queue.add(chat_id, track)

    if call.is_active(chat_id):
        await message.reply_text(
            f"**Added to Queue** `#{pos}`\n\n"
            f"**{track.title}**\n"
            f"`{track.duration}` | {track.channel}\n"
            f"Requested by: {track.requested_by_name}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Queue", callback_data="queue"),
                InlineKeyboardButton("⏭ Skip",  callback_data="skip"),
            ]])
        )
        return

    status_msg = await message.reply_text("**Downloading...**")
    try:
        if video:
            file_path = await download_video(track.url)
        else:
            file_path = await download_audio(track.url)

        if not file_path:
            await status_msg.edit("**Failed to download.**")
            queue.clear(chat_id)
            return

        track.file_path = file_path
        success = await call.join_and_play(chat_id, file_path, video=video)

        if success:
            await increment_play_count()
            await add_to_history(chat_id, track.requested_by, track.title, track.url, track.duration)
            cancel_leave(chat_id)
            await status_msg.delete()
            await _send_now_playing(message, track, queue_pos=1, total=queue.queue_length(chat_id))
        else:
            await status_msg.edit("**Failed to join voice chat.** Make sure bot is admin.")
            queue.clear(chat_id)

    except Exception as e:
        await status_msg.edit(f"**Error:** `{str(e)[:200]}`")
        queue.clear(chat_id)


async def _handle_play_request(client: Client, message: Message, query: str, video: bool = False):
    chat_id = message.chat.id
    user = message.from_user

    if await is_blacklisted(chat_id) or await is_blacklisted(user.id):
        return await message.reply_text("**You or this chat is blacklisted.**")

    # Flood protection
    flooded, wait_s = check_flood(user.id)
    if flooded:
        return await message.reply_text(
            f"**Slow down!** Wait `{wait_s}s` before next request.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("OK", callback_data="close")]])
        )

    await add_chat(chat_id)
    await add_user(user.id, user.first_name)

    if is_youtube_url(query):
        status_msg = await message.reply_text("**Fetching info...**")
        try:
            info = await get_video_info(query)
            await status_msg.delete()
            track = Track(
                title=info["title"], url=info["url"],
                duration=info["duration"], duration_s=info["duration_s"],
                thumbnail=info["thumbnail"], channel=info["channel"],
                requested_by=user.id, requested_by_name=user.first_name,
                video_id=info["video_id"], is_video=video,
            )
            await _play_track(client, message, track, video=video)
        except Exception as e:
            await status_msg.edit(f"**Error:** `{str(e)[:150]}`")
        return

    # Search
    status_msg = await message.reply_text(f"**Searching:** `{query}`")
    results = await youtube_search(query, limit=5)

    if not results:
        return await status_msg.edit("**No results found.**")

    if len(results) == 1:
        await status_msg.delete()
        r = results[0]
        track = Track(
            title=r["title"], url=r["url"],
            duration=r["duration"], duration_s=r["duration_s"],
            thumbnail=r["thumbnail"], channel=r["channel"],
            requested_by=user.id, requested_by_name=user.first_name,
            video_id=r["video_id"], is_video=video,
        )
        await _play_track(client, message, track, video=video)
        return

    buttons = []
    text = f"**Results for:** `{query}`\n\n"
    for i, r in enumerate(results, 1):
        text += f"`{i}.` **{r['title'][:45]}**\n    `{r['duration']}` | {r['channel'][:20]}\n\n"
        prefix = "v" if video else "a"
        buttons.append([InlineKeyboardButton(
            f"{i}. {r['title'][:38]}", callback_data=f"search_{prefix}_{r['video_id']}"
        )])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")])
    await status_msg.edit(text, reply_markup=InlineKeyboardMarkup(buttons))


# ── COMMANDS ────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("play") & filters.group)
async def play_command(client: Client, message: Message):
    if len(message.command) < 2:
        query = message.reply_to_message.text if message.reply_to_message else None
        if not query:
            return await message.reply_text(
                "**Usage:** `/play <song name or URL>`\n**Example:** `/play Tum Hi Ho`"
            )
    else:
        query = " ".join(message.command[1:])
    await _handle_play_request(client, message, query, video=False)


@Client.on_message(filters.command(["vplay", "video"]) & filters.group)
async def vplay_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/vplay <song name or URL>`")
    query = " ".join(message.command[1:])
    await _handle_play_request(client, message, query, video=True)


@Client.on_message(filters.command("stream") & filters.group)
async def stream_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/stream <song name>`")
    query = " ".join(message.command[1:])
    await _handle_play_request(client, message, query, video=True)


@Client.on_message(filters.command(["search", "yt"]) & filters.group)
async def search_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/search <query>`")
    query = " ".join(message.command[1:])
    user = message.from_user
    await add_user(user.id, user.first_name)
    status = await message.reply_text(f"**Searching:** `{query}`")
    results = await youtube_search(query, limit=8)
    if not results:
        return await status.edit("**No results found.**")
    text = f"**YouTube Results**\n`{query}`\n\n"
    buttons = []
    for i, r in enumerate(results, 1):
        text += f"`{i}.` **{r['title'][:40]}**\n    `{r['duration']}` | {format_views(r['views'])} views\n\n"
        buttons.append([
            InlineKeyboardButton(f"🎵 Audio {i}", callback_data=f"search_a_{r['video_id']}"),
            InlineKeyboardButton(f"🎬 Video {i}", callback_data=f"search_v_{r['video_id']}"),
        ])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")])
    await status.edit(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)


@Client.on_message(filters.command("playlist") & filters.group)
async def playlist_command(client: Client, message: Message):
    """Import YouTube playlist into queue"""
    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/playlist <YouTube Playlist URL>`\n\n"
            f"Max `{Config.PLAYLIST_FETCH_LIMIT}` songs will be added."
        )
    user = message.from_user
    url = message.command[1]
    if "playlist" not in url.lower() and "list=" not in url.lower():
        return await message.reply_text("**Invalid playlist URL.** Provide a YouTube playlist link.")

    flooded, wait_s = check_flood(user.id)
    if flooded:
        return await message.reply_text(f"**Wait `{wait_s}s` before next request.**")

    status = await message.reply_text(f"**Fetching playlist...** (max {Config.PLAYLIST_FETCH_LIMIT} songs)")
    try:
        tracks_info = await fetch_playlist(url, limit=Config.PLAYLIST_FETCH_LIMIT)
        if not tracks_info:
            return await status.edit("**Failed to fetch playlist or empty playlist.**")

        chat_id = message.chat.id
        added = 0
        for info in tracks_info:
            track = Track(
                title=info["title"], url=info["url"],
                duration=info["duration"], duration_s=info["duration_s"],
                thumbnail=info.get("thumbnail", ""), channel=info.get("channel", "YouTube"),
                requested_by=user.id, requested_by_name=user.first_name,
                video_id=info.get("video_id", ""), is_video=False,
            )
            queue.add(chat_id, track)
            added += 1

        await status.edit(
            f"**Playlist Added!**\n\n"
            f"**{added} songs** added to queue.\n"
            f"Use `/play` to start if not already playing.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Queue", callback_data="queue"),
            ]])
        )
        # Auto-start if nothing playing
        call = get_call_manager()
        if not call.is_active(chat_id):
            first = queue.get_current(chat_id)
            if first:
                fake_msg = message
                await _play_track(client, fake_msg, first, video=False)
    except Exception as e:
        await status.edit(f"**Error:** `{str(e)[:200]}`")
