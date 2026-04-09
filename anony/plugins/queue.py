"""
Queue Plugin V2
/queue /remove /clearqueue - with pagination and inline buttons
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.queue import queue
from anony.helpers.admins import can_control_stream


@Client.on_message(filters.command(["queue", "q"]) & filters.group)
async def queue_command(client: Client, message: Message):
    chat_id = message.chat.id
    page = 1
    if len(message.command) > 1:
        try:
            page = int(message.command[1])
        except ValueError:
            pass

    current = queue.get_current(chat_id)
    if not current:
        return await message.reply_text(
            "**Queue is empty.**\nUse `/play <song>` to add music."
        )

    total = queue.queue_length(chat_id)
    text = queue.format_queue(chat_id, page=page)

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"qpage_{page-1}"))
    if page * 5 < total:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"qpage_{page+1}"))

    buttons = []
    if nav:
        buttons.append(nav)

    loop_txt   = "🔁 Loop: ON"  if queue.is_looping(chat_id)   else "🔁 Loop: OFF"
    repeat_txt = "🔂 Repeat: ON" if queue.is_repeating(chat_id) else "🔂 Repeat: OFF"
    buttons.append([
        InlineKeyboardButton(loop_txt,   callback_data="loop"),
        InlineKeyboardButton(repeat_txt, callback_data="repeat"),
    ])
    buttons.append([
        InlineKeyboardButton("🎵 Now Playing", callback_data="nowplaying"),
        InlineKeyboardButton("❌ Close",        callback_data="close"),
    ])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.command("remove") & filters.group)
async def remove_command(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await can_control_stream(client, chat_id, user_id):
        return await message.reply_text("**Only admins/auth users can remove tracks.**")

    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/remove <position>`\nExample: `/remove 2`")

    try:
        pos = int(message.command[1])
    except ValueError:
        return await message.reply_text("**Invalid position number.**")

    track = queue.remove(chat_id, pos)
    if track:
        await message.reply_text(
            f"**Removed from queue:**\n`{pos}.` {track.title}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Queue", callback_data="queue"),
            ]])
        )
    else:
        await message.reply_text("**Invalid position.** Check `/queue` for positions.")


@Client.on_message(filters.command("clearqueue") & filters.group)
async def clearqueue_command(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await can_control_stream(client, chat_id, user_id):
        return await message.reply_text("**Only admins/auth users can clear the queue.**")

    length = queue.queue_length(chat_id)
    queue.clear(chat_id)
    await message.reply_text(f"**Queue cleared.** Removed `{length}` tracks.")


@Client.on_callback_query(filters.regex(r"^qpage_\d+$"))
async def queue_page_callback(client: Client, callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    chat_id = callback.message.chat.id
    total = queue.queue_length(chat_id)

    if not total:
        return await callback.answer("Queue is empty!", show_alert=True)

    text = queue.format_queue(chat_id, page=page)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"qpage_{page-1}"))
    if page * 5 < total:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"qpage_{page+1}"))

    buttons = []
    if nav:
        buttons.append(nav)

    loop_txt   = "🔁 Loop: ON"  if queue.is_looping(chat_id)   else "🔁 Loop: OFF"
    repeat_txt = "🔂 Repeat: ON" if queue.is_repeating(chat_id) else "🔂 Repeat: OFF"
    buttons.append([
        InlineKeyboardButton(loop_txt,   callback_data="loop"),
        InlineKeyboardButton(repeat_txt, callback_data="repeat"),
    ])
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])

    await callback.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback.answer()


@Client.on_callback_query(filters.regex("^nowplaying$"))
async def nowplaying_callback(client: Client, callback: CallbackQuery):
    from anony.plugins.now import now_playing
    await now_playing(client, callback.message)
    await callback.answer()
