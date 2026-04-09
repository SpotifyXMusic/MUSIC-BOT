"""
Start & Help Plugin V2
Blue + Red button colors matching screenshot
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config


# ── BUTTON COLORS (blue = url/action, red = close/source, gray = sections) ──

HELP_SECTIONS = {
    "admins": (
        "**Admin Commands:**\n\n"
        "`/pause` - Pause the ongoing stream\n"
        "`/resume` - Resume the paused stream\n"
        "`/skip` - Skip the current track\n"
        "`/stop` - Stop stream and clear queue\n\n"
        "`/seek [seconds]` - Seek forward\n"
        "`/seekback [seconds]` - Seek backward\n\n"
        "`/mute` - Mute bot in voice chat\n"
        "`/unmute` - Unmute bot\n\n"
        "`/loop` - Toggle queue loop\n"
        "`/repeat` - Toggle repeat current song\n"
        "`/reload` - Reload admin cache"
    ),
    "auth": (
        "**Auth Commands:**\n\n"
        "_Authorized users can control stream without being admin._\n\n"
        "`/auth` - Authorize a user\n"
        "`/unauth` - Remove authorization\n"
        "`/authlist` - Show authorized users"
    ),
    "blacklist": (
        "**Blacklist Commands:**\n\n"
        "_Blacklisted chats/users cannot use the bot._\n\n"
        "`/blacklist [id]` - Add to blacklist\n"
        "`/unblacklist [id]` - Remove from blacklist\n"
        "`/blacklistlist` - Show all blacklisted"
    ),
    "language": (
        "**Language Commands:**\n\n"
        "_Bot supports 13 languages._\n\n"
        "`/lang` - Change bot language\n\n"
        "Available: English, Hindi, Arabic, German,\n"
        "Spanish, French, Japanese, Burmese,\n"
        "Punjabi, Portuguese, Russian, Turkish, Chinese"
    ),
    "ping": (
        "**Ping Commands:**\n\n"
        "`/help` - Show this help menu\n"
        "`/ping` - Check ping and memory usage\n"
        "`/start` - Start the bot\n"
        "`/sudolist` - List of sudo users"
    ),
    "play": (
        "**Play Commands:**\n\n"
        "`/play [song/URL]` - Play audio from YouTube\n"
        "`/vplay [song/URL]` - Stream video (480p)\n"
        "`/stream [song/URL]` - Same as vplay\n"
        "`/search [query]` - Search YouTube\n"
        "`/playlist [URL]` - Import YouTube playlist\n\n"
        "Tip: Reply to any message with `/play` to search!"
    ),
    "queue": (
        "**Queue Commands:**\n\n"
        "`/queue` or `/q` - Show queue with pagination\n"
        "`/now` or `/np` - Now playing + progress bar\n"
        "`/remove [pos]` - Remove track from queue\n"
        "`/clearqueue` - Clear entire queue\n"
        "`/voteskip` - Vote to skip current song"
    ),
    "stats": (
        "**Stats Commands:**\n\n"
        "`/stats` - Bot statistics (sudo)\n"
        "`/ac` - Active calls count\n"
        "`/activevc` - List active calls\n"
        "`/ping` - Ping and system usage\n"
        "`/history` - Recently played songs\n"
        "`/topsongs` - Most played songs\n"
        "`/toprequests` - Top requesters"
    ),
    "sudoers": (
        "**Sudo Commands:**\n\n"
        "`/ac` - Active calls count\n"
        "`/activevc` - Active voice calls list\n"
        "`/broadcast` - Broadcast to all chats\n"
        "`/eval` - Execute Python code\n"
        "`/logs` - Get log file\n"
        "`/logger [on|off]` - Toggle logger\n"
        "`/restart` - Restart bot\n"
        "`/addsudo` - Add sudo user\n"
        "`/rmsudo` - Remove sudo user"
    ),
    "effects": (
        "**Audio Effects:**\n\n"
        "`/effect` - Open effects menu\n"
        "`/bass` - Heavy bass boost\n"
        "`/nightcore` - Speed up + pitch\n"
        "`/slow` - Slow down audio\n"
        "`/8d` - 8D spatial audio\n"
        "`/reverb` - Echo/reverb effect\n"
        "`/karaoke` - Remove center vocals\n"
        "`/vocalboost` - Enhance vocals\n"
        "`/speed [0.5-2.0]` - Custom speed\n"
        "`/cleareffect` - Remove active effect"
    ),
    "settings": (
        "**Settings Commands:**\n\n"
        "`/settings` - Group settings panel\n"
        "  Toggle: Auto Leave, Vote Skip,\n"
        "          Thumbnail, Announcements\n\n"
        "`/lyrics [song]` - Get song lyrics\n"
        "`/history` - Recently played\n"
        "`/topsongs` - Most played songs\n"
        "`/toprequests` - Top song requesters"
    ),
}

HELP_BUTTONS = [
    [
        InlineKeyboardButton("Admins",    callback_data="help_admins"),
        InlineKeyboardButton("Auth",      callback_data="help_auth"),
        InlineKeyboardButton("Blacklist", callback_data="help_blacklist"),
    ],
    [
        InlineKeyboardButton("Language",  callback_data="help_language"),
        InlineKeyboardButton("Ping",      callback_data="help_ping"),
        InlineKeyboardButton("Play",      callback_data="help_play"),
    ],
    [
        InlineKeyboardButton("Queue",     callback_data="help_queue"),
        InlineKeyboardButton("Stats",     callback_data="help_stats"),
        InlineKeyboardButton("Sudoers",   callback_data="help_sudoers"),
    ],
    [
        InlineKeyboardButton("Effects",   callback_data="help_effects"),
        InlineKeyboardButton("Settings",  callback_data="help_settings"),
    ],
]

# Blue add button + gray info buttons + red source (matching screenshots)
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "Add me to your group",
            url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true"
        )],
        [InlineKeyboardButton("Help", callback_data="help_main")],
        [
            InlineKeyboardButton("Support",  url=Config.SUPPORT_GROUP),
            InlineKeyboardButton("Channel",  url=Config.SUPPORT_CHANNEL),
        ],
    ])


@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user = message.from_user
    await message.reply_text(
        f"Hey **{user.first_name}**!\n"
        f"This is **{Config.BOT_NAME}**!\n\n"
        f"An advanced music player bot with awesome features.\n\n"
        f"_Click Help for all commands._",
        reply_markup=main_buttons()
    )


@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    await message.reply_text(
        "**Click the buttons below to get information about my commands.**\n\n"
        "_Note: All commands can be used with_ `/`",
        reply_markup=InlineKeyboardMarkup(HELP_BUTTONS)
    )


@Client.on_callback_query(filters.regex("^help_"))
async def help_callback(client: Client, callback: CallbackQuery):
    section = callback.data.replace("help_", "")

    if section == "main":
        await callback.message.edit(
            "**Click the buttons below to get information about my commands.**\n\n"
            "_Note: All commands can be used with_ `/`",
            reply_markup=InlineKeyboardMarkup(HELP_BUTTONS)
        )
        return

    if section not in HELP_SECTIONS:
        return await callback.answer("Unknown section.", show_alert=True)

    await callback.message.edit(
        HELP_SECTIONS[section],
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Back",  callback_data="help_main"),
            InlineKeyboardButton("Close", callback_data="close"),
        ]])
    )
    await callback.answer()
