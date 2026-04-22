# AI Features Plugin
# Commands: /ask, /mood, /songinfo, /recommend, /translate, /moodplay

from pyrogram import filters, types

from anony import app, config, yt, queue
from anony.core.ai import (
    ai_chat, detect_mood, get_song_recommendation,
    get_mood_songs, get_song_info, translate_text
)
from anony.helpers import Track, utils


def ai_required(func):
    """Decorator to check if AI is enabled"""
    async def wrapper(_, message: types.Message):
        if not config.AI_ENABLED:
            return await message.reply_text(
                "<b>AI features are disabled.</b>\n\n"
                "<i>Add <code>GROQ_API_KEY</code> in your environment variables to enable AI.\n"
                "Get free API key from: groq.com</i>"
            )
        return await func(_, message)
    return wrapper


@app.on_message(filters.command(["ask", "ai"]) & ~app.bl_users)
@ai_required
async def ask_ai(_, message: types.Message):
    """/ask - Chat with AI"""
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Usage:</b> <code>/ask your question here</code>\n\n"
            "<i>Example: /ask suggest me a sad Hindi song</i>"
        )

    query = " ".join(message.command[1:])
    user_name = message.from_user.first_name if message.from_user else "User"

    sent = await message.reply_text("<b>Thinking...</b>")
    response = await ai_chat(query, user_name)

    await sent.edit_text(
        f"<b>AI Response</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"{response}"
    )


@app.on_message(filters.command(["mood"]) & filters.group & ~app.bl_users)
@ai_required
async def mood_detect(_, message: types.Message):
    """/mood - Detect mood and get song suggestions"""
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text(
            "<b>Usage:</b> <code>/mood [your feeling]</code>\n\n"
            "<i>Example: /mood aaj bahut khushi ho rahi hai</i>"
        )

    if message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    else:
        text = " ".join(message.command[1:])

    sent = await message.reply_text("<b>Detecting your mood...</b>")
    mood = await detect_mood(text)

    mood_emojis = {
        "happy": "😊", "sad": "😢", "romantic": "💕", "energetic": "⚡",
        "calm": "🌿", "angry": "😤", "party": "🎉", "devotional": "🙏",
        "motivational": "💪", "chill": "😎"
    }
    emoji = mood_emojis.get(mood, "🎵")

    # Get song suggestions for this mood
    songs = await get_mood_songs(mood, "Hindi")

    songs_text = ""
    for i, song in enumerate(songs, 1):
        songs_text += f"<b>{i}.</b> {song}\n"

    await sent.edit_text(
        f"{emoji} <b>Mood Detected: {mood.upper()}</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"<b>Suggested Songs:</b>\n\n"
        f"{songs_text}\n"
        f"<i>Use /play [song name] to play any song!</i>"
    )


@app.on_message(filters.command(["moodplay"]) & filters.group & ~app.bl_users)
@ai_required
async def mood_play(_, message: types.Message):
    """/moodplay - Play songs based on mood"""
    if len(message.command) < 2:
        moods = "happy | sad | romantic | energetic | calm | party | chill | motivational"
        return await message.reply_text(
            f"<b>Usage:</b> <code>/moodplay [mood]</code>\n\n"
            f"<b>Available moods:</b>\n<code>{moods}</code>"
        )

    mood = message.command[1].lower()
    sent = await message.reply_text(f"<b>Finding {mood} songs...</b>")

    songs = await get_mood_songs(mood, "Hindi")
    if not songs:
        return await sent.edit_text("<b>Could not find songs for this mood. Try again!</b>")

    # Search and queue first song
    first_song = songs[0]
    track = await yt.search(first_song, sent.id)
    if not track:
        return await sent.edit_text("<b>Could not find song on YouTube. Try /play manually.</b>")

    mention = message.from_user.mention if message.from_user else "User"
    track.user = mention
    position = queue.add(message.chat.id, track)

    songs_text = ""
    for i, song in enumerate(songs, 1):
        songs_text += f"<b>{i}.</b> {song}\n"

    await sent.edit_text(
        f"🎵 <b>Mood Playlist: {mood.upper()}</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"{songs_text}\n"
        f"<i>First song added to queue! Use /play for others.</i>"
    )


@app.on_message(filters.command(["songinfo", "sinfo"]) & ~app.bl_users)
@ai_required
async def song_info(_, message: types.Message):
    """/songinfo - Get info about a song"""
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Usage:</b> <code>/songinfo song name</code>\n\n"
            "<i>Example: /songinfo Tum Hi Ho Arijit Singh</i>"
        )

    query = " ".join(message.command[1:])
    sent = await message.reply_text("<b>Fetching song info...</b>")

    info = await get_song_info(query)
    await sent.edit_text(
        f"<b>Song Info</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"<b>Query:</b> {query}\n\n"
        f"{info}"
    )


@app.on_message(filters.command(["recommend", "similar"]) & filters.group & ~app.bl_users)
@ai_required
async def recommend_song(_, message: types.Message):
    """/recommend - Get song recommendation based on current or given song"""
    chat_id = message.chat.id

    if len(message.command) >= 2:
        song_name = " ".join(message.command[1:])
    else:
        # Use currently playing song
        current = queue.get_current(chat_id)
        if not current:
            return await message.reply_text(
                "<b>No song playing.</b>\n\n"
                "<i>Use: /recommend [song name] to get recommendations.</i>"
            )
        song_name = current.title

    sent = await message.reply_text("<b>Finding similar songs...</b>")
    recommendation = await get_song_recommendation(song_name)

    if not recommendation:
        return await sent.edit_text("<b>Could not get recommendation. Try again!</b>")

    await sent.edit_text(
        f"<b>Song Recommendation</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"<b>Based on:</b> {song_name}\n\n"
        f"<b>Try next:</b> {recommendation}\n\n"
        f"<i>Use /play {recommendation} to play it!</i>"
    )


@app.on_message(filters.command(["translate", "tr"]) & ~app.bl_users)
@ai_required
async def translate_cmd(_, message: types.Message):
    """/translate - Translate text"""
    if message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
        target = message.command[1] if len(message.command) > 1 else "English"
    elif len(message.command) > 2:
        target = message.command[1]
        text = " ".join(message.command[2:])
    elif len(message.command) > 1:
        text = " ".join(message.command[1:])
        target = "English"
    else:
        return await message.reply_text(
            "<b>Usage:</b>\n"
            "<code>/translate [language] [text]</code>\n"
            "<i>Or reply to a message: /translate Hindi</i>\n\n"
            "<b>Example:</b> <code>/translate Hindi How are you?</code>"
        )

    sent = await message.reply_text("<b>Translating...</b>")
    translated = await translate_text(text, target)

    await sent.edit_text(
        f"<b>Translation → {target}</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"{translated}"
    )


@app.on_message(filters.command(["aihelp"]) & ~app.bl_users)
async def ai_help(_, message: types.Message):
    """/aihelp - Show all AI commands"""
    status = "Enabled ✓" if config.AI_ENABLED else "Disabled — Add GROQ_API_KEY"
    await message.reply_text(
        f"<b>AI Features</b>\n"
        f"<code>━━━━━━━━━━━━━━━━</code>\n"
        f"<b>Status:</b> {status}\n\n"
        f"<b>/ask</b> [question] — Chat with AI\n"
        f"<b>/mood</b> [feeling] — Detect mood & get songs\n"
        f"<b>/moodplay</b> [mood] — Play songs by mood\n"
        f"<b>/recommend</b> — Get similar song suggestion\n"
        f"<b>/songinfo</b> [name] — Get song details\n"
        f"<b>/translate</b> [lang] [text] — Translate text\n\n"
        f"<b>Auto Moderation:</b>\n"
        f"— Bad words auto deleted\n"
        f"— 3 warnings then auto ban\n"
        f"<b>/warns</b> — Check user warnings\n"
        f"<b>/resetwarn</b> — Reset user warnings"
    )
