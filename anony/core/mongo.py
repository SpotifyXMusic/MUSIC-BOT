"""
MongoDB Database Handler V2
Handles: chats, users, blacklist, auth, sudo, settings, history, stats, group settings
"""

import motor.motor_asyncio
from config import Config

client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_DB_URI)
db = client.musicbot

chats_col     = db.chats
users_col     = db.users
blacklist_col = db.blacklist
auth_col      = db.auth_users
sudo_col      = db.sudo_users
settings_col  = db.settings
stats_col     = db.stats
history_col   = db.history
grp_settings  = db.group_settings


# ── CHATS ───────────────────────────────────────────────────────────────────

async def add_chat(chat_id: int):
    await chats_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

async def get_all_chats() -> list:
    docs = await chats_col.find({}, {"chat_id": 1}).to_list(length=None)
    return [d["chat_id"] for d in docs]

async def get_chat_count() -> int:
    return await chats_col.count_documents({})


# ── USERS ────────────────────────────────────────────────────────────────────

async def add_user(user_id: int, name: str = ""):
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "name": name}},
        upsert=True
    )

async def get_user_count() -> int:
    return await users_col.count_documents({})


# ── BLACKLIST ─────────────────────────────────────────────────────────────────

async def blacklist_chat(chat_id: int):
    await blacklist_col.update_one({"id": chat_id}, {"$set": {"id": chat_id, "type": "chat"}}, upsert=True)

async def blacklist_user(user_id: int):
    await blacklist_col.update_one({"id": user_id}, {"$set": {"id": user_id, "type": "user"}}, upsert=True)

async def unblacklist(id: int):
    await blacklist_col.delete_one({"id": id})

async def is_blacklisted(id: int) -> bool:
    return await blacklist_col.find_one({"id": id}) is not None

async def get_blacklist() -> list:
    return await blacklist_col.find({}).to_list(length=None)


# ── AUTH USERS ───────────────────────────────────────────────────────────────

async def auth_user(chat_id: int, user_id: int):
    await auth_col.update_one({"chat_id": chat_id, "user_id": user_id},
        {"$set": {"chat_id": chat_id, "user_id": user_id}}, upsert=True)

async def unauth_user(chat_id: int, user_id: int):
    await auth_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def is_authed(chat_id: int, user_id: int) -> bool:
    return await auth_col.find_one({"chat_id": chat_id, "user_id": user_id}) is not None

async def get_auth_users(chat_id: int) -> list:
    docs = await auth_col.find({"chat_id": chat_id}, {"user_id": 1}).to_list(length=None)
    return [d["user_id"] for d in docs]


# ── SUDO ──────────────────────────────────────────────────────────────────────

async def add_sudo(user_id: int):
    await sudo_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

async def remove_sudo(user_id: int):
    await sudo_col.delete_one({"user_id": user_id})

async def get_sudos() -> list:
    docs = await sudo_col.find({}, {"user_id": 1}).to_list(length=None)
    return [d["user_id"] for d in docs]


# ── SETTINGS ──────────────────────────────────────────────────────────────────

async def get_setting(chat_id: int, key: str, default=None):
    doc = await settings_col.find_one({"chat_id": chat_id})
    return doc.get(key, default) if doc else default

async def set_setting(chat_id: int, key: str, value):
    await settings_col.update_one({"chat_id": chat_id}, {"$set": {key: value}}, upsert=True)


# ── GROUP SETTINGS ────────────────────────────────────────────────────────────

async def get_group_settings(chat_id: int) -> dict:
    doc = await grp_settings.find_one({"chat_id": chat_id})
    if not doc:
        return {
            "auto_leave": True,
            "vote_skip": False,
            "vote_skip_percent": 51,
            "language": "en",
            "thumbnail": True,
            "announce": True,
        }
    return doc

async def update_group_setting(chat_id: int, key: str, value):
    await grp_settings.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, key: value}},
        upsert=True
    )


# ── PLAY STATS & HISTORY ──────────────────────────────────────────────────────

async def increment_play_count():
    await stats_col.update_one({"_id": "global"}, {"$inc": {"plays": 1}}, upsert=True)

async def get_play_count() -> int:
    doc = await stats_col.find_one({"_id": "global"})
    return doc.get("plays", 0) if doc else 0

async def add_to_history(chat_id: int, user_id: int, title: str, url: str, duration: str):
    """Add song to history"""
    import time
    await history_col.insert_one({
        "chat_id": chat_id,
        "user_id": user_id,
        "title": title,
        "url": url,
        "duration": duration,
        "timestamp": time.time()
    })
    # Keep last 50 per chat
    count = await history_col.count_documents({"chat_id": chat_id})
    if count > 50:
        oldest = await history_col.find({"chat_id": chat_id}).sort("timestamp", 1).limit(count - 50).to_list(length=None)
        ids = [d["_id"] for d in oldest]
        await history_col.delete_many({"_id": {"$in": ids}})

async def get_history(chat_id: int, limit: int = 10) -> list:
    docs = await history_col.find({"chat_id": chat_id}).sort("timestamp", -1).limit(limit).to_list(length=None)
    return docs

async def get_top_songs(chat_id: int = None, limit: int = 10) -> list:
    match = {"chat_id": chat_id} if chat_id else {}
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$title", "count": {"$sum": 1}, "url": {"$first": "$url"}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    return await history_col.aggregate(pipeline).to_list(length=None)

async def get_top_requesters(chat_id: int, limit: int = 10) -> list:
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    return await history_col.aggregate(pipeline).to_list(length=None)
