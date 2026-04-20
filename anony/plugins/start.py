from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

HELP = {
    "play": "**Play Commands:**\n\n`/play <song/URL>` - Play audio\n`/vplay <song/URL>` - Play video\n`/stream <song/URL>` - Same as vplay\n`/search <query>` - Search YouTube\n`/playlist <URL>` - Import playlist",
    "controls": "**Controls (Admin/Auth):**\n\n`/pause` - Pause\n`/resume` - Resume\n`/skip` - Skip track\n`/stop` - Stop & clear\n`/seek <s>` - Seek forward\n`/seekback <s>` - Seek back\n`/mute` `/unmute`\n`/loop` `/repeat`",
    "queue": "**Queue:**\n\n`/queue` `/q` - Show queue\n`/now` `/np` - Now playing\n`/remove <pos>` - Remove track\n`/clearqueue` - Clear all\n`/voteskip` - Vote to skip",
    "features": "**Features:**\n\n`/lyrics [song]` - Get lyrics\n`/history` - Recently played\n`/topsongs` - Most played\n`/settings` - Group settings\n`/lang` - Change language",
    "admin": "**Admin:**\n\n`/auth` - Authorize user\n`/unauth` - Remove auth\n`/authlist` - Show auth users\n`/blacklist <id>` - Blacklist\n`/reload` - Reload cache",
    "sudo": "**Sudo:**\n\n`/stats` - Bot stats\n`/ac` - Active calls\n`/activevc` - Active VC list\n`/broadcast` - Broadcast\n`/addsudo` `/rmsudo`\n`/eval` - Run code\n`/restart` - Restart bot",
}

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Add to Group", url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("Help", callback_data="help_main")],
        [InlineKeyboardButton("Support", url=Config.SUPPORT_GROUP),
         InlineKeyboardButton("Channel", url=Config.SUPPORT_CHANNEL)],
    ])

def help_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Play",      callback_data="help_play"),
         InlineKeyboardButton("Controls",  callback_data="help_controls")],
        [InlineKeyboardButton("Queue",     callback_data="help_queue"),
         InlineKeyboardButton("Features",  callback_data="help_features")],
        [InlineKeyboardButton("Admin",     callback_data="help_admin"),
         InlineKeyboardButton("Sudo",      callback_data="help_sudo")],
        [InlineKeyboardButton("❌ Close",  callback_data="close")],
    ])


@Client.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        f"Hey **{message.from_user.first_name}**!\n"
        f"This is **{Config.BOT_NAME}**!\n\n"
        f"Advanced music player bot with Lyrics, Effects, Queue, History and more.\n\n"
        f"_Click Help for all commands._",
        reply_markup=main_kb()
    )


@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply_text(
        "**Commands — click a button for details:**",
        reply_markup=help_kb()
    )


@Client.on_callback_query(filters.regex("^help_"))
async def help_cb(client: Client, cb: CallbackQuery):
    section = cb.data.replace("help_", "")
    if section == "main":
        await cb.message.edit("**Commands — click a button for details:**", reply_markup=help_kb())
        return
    if section in HELP:
        await cb.message.edit(
            HELP[section],
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data="help_main"),
                InlineKeyboardButton("❌ Close", callback_data="close"),
            ]])
        )
    await cb.answer()
