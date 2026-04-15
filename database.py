from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import time

# ── Connect ───────────────────────────────────────────────
_client   = AsyncIOMotorClient(Config.DATABASE_URL)
db        = _client[Config.DATABASE_NAME]

users_col          = db["users"]
banned_col         = db["banned"]
batches_col        = db["batches"]
special_links_col  = db["special_links"]   # editable links
universal_links_col= db["universal_links"] # multi-clone links
user_settings_col  = db["user_settings"]   # per-user settings

# ═══════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════

async def add_user(user_id: int, name: str):
    if not await users_col.find_one({"user_id": user_id}):
        await users_col.insert_one({
            "user_id":  user_id,
            "name":     name,
            "joined":   time.time()
        })

async def get_all_users():
    return users_col.find({})

async def get_user_count() -> int:
    return await users_col.count_documents({})

# ═══════════════════════════════════════════════════════════
#  BAN / UNBAN
# ═══════════════════════════════════════════════════════════

async def ban_user(user_id: int):
    await banned_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "banned_at": time.time()}},
        upsert=True
    )
    # remove from active users
    await users_col.delete_one({"user_id": user_id})

async def unban_user(user_id: int):
    await banned_col.delete_one({"user_id": user_id})

async def is_banned(user_id: int) -> bool:
    return bool(await banned_col.find_one({"user_id": user_id}))

# ═══════════════════════════════════════════════════════════
#  BATCHES
# ═══════════════════════════════════════════════════════════

async def save_batch(batch_id: str, messages: list, user_id: int):
    await batches_col.insert_one({
        "batch_id":    batch_id,
        "messages":    messages,   # list of message IDs in FILE_DB_CHANNEL
        "created_by":  user_id,
        "created_at":  time.time()
    })

async def get_batch(batch_id: str):
    return await batches_col.find_one({"batch_id": batch_id})

# ═══════════════════════════════════════════════════════════
#  SPECIAL LINKS  (editable — owner can update target)
# ═══════════════════════════════════════════════════════════

async def save_special_link(link_id: str, msg_id: int, user_id: int, name: str = ""):
    await special_links_col.insert_one({
        "link_id":    link_id,
        "msg_id":     msg_id,
        "created_by": user_id,
        "name":       name,
        "created_at": time.time()
    })

async def get_special_link(link_id: str):
    return await special_links_col.find_one({"link_id": link_id})

async def update_special_link(link_id: str, new_msg_id: int):
    await special_links_col.update_one(
        {"link_id": link_id},
        {"$set": {"msg_id": new_msg_id, "updated_at": time.time()}}
    )

async def get_user_special_links(user_id: int):
    return special_links_col.find({"created_by": user_id})

async def delete_special_link(link_id: str, user_id: int):
    await special_links_col.delete_one({"link_id": link_id, "created_by": user_id})

# ═══════════════════════════════════════════════════════════
#  UNIVERSAL LINKS  (multi-clone: same link_id, any clone bot)
# ═══════════════════════════════════════════════════════════

async def save_universal_link(link_id: str, msg_id: int, user_id: int):
    await universal_links_col.insert_one({
        "link_id":    link_id,
        "msg_id":     msg_id,
        "created_by": user_id,
        "created_at": time.time()
    })

async def get_universal_link(link_id: str):
    return await universal_links_col.find_one({"link_id": link_id})

# ═══════════════════════════════════════════════════════════
#  USER SETTINGS
# ═══════════════════════════════════════════════════════════

DEFAULT_SETTINGS = {
    "auto_delete":    False,   # auto-delete sent files after 5 min
    "notify_store":   True,    # send confirmation when file is stored
    "show_filename":  True,    # show filename in link message
    "language":       "en",    # language (en / hi)
}

async def get_settings(user_id: int) -> dict:
    doc = await user_settings_col.find_one({"user_id": user_id})
    if not doc:
        return DEFAULT_SETTINGS.copy()
    return {**DEFAULT_SETTINGS, **doc.get("settings", {})}

async def update_settings(user_id: int, key: str, value):
    await user_settings_col.update_one(
        {"user_id": user_id},
        {"$set": {f"settings.{key}": value}},
        upsert=True
    )
