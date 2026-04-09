"""Callbacks Plugin - Search result selection"""
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from anony.helpers.youtube import get_video_info
from anony.helpers.queue import queue, Track

def get_cm():
    from anony.core import call_manager
    return call_manager

@Client.on_callback_query(filters.regex("^search_"))
async def search_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    if data == "search_cancel":
        await callback.message.delete()
        return
    parts = data.split("_", 2)
    if len(parts) < 3:
        return await callback.answer("Invalid.", show_alert=True)
    _, mode, video_id = parts
    is_video = (mode == "v")
    url = f"https://youtube.com/watch?v={video_id}"
    user = callback.from_user
    await callback.answer("Loading...")
    await callback.message.edit(f"**Fetching:** `{url}`")
    try:
        info = await get_video_info(url)
        track = Track(
            title=info["title"], url=info["url"],
            duration=info["duration"], duration_s=info["duration_s"],
            thumbnail=info["thumbnail"], channel=info["channel"],
            requested_by=user.id, requested_by_name=user.first_name,
            video_id=info["video_id"], is_video=is_video,
        )
        await callback.message.delete()
        msg = await client.send_message(callback.message.chat.id, f"**Loading:** {track.title}")
        from anony.plugins.play import _play_track
        await _play_track(client, msg, track, video=is_video)
    except Exception as e:
        await callback.message.edit(f"**Error:** `{str(e)[:200]}`")
