from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from anony.helpers.admins import can_control
from anony.helpers.queue import queue
import time

_start_times: dict = {}


def set_start(chat_id): _start_times[chat_id] = time.time()
def get_elapsed(chat_id): return int(time.time() - _start_times.get(chat_id, time.time()))


@Client.on_message(filters.command(["queue", "q"]) & filters.group)
async def queue_cmd(client: Client, message: Message):
    cid = message.chat.id
    page = 1
    if len(message.command) > 1:
        try: page = int(message.command[1])
        except: pass
    if not queue.get_current(cid):
        return await message.reply_text("**Queue is empty.**\nUse `/play <song>` to add music.")
    total = queue.length(cid)
    text = queue.format_queue(cid, page)
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"qp_{page-1}"))
    if page * 5 < total: nav.append(InlineKeyboardButton("Next ▶", callback_data=f"qp_{page+1}"))
    btns = []
    if nav: btns.append(nav)
    btns.append([
        InlineKeyboardButton("🔁 Loop: " + ("ON" if queue.is_looping(cid) else "OFF"), callback_data="loop"),
        InlineKeyboardButton("🔂 Repeat: " + ("ON" if queue.is_repeating(cid) else "OFF"), callback_data="repeat"),
    ])
    btns.append([InlineKeyboardButton("❌ Close", callback_data="close")])
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns))


@Client.on_message(filters.command(["now", "np"]) & filters.group)
async def now_cmd(client: Client, message: Message):
    cid = message.chat.id
    t = queue.get_current(cid)
    if not t: return await message.reply_text("**Nothing is playing.**")
    try:
        from anony.core import call_manager
        paused = call_manager.is_paused(cid)
    except: paused = False
    elapsed = get_elapsed(cid)
    total_s = t.duration_s or 300
    pct = min(elapsed / total_s, 1.0)
    filled = int(20 * pct)
    bar = "█" * filled + "─" * (20 - filled)
    e_min, e_sec = divmod(elapsed, 60)
    t_min, t_sec = divmod(total_s, 60)
    status = "⏸ Paused" if paused else "▶ Playing"
    await message.reply_text(
        f"**{status}**\n\n**{t.title}**\n\n"
        f"`{e_min}:{e_sec:02d}` {bar} `{t_min}:{t_sec:02d}`\n\n"
        f"Channel: {t.channel}\nBy: {t.requested_by_name}\n"
        f"Queue: {queue.get_index(cid)+1}/{queue.length(cid)}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏸ Pause" if not paused else "▶ Resume",
                                     callback_data="pause" if not paused else "resume"),
                InlineKeyboardButton("⏭ Skip",  callback_data="skip"),
                InlineKeyboardButton("⏹ Stop",  callback_data="stop"),
            ],
            [
                InlineKeyboardButton("📋 Queue",  callback_data="queue"),
                InlineKeyboardButton("🎵 Lyrics", callback_data="lyrics"),
            ],
            [InlineKeyboardButton("❌ Close", callback_data="close")],
        ])
    )


@Client.on_message(filters.command("remove") & filters.group)
async def remove_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth.**")
    if len(message.command) < 2: return await message.reply_text("**Usage:** `/remove <position>`")
    try: pos = int(message.command[1])
    except: return await message.reply_text("**Invalid position.**")
    t = queue.remove(cid, pos)
    if t: await message.reply_text(f"**Removed:** {t.title}")
    else: await message.reply_text("**Invalid position.**")


@Client.on_message(filters.command("clearqueue") & filters.group)
async def clearqueue_cmd(client: Client, message: Message):
    cid = message.chat.id
    if not await can_control(client, cid, message.from_user.id):
        return await message.reply_text("**Only admins/auth.**")
    n = queue.length(cid)
    queue.clear(cid)
    await message.reply_text(f"**Queue cleared.** Removed `{n}` tracks.")


@Client.on_callback_query(filters.regex(r"^qp_\d+$"))
async def qpage_cb(client: Client, cb: CallbackQuery):
    page = int(cb.data.split("_")[1])
    cid = cb.message.chat.id
    total = queue.length(cid)
    if not total: return await cb.answer("Queue empty!", show_alert=True)
    text = queue.format_queue(cid, page)
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"qp_{page-1}"))
    if page * 5 < total: nav.append(InlineKeyboardButton("Next ▶", callback_data=f"qp_{page+1}"))
    btns = []
    if nav: btns.append(nav)
    btns.append([InlineKeyboardButton("❌ Close", callback_data="close")])
    await cb.message.edit(text, reply_markup=InlineKeyboardMarkup(btns))
    await cb.answer()
