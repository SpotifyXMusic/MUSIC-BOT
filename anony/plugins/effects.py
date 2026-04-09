"""
Audio Effects Plugin
/bass /nightcore /slow /reverb /8d /karaoke /vocalboost /speed /effect /cleareffect
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from anony.helpers.admins import can_control_stream
from anony.helpers.filters_audio import AUDIO_FILTERS, FILTER_DESCRIPTIONS, apply_filter, apply_speed
from anony.helpers.queue import queue

_active_effects: dict = {}


async def _apply_and_stream(chat_id: int, filter_name: str = None, speed: float = None) -> bool:
    track = queue.get_current(chat_id)
    if not track or not track.file_path:
        return False
    try:
        from anony.core import call_manager
        if filter_name:
            new_path = await apply_filter(track.file_path, filter_name)
        elif speed:
            new_path = await apply_speed(track.file_path, speed)
        else:
            new_path = track.file_path
        await call_manager.join_and_play(chat_id, new_path, video=track.is_video)
        return True
    except Exception:
        return False


@Client.on_message(filters.command("effect") & filters.group)
async def effect_menu(client: Client, message: Message):
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
        InlineKeyboardButton("Clear Effect", callback_data="effect_clear"),
        InlineKeyboardButton("Close", callback_data="close"),
    ])
    active = _active_effects.get(message.chat.id, "None")
    await message.reply_text(
        f"**Audio Effects**\nActive: `{active}`\n\nSelect an effect:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_message(filters.command("bass") & filters.group)
async def bass_cmd(client: Client, message: Message):
    await _effect_command(client, message, "bass")

@Client.on_message(filters.command("nightcore") & filters.group)
async def nightcore_cmd(client: Client, message: Message):
    await _effect_command(client, message, "nightcore")

@Client.on_message(filters.command("slow") & filters.group)
async def slow_cmd(client: Client, message: Message):
    await _effect_command(client, message, "slow")

@Client.on_message(filters.command("reverb") & filters.group)
async def reverb_cmd(client: Client, message: Message):
    await _effect_command(client, message, "reverb")

@Client.on_message(filters.command("8d") & filters.group)
async def eightd_cmd(client: Client, message: Message):
    await _effect_command(client, message, "8d")

@Client.on_message(filters.command("karaoke") & filters.group)
async def karaoke_cmd(client: Client, message: Message):
    await _effect_command(client, message, "karaoke")

@Client.on_message(filters.command("vocalboost") & filters.group)
async def vocalboost_cmd(client: Client, message: Message):
    await _effect_command(client, message, "vocalboost")


async def _effect_command(client: Client, message: Message, effect: str):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can apply effects.**")
    if not queue.get_current(chat_id):
        return await message.reply_text("**Nothing is playing.**")
    status = await message.reply_text(f"**Applying {effect} effect...**")
    success = await _apply_and_stream(chat_id, filter_name=effect)
    if success:
        _active_effects[chat_id] = effect
        desc = FILTER_DESCRIPTIONS.get(effect, effect)
        await status.edit(
            f"**Effect Applied:** {desc}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Clear Effect", callback_data="effect_clear"),
                InlineKeyboardButton("More Effects", callback_data="effect_menu"),
            ]])
        )
    else:
        await status.edit("**Failed to apply effect.**")


@Client.on_message(filters.command("speed") & filters.group)
async def speed_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can change speed.**")
    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/speed <0.5 - 2.0>`\n`/speed 1.5` - Faster\n`/speed 0.75` - Slower"
        )
    try:
        speed = float(message.command[1])
        if not 0.5 <= speed <= 2.0:
            return await message.reply_text("**Speed must be between 0.5 and 2.0**")
    except ValueError:
        return await message.reply_text("**Invalid speed value.**")
    status = await message.reply_text(f"**Applying {speed}x speed...**")
    success = await _apply_and_stream(chat_id, speed=speed)
    await status.edit(f"**Speed set to {speed}x**" if success else "**Failed.**")


@Client.on_message(filters.command("cleareffect") & filters.group)
async def cleareffect_command(client: Client, message: Message):
    chat_id = message.chat.id
    if not await can_control_stream(client, chat_id, message.from_user.id):
        return await message.reply_text("**Only admins/auth users can clear effects.**")
    _active_effects.pop(chat_id, None)
    success = await _apply_and_stream(chat_id)
    await message.reply_text("**Effect cleared.**" if success else "**Nothing is playing.**")


@Client.on_callback_query(filters.regex("^effect_"))
async def effect_callback(client: Client, callback: CallbackQuery):
    action = callback.data.replace("effect_", "")
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    if action == "menu":
        await effect_menu(client, callback.message)
        return await callback.answer()

    if not await can_control_stream(client, chat_id, user_id):
        return await callback.answer("Only admins/auth users!", show_alert=True)

    if action == "clear":
        _active_effects.pop(chat_id, None)
        await _apply_and_stream(chat_id)
        await callback.answer("Effect cleared!")
        await callback.message.edit("**Effect cleared.**")
        return

    if action not in AUDIO_FILTERS:
        return await callback.answer("Unknown effect.", show_alert=True)

    await callback.answer(f"Applying {action}...")
    if not queue.get_current(chat_id):
        return await callback.message.edit("**Nothing is playing.**")

    success = await _apply_and_stream(chat_id, filter_name=action)
    if success:
        _active_effects[chat_id] = action
        desc = FILTER_DESCRIPTIONS.get(action, action)
        await callback.message.edit(
            f"**Effect Applied:** {desc}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Clear Effect", callback_data="effect_clear"),
                InlineKeyboardButton("More Effects", callback_data="effect_menu"),
            ]])
        )
    else:
        await callback.message.edit("**Failed to apply effect.**")
