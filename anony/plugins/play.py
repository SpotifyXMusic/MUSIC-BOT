from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from anony.core.mongo import add_chat, add_user, increment_plays, add_history, is_blacklisted
from anony.helpers.youtube import youtube_search, get_video_info, download_audio, download_video, is_url, fetch_playlist, fmt_views
from anony.helpers.queue import queue, Track
from anony.helpers.flood import check_flood
from config import Config


def cm():
    from anony.core import call_manager
    return call_manager


def player_btns(paused=False):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause" if not paused else "▶ Resume",
                                 callback_data="pause" if not paused else "resume"),
            InlineKeyboardButton("⏭ Skip",   callback_data="skip"),
            InlineKeyboardButton("⏹ Stop",   callback_data="stop"),
        ],
        [
            InlineKeyboardButton("📋 Queue",  callback_data="queue"),
            InlineKeyboardButton("🔁 Loop",   callback_data="loop"),
            InlineKeyboardButton("🎵 Lyrics", callback_data="lyrics"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close")],
    ])


async def _play_track(client: Client, message: Message, track: Track, video: bool = False):
    chat_id = message.chat.id
    call = cm()

    pos = queue.add(chat_id, track)

    if call.is_active(chat_id):
        await message.reply_text(
            f"**Added to Queue** `#{pos}`\n\n**{track.title}**\n`{track.duration}` | {track.channel}\nBy: {track.requested_by_name}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Queue", callback_data="queue"),
                InlineKeyboardButton("⏭ Skip",  callback_data="skip"),
            ]])
        )
        return

    status = await message.reply_text("**Downloading...**")
    try:
        fp = await (download_video(track.url) if video else download_audio(track.url))
        if not fp:
            await status.edit("**Failed to download.**")
            queue.clear(chat_id)
            return
        track.file_path = fp
        ok = await call.join_and_play(chat_id, fp, video=video)
        if ok:
            await increment_plays()
            await add_history(chat_id, track.requested_by, track.title, track.url, track.duration)
            await status.delete()
            await message.reply_text(
                f"**Now {'Streaming' if video else 'Playing'}**\n\n**{track.title}**\n"
                f"`{track.duration}` | {track.channel}\nBy: {track.requested_by_name}",
                reply_markup=player_btns()
            )
        else:
            await status.edit("**Failed to join voice chat.**\nMake sure bot is admin with voice chat permission.")
            queue.clear(chat_id)
    except Exception as e:
        await status.edit(f"**Error:** `{str(e)[:200]}`")
        queue.clear(chat_id)


async def _handle(client: Client, message: Message, query: str, video: bool = False):
    chat_id = message.chat.id
    user = message.from_user

    if await is_blacklisted(chat_id) or await is_blacklisted(user.id):
        return await message.reply_text("**Blacklisted.**")

    flooded, wait = check_flood(user.id)
    if flooded:
        return await message.reply_text(f"**Wait `{wait}s` before next request.**")

    await add_chat(chat_id)
    await add_user(user.id, user.first_name)

    if is_url(query):
        status = await message.reply_text("**Fetching info...**")
        try:
            info = await get_video_info(query)
            await status.delete()
            t = Track(title=info["title"], url=info["url"], duration=info["duration"],
                      duration_s=info["duration_s"], thumbnail=info["thumbnail"],
                      channel=info["channel"], requested_by=user.id,
                      requested_by_name=user.first_name, video_id=info["video_id"], is_video=video)
            await _play_track(client, message, t, video)
        except Exception as e:
            await status.edit(f"**Error:** `{str(e)[:150]}`")
        return

    status = await message.reply_text(f"**Searching:** `{query}`")
    results = await youtube_search(query, limit=5)
    if not results:
        return await status.edit("**No results found.**")

    if len(results) == 1:
        await status.delete()
        r = results[0]
        t = Track(title=r["title"], url=r["url"], duration=r["duration"],
                  duration_s=r["duration_s"], thumbnail=r["thumbnail"],
                  channel=r["channel"], requested_by=user.id,
                  requested_by_name=user.first_name, video_id=r["video_id"], is_video=video)
        await _play_track(client, message, t, video)
        return

    text = f"**Results for:** `{query}`\n\n"
    buttons = []
    pref = "v" if video else "a"
    for i, r in enumerate(results, 1):
        text += f"`{i}.` **{r['title'][:40]}**\n   `{r['duration']}` | {r['channel'][:20]}\n\n"
        buttons.append([InlineKeyboardButton(f"{i}. {r['title'][:40]}", callback_data=f"search_{pref}_{r['video_id']}")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")])
    await status.edit(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.command("play") & filters.group)
async def play_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        q = message.reply_to_message.text if message.reply_to_message else None
        if not q: return await message.reply_text("**Usage:** `/play <song name or URL>`")
    else:
        q = " ".join(message.command[1:])
    await _handle(client, message, q, False)


@Client.on_message(filters.command(["vplay", "video", "stream"]) & filters.group)
async def vplay_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/vplay <song name or URL>`")
    await _handle(client, message, " ".join(message.command[1:]), True)


@Client.on_message(filters.command(["search", "yt"]) & filters.group)
async def search_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/search <query>`")
    query = " ".join(message.command[1:])
    await add_user(message.from_user.id, message.from_user.first_name)
    status = await message.reply_text(f"**Searching:** `{query}`")
    results = await youtube_search(query, limit=8)
    if not results:
        return await status.edit("**No results found.**")
    text = f"**YouTube Results**\n\n"
    buttons = []
    for i, r in enumerate(results, 1):
        text += f"`{i}.` **{r['title'][:40]}**\n   `{r['duration']}` | {fmt_views(r['views'])} views\n\n"
        buttons.append([
            InlineKeyboardButton(f"🎵 Audio {i}", callback_data=f"search_a_{r['video_id']}"),
            InlineKeyboardButton(f"🎬 Video {i}", callback_data=f"search_v_{r['video_id']}"),
        ])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="search_cancel")])
    await status.edit(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)


@Client.on_message(filters.command("playlist") & filters.group)
async def playlist_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(f"**Usage:** `/playlist <YouTube Playlist URL>`\nMax {Config.PLAYLIST_LIMIT} songs.")
    url = message.command[1]
    user = message.from_user
    flooded, wait = check_flood(user.id)
    if flooded: return await message.reply_text(f"**Wait `{wait}s`.**")
    status = await message.reply_text("**Fetching playlist...**")
    try:
        tracks = await fetch_playlist(url, Config.PLAYLIST_LIMIT)
        if not tracks: return await status.edit("**Empty or invalid playlist.**")
        chat_id = message.chat.id
        for info in tracks:
            queue.add(chat_id, Track(
                title=info["title"], url=info["url"], duration=info["duration"],
                duration_s=info["duration_s"], thumbnail=info.get("thumbnail",""),
                channel=info.get("channel","YouTube"), requested_by=user.id,
                requested_by_name=user.first_name, video_id=info.get("video_id","")
            ))
        await status.edit(
            f"**Playlist Added!**\n`{len(tracks)}` songs in queue.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Queue", callback_data="queue")]])
        )
        call = cm()
        if not call.is_active(chat_id):
            first = queue.get_current(chat_id)
            if first: await _play_track(client, message, first)
    except Exception as e:
        await status.edit(f"**Error:** `{str(e)[:200]}`")
