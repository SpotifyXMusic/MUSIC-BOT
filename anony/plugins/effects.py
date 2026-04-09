"""
Audio Effects Plugin
/bass /nightcore /slow /reverb /8d /speed /effect /cleareffect
No API key - uses FFmpeg (already installed)
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.admins import can_control_stream
from anony.helpers.filters_audio import AUDIO_FILTERS, FILTER_DESCRIPTIONS, apply_filter, apply_speed
from anony.helpers.queue import queue

# Store active effect per chat
_active_effects: dict = {}  # chat_id -> filter_name or None


def get_call_manager():
    from anony.core import call_manager
    return call_manager


async def _apply_and_stream(chat_id: int, filter_name: str = None, speed: float = None):
    """Apply filter to current track and restart stream"""
    track = queue.get_current(chat_id)
    if not track or not track.file_path:
        return False

    call = get_call_manager()
    try:
        if filter_name:
            new_path = await apply_filter(track.file_path, filter_name)
        elif speed:
            new_path = await apply_speed(track.file_path, speed)
        else:
            new_path = track.file_path

        await call.join_and_play(chat_id, new_path, video=track.is_video)
        return True
    except Exception:
        return False


@Client.on_message(filters.command("effect") & filters.group)
async def effect_menu(client: Client, message: Message):
    """Show effects menu"""
    buttons = []
    row = []
    for name, desc in FILTER_DESCRIPTIONS.items():
        label = desc.split(" - ")[0]
        row.append(InlineKeyboardButton(label, callback_data=f"effect_{name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton("❌ Clear Effect", callback_data="effect_clear"),
        InlineKeyboardButton("Close", callback_data="close"),
    ])

    chat_id = message.chat.id
    active = _active_effects.get(chat_id, "None")
    await message.reply_text(
        f"**Audio Effects**\n\nActive: `{active}`\n\nSelect an effect to apply:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_message(filters.command("speed") & filters.group)
async def speed_command(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await can_control_stream(client, chat_id, user_id):
        return await message.reply_text("**Only admins/auth users can change speed.**")

    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/speed <0.5 - 2.0>`\n\n"
            "Examples:\n`/speed 1.5` - 1.5x faster\n`/speed 0.75` - Slower"
        )

    try:
        speed = float(message.command[1])
        if not 0.5 <= speed <= 2.0:
            return await message.reply_text("**Speed must be between 0.5 and 2.0**")
    except ValueError:
        return await message.reply_text("**Invalid speed value.**")

    status = await message.reply_text(f"**Applying {speed}x speed...**")
    success = await _apply_and_stream(chat_id, speed=speed)
    if success:
        await status.edit(f"**Speed set to {speed}x**")
    else:
        await status.edit("**Failed. Is anything playing?**")


# Shortcut commands
for _effect in ["bass", "nightcore", "slow", "reverb", "8d", "karaoke", "vocalboost"]:
    def _make_handler(eff):
        @Client.on_message(filters.command(eff) & filters.group)
        async def handler(client, message, _eff=eff):
            uid = message.from_user.id
            cid = message.chat.id
            if not await can_control_stream(client, cid, uid):
                return await message.reply_text("**Only admins/auth users can apply effects.**")
            track = queue.get_current(cid)
            if not track:
                return await message.reply_text("**Nothing is playing.**")
            status = await message.reply_text(f"**Applying {_eff} effect...**")
            success = await _apply_and_stream(cid, filter_name=_eff)
            if success:
                _active_effects[cid] = _eff
                desc = FILTER_DESCRIPTIONS.get(_eff, _eff)
                await status.edit(
                    f"**Effect Applied: {desc}**",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Clear Effect", callback_data="effect_clear"),
                        InlineKeyboardButton("🎚 More Effects", callback_data="effect_menu"),
                    ]])
                )
            else:
                await status.edit("**Failed to apply effect.**")
        return handler
    _make_handler(_effect)


@Client.on_message(filters.command("cleareffect") & filters.group)
async def cleareffect_command(client: Client, message: Message):
    uid = message.from_user.id
    cid = message.chat.id
    if not await can_control_stream(client, cid, uid):
        return await message.reply_text("**Only admins/auth users can clear effects.**")
    track = queue.get_current(cid)
    if not track:
        return await message.reply_text("**Nothing is playing.**")
    status = await message.reply_text("**Clearing effect...**")
    _active_effects.pop(cid, None)
    success = await _apply_and_stream(cid, filter_name=None)
    await status.edit("**Effect cleared. Playing original.**" if success else "**Failed.**")


@Client.on_callback_query(filters.regex("^effect_"))
async def effect_callback(client: Client, callback: CallbackQuery):
    action = callback.data.replace("effect_", "")
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    if action == "menu":
        await effect_menu(client, callback.message)
        return

    if not await can_control_stream(client, chat_id, user_id):
        return await callback.answer("Only admins/auth users can apply effects!", show_alert=True)

    if action == "clear":
        _active_effects.pop(chat_id, None)
        track = queue.get_current(chat_id)
        if track:
            await _apply_and_stream(chat_id, filter_name=None)
        await callback.answer("Effect cleared!", show_alert=False)
        await callback.message.edit("**Effect cleared.**")
        return

    if action not in AUDIO_FILTERS:
        return await callback.answer("Unknown effect.", show_alert=True)

    await callback.answer(f"Applying {action}...")
    track = queue.get_current(chat_id)
    if not track:
        return await callback.message.edit("**Nothing is playing.**")

    success = await _apply_and_stream(chat_id, filter_name=action)
    if success:
        _active_effects[chat_id] = action
        desc = FILTER_DESCRIPTIONS.get(action, action)
        await callback.message.edit(
            f"**Effect Applied:** {desc}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Clear Effect", callback_data="effect_clear"),
                InlineKeyboardButton("🎚 More Effects", callback_data="effect_menu"),
            ]])
        )
    else:
        await callback.message.edit("**Failed to apply effect.**")
