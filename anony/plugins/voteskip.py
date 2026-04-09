"""
Vote Skip Plugin
/voteskip - Democratic skip system
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.flood import add_vote_skip, get_vote_skips, clear_vote_skips
from anony.helpers.queue import queue
from anony.core.mongo import get_group_settings
from config import Config


def get_call_manager():
    from anony.core import call_manager
    return call_manager


@Client.on_message(filters.command("voteskip") & filters.group)
async def voteskip_command(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    call = get_call_manager()
    if not call.is_active(chat_id):
        return await message.reply_text("**Nothing is playing.**")

    settings = await get_group_settings(chat_id)
    if not settings.get("vote_skip", False):
        return await message.reply_text(
            "**Vote Skip is disabled.**\nAdmins can enable it in `/settings`."
        )

    voters = add_vote_skip(chat_id, user_id)
    needed_pct = settings.get("vote_skip_percent", Config.VOTE_SKIP_PERCENT)

    try:
        chat = await client.get_chat(chat_id)
        total_members = chat.members_count or 10
    except Exception:
        total_members = 10

    needed = max(2, int(total_members * needed_pct / 100))
    current = len(voters)
    track = queue.get_current(chat_id)
    track_name = track.title[:40] if track else "current song"

    if current >= needed:
        # Skip!
        clear_vote_skips(chat_id)
        next_track = queue.next(chat_id)
        if not next_track:
            await call.stop(chat_id)
            return await message.reply_text(
                f"**Vote Skip Passed!** ({current}/{needed})\n\n**Queue ended.**"
            )

        from anony.helpers.youtube import download_audio
        status = await message.reply_text(f"**Vote Skip Passed!** ({current}/{needed}) Skipping...")
        try:
            file_path = await download_audio(next_track.url)
            if file_path:
                next_track.file_path = file_path
                await call.join_and_play(chat_id, file_path, video=next_track.is_video)
                await status.edit(
                    f"**Vote Skip Passed!** `{current}/{needed} votes`\n\n"
                    f"**Now Playing:** {next_track.title}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⏭ Skip", callback_data="skip"),
                        InlineKeyboardButton("⏹ Stop", callback_data="stop"),
                    ]])
                )
        except Exception as e:
            await status.edit(f"**Skip failed:** `{str(e)[:100]}`")
    else:
        remaining = needed - current
        await message.reply_text(
            f"**Vote Skip** for: `{track_name}`\n\n"
            f"Votes: `{current}/{needed}` | Need `{remaining}` more\n\n"
            f"Use `/voteskip` to vote!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"👍 Vote Skip ({current}/{needed})", callback_data=f"vs_{chat_id}"),
            ]])
        )


@Client.on_callback_query(filters.regex(r"^vs_"))
async def voteskip_callback(client: Client, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    call = get_call_manager()
    if not call.is_active(chat_id):
        return await callback.answer("Nothing is playing!", show_alert=True)

    voters = add_vote_skip(chat_id, user_id)
    settings = await get_group_settings(chat_id)
    needed_pct = settings.get("vote_skip_percent", Config.VOTE_SKIP_PERCENT)

    try:
        chat = await client.get_chat(chat_id)
        total_members = chat.members_count or 10
    except Exception:
        total_members = 10

    needed = max(2, int(total_members * needed_pct / 100))
    current = len(voters)
    await callback.answer(f"Voted! {current}/{needed}", show_alert=False)

    if current >= needed:
        clear_vote_skips(chat_id)
        next_track = queue.next(chat_id)
        if not next_track:
            await call.stop(chat_id)
            await callback.message.edit(f"**Vote Skip Passed!** Queue ended.")
        else:
            await callback.message.edit(f"**Vote Skip Passed!** {current}/{needed} votes. Skipping...")
    else:
        track = queue.get_current(chat_id)
        track_name = track.title[:40] if track else "current song"
        await callback.message.edit(
            f"**Vote Skip** for: `{track_name}`\n\n"
            f"Votes: `{current}/{needed}` | Need `{needed - current}` more",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(f"👍 Vote Skip ({current}/{needed})", callback_data=f"vs_{chat_id}"),
            ]])
        )
