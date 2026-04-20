from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from anony.helpers.youtube import get_video_info
from anony.helpers.queue import queue, Track


@Client.on_callback_query(filters.regex("^search_"))
async def search_cb(client: Client, cb: CallbackQuery):
    if cb.data == "search_cancel":
        await cb.message.delete()
        return
    parts = cb.data.split("_", 2)
    if len(parts) < 3:
        return await cb.answer("Invalid.", show_alert=True)
    _, mode, vid = parts
    is_video = (mode == "v")
    url = f"https://youtube.com/watch?v={vid}"
    user = cb.from_user
    await cb.answer("Loading...")
    await cb.message.edit(f"**Fetching:** `{url}`")
    try:
        info = await get_video_info(url)
        track = Track(
            title=info["title"], url=info["url"],
            duration=info["duration"], duration_s=info["duration_s"],
            thumbnail=info["thumbnail"], channel=info["channel"],
            requested_by=user.id, requested_by_name=user.first_name,
            video_id=info["video_id"], is_video=is_video,
        )
        await cb.message.delete()
        msg = await client.send_message(cb.message.chat.id, f"**Loading:** {track.title}")
        from anony.plugins.play import _play_track
        await _play_track(client, msg, track, is_video)
    except Exception as e:
        await cb.message.edit(f"**Error:** `{str(e)[:200]}`")
