import motor.motor_asyncio
from config import Config

client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_DB_URI)
db = client.musicbot

chats_col    = db.chats
users_col    = db.users
blacklist_col= db.blacklist
auth_col     = db.auth_users
sudo_col     = db.sudo_users
settings_col = db.settings
stats_col    = db.stats
history_col  = db.history


async def add_chat(chat_id: int):
    await chats_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

async def get_all_chats():
    docs = await chats_col.find({}, {"chat_id": 1}).to_list(length=None)
    return [d["chat_id"] for d in docs]

async def get_chat_count():
    return await chats_col.count_documents({})

async def add_user(user_id: int, name: str = ""):
    await users_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id, "name": name}}, upsert=True)

async def get_user_count():
    return await users_col.count_documents({})

async def blacklist_add(id: int, type: str):
    await blacklist_col.update_one({"id": id}, {"$set": {"id": id, "type": type}}, upsert=True)

async def blacklist_remove(id: int):
    await blacklist_col.delete_one({"id": id})

async def is_blacklisted(id: int) -> bool:
    return await blacklist_col.find_one({"id": id}) is not None

async def get_blacklist():
    return await blacklist_col.find({}).to_list(length=None)

async def auth_user(chat_id: int, user_id: int):
    await auth_col.update_one({"chat_id": chat_id, "user_id": user_id},
        {"$set": {"chat_id": chat_id, "user_id": user_id}}, upsert=True)

async def unauth_user(chat_id: int, user_id: int):
    await auth_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def is_authed(chat_id: int, user_id: int) -> bool:
    return await auth_col.find_one({"chat_id": chat_id, "user_id": user_id}) is not None

async def get_auth_users(chat_id: int):
    docs = await auth_col.find({"chat_id": chat_id}, {"user_id": 1}).to_list(length=None)
    return [d["user_id"] for d in docs]

async def add_sudo(user_id: int):
    await sudo_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

async def remove_sudo(user_id: int):
    await sudo_col.delete_one({"user_id": user_id})

async def get_sudos():
    docs = await sudo_col.find({}, {"user_id": 1}).to_list(length=None)
    return [d["user_id"] for d in docs]

async def get_setting(chat_id: int, key: str, default=None):
    doc = await settings_col.find_one({"chat_id": chat_id})
    return doc.get(key, default) if doc else default

async def set_setting(chat_id: int, key: str, value):
    await settings_col.update_one({"chat_id": chat_id}, {"$set": {key: value}}, upsert=True)

async def increment_plays():
    await stats_col.update_one({"_id": "global"}, {"$inc": {"plays": 1}}, upsert=True)

async def get_plays():
    doc = await stats_col.find_one({"_id": "global"})
    return doc.get("plays", 0) if doc else 0

async def add_history(chat_id: int, user_id: int, title: str, url: str, duration: str):
    import time
    await history_col.insert_one({
        "chat_id": chat_id, "user_id": user_id,
        "title": title, "url": url,
        "duration": duration, "ts": time.time()
    })
    count = await history_col.count_documents({"chat_id": chat_id})
    if count > 50:
        oldest = await history_col.find({"chat_id": chat_id}).sort("ts", 1).limit(count - 50).to_list(length=None)
        await history_col.delete_many({"_id": {"$in": [d["_id"] for d in oldest]}})

async def get_history(chat_id: int, limit: int = 10):
    return await history_col.find({"chat_id": chat_id}).sort("ts", -1).limit(limit).to_list(length=None)

async def get_top_songs(chat_id: int, limit: int = 10):
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {"_id": "$title", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    return await history_col.aggregate(pipeline).to_list(length=None)
