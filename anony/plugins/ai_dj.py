# AI DJ Plugin
# Toggle AI Auto DJ on/off per group

from pyrogram import filters, types
from anony import app, config, db


# In-memory AI DJ settings: {chat_id: bool}
_ai_dj_enabled: dict[int, bool] = {}


def is_ai_dj_on(chat_id: int) -> bool:
    return _ai_dj_enabled.get(chat_id, True)  # Default: ON


@app.on_message(filters.command(["aidj", "autodj"]) & filters.group & ~app.bl_users)
async def toggle_ai_dj(_, message: types.Message):
    """/aidj - Toggle AI Auto DJ"""
    if not config.AI_ENABLED:
        return await message.reply_text(
            "<b>AI DJ is disabled.</b>\n"
            "<i>Add GROQ_API_KEY to enable AI features.</i>"
        )

    chat_id = message.chat.id
    current = is_ai_dj_on(chat_id)

    if len(message.command) > 1:
        arg = message.command[1].lower()
        if arg == "on":
            _ai_dj_enabled[chat_id] = True
        elif arg == "off":
            _ai_dj_enabled[chat_id] = False
        else:
            _ai_dj_enabled[chat_id] = not current
    else:
        _ai_dj_enabled[chat_id] = not current

    status = "ON" if _ai_dj_enabled[chat_id] else "OFF"
    await message.reply_text(
        f"<b>AI DJ: {status}</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"<i>{'AI will auto-queue similar songs when queue ends.' if _ai_dj_enabled[chat_id] else 'AI auto-queue disabled.'}</i>"
    )
