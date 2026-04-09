# 🎵 MusicBot V2 - Advanced Telegram Music Bot

> Lyrics | Thumbnail Cards | Audio Effects | Vote Skip | Playlist | History | Auto-Leave | Progress Bar

---

## ✨ New Features in V2

| Feature | Command | Details |
|---------|---------|---------|
| 🎵 Lyrics | `/lyrics` | Free - no API key needed |
| 🖼 Thumbnail Cards | Auto | Beautiful Now Playing cards |
| 📊 Progress Bar | `/now` | Live time progress |
| 🎚 Audio Effects | `/effect` `/bass` `/nightcore` etc | 12 effects via FFmpeg |
| ⚡ Speed Control | `/speed 1.5` | 0.5x to 2.0x |
| 👍 Vote Skip | `/voteskip` | Democratic skip |
| 📋 Playlist | `/playlist <URL>` | Import YouTube playlists |
| 📜 History | `/history` | Recently played songs |
| 🏆 Top Songs | `/topsongs` | Most played in group |
| 🧹 Auto Cleanup | Auto | Delete old downloads |
| 🛡 Flood Protection | Auto | 5s cooldown per user |
| ⚙️ Settings Panel | `/settings` | Toggle features per group |
| 🚗 Auto Leave | Auto | Leave when idle |

---

## 🚀 Deploy on Railway (Recommended)

1. Fork this repo to your GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables (see below)
4. Click Deploy!

---

## ⚙️ Environment Variables

Fill these in Railway dashboard or `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `STRING_SESSION` | ✅ | Pyrogram string session (run `generate_session.py`) |
| `MONGO_DB_URI` | ✅ | Free MongoDB Atlas cluster |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `BOT_USERNAME` | ✅ | Bot username without @ |
| `BOT_NAME` | ❌ | Display name (default: MusicBot) |
| `OWNER_NAME` | ❌ | Your name |
| `SUPPORT_GROUP` | ❌ | Your support group link |
| `SUPPORT_CHANNEL` | ❌ | Your channel link |
| `COOKIES_URL` | ❌ | YouTube cookies URL (fixes VPS IP blocks) |
| `DURATION_LIMIT` | ❌ | Max song duration in minutes (default: 180) |
| `PLAYLIST_FETCH_LIMIT` | ❌ | Max playlist songs (default: 25) |
| `AUTO_LEAVE_DELAY` | ❌ | Idle leave delay in seconds (default: 300) |

**No extra API keys needed for any feature!**

---

## 📋 All Commands

### 🎵 Play
```
/play <song/URL>       - Play audio
/vplay <song/URL>      - Play video (480p)
/stream <song/URL>     - Same as vplay
/search <query>        - Search & pick
/playlist <URL>        - Import YouTube playlist
```

### ⏯ Controls (Admin/Auth)
```
/pause    /resume    /skip    /stop
/seek <s> /seekback <s>
/mute     /unmute
/loop     /repeat
```

### 📋 Queue
```
/queue    /q         - Show queue
/now      /np        - Now playing + progress bar
/remove <pos>        - Remove from queue
/clearqueue          - Clear all
/voteskip            - Vote to skip
```

### 🎵 Music Features
```
/lyrics [song]       - Get lyrics (free, no API key)
/effect              - Open effects menu
/bass                - Bass boost
/nightcore           - Speed + pitch up
/slow                - Slow version
/8d                  - 8D audio
/reverb              - Reverb effect
/karaoke             - Remove vocals
/vocalboost          - Boost vocals
/speed <0.5-2.0>     - Custom speed
/cleareffect         - Remove effect
```

### 📊 Stats & History
```
/history             - Recently played
/topsongs            - Most played songs
/toprequests         - Top requesters
/ping                - Ping + system stats
/stats               - Full bot stats (sudo)
```

### ⚙️ Settings & Admin
```
/settings            - Group settings panel
/lang                - Change language
/auth    /unauth     - Authorize users
/authlist            - Show authorized users
/reload              - Reload admin cache
```

### 🔒 Sudo
```
/stats    /ac    /activevc
/broadcast         - Broadcast to all chats
/addsudo /rmsudo  - Manage sudo users
/blacklist /unblacklist
/eval              - Run Python code
/logs              - Get log file
/restart           - Restart bot
```

---

## 🍪 YouTube Cookie Setup (Optional)

If bot can't play (VPS IP blocked by YouTube):

1. Install "Get cookies.txt LOCALLY" browser extension
2. Go to YouTube, export cookies (Netscape format)
3. Upload to [batbin.me](https://batbin.me)
4. Set `COOKIES_URL` in env variables

---

## 📁 Project Structure

```
MusicBotV2/
├── anony/
│   ├── core/
│   │   ├── bot.py          # Pyrogram client
│   │   ├── calls.py        # PyTgCalls manager
│   │   ├── mongo.py        # Database (history, stats, settings)
│   │   └── __init__.py     # Userbot + CallManager init
│   ├── helpers/
│   │   ├── youtube.py      # yt-dlp: search, download, playlist
│   │   ├── queue.py        # Queue system
│   │   ├── admins.py       # Permission checks
│   │   ├── thumbnail.py    # Now Playing card generator
│   │   ├── lyrics.py       # Free lyrics fetcher
│   │   ├── filters_audio.py# FFmpeg audio effects
│   │   ├── flood.py        # Rate limiting + vote skip
│   │   ├── autoleave.py    # Auto-leave when idle
│   │   └── cleanup.py      # Auto-delete old downloads
│   ├── plugins/            # All commands
│   └── locales/            # Language files
├── cookies/                # YouTube cookie files
├── downloads/              # Auto-created, auto-cleaned
├── config.py
├── __main__.py
├── requirements.txt
├── Dockerfile
├── railway.toml
└── .env.sample
```

---

**MIT License** | No extra API keys needed | Railway ready
