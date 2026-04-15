from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import ban_user, unban_user, is_banned, get_all_users, get_user_count
import asyncio

# ── Owner-only filter ─────────────────────────────────────
owner_filter = filters.user(Config.OWNER_ID) & filters.private


# ═══════════════════════════════════════════════════════════
#  BAN
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("ban") & owner_filter)
async def cmd_ban(_, message: Message):
    if len(message.command) < 2:
        await message.reply("**Usage:** `/ban <user_id>`")
        return
    try:
        uid = int(message.command[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return

    if uid == Config.OWNER_ID:
        await message.reply("❌ Cannot ban the owner!")
        return

    await ban_user(uid)
    await message.reply(f"✅ User `{uid}` has been **banned**.")


# ═══════════════════════════════════════════════════════════
#  UNBAN
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("unban") & owner_filter)
async def cmd_unban(_, message: Message):
    if len(message.command) < 2:
        await message.reply("**Usage:** `/unban <user_id>`")
        return
    try:
        uid = int(message.command[1])
    except ValueError:
        await message.reply("❌ Invalid user ID.")
        return

    if not await is_banned(uid):
        await message.reply(f"ℹ️ User `{uid}` is not banned.")
        return

    await unban_user(uid)
    await message.reply(f"✅ User `{uid}` has been **unbanned**.")


# ═══════════════════════════════════════════════════════════
#  STATS
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("stats") & owner_filter)
async def cmd_stats(_, message: Message):
    count = await get_user_count()
    await message.reply(
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total Users: **{count}**"
    )


# ═══════════════════════════════════════════════════════════
#  BROADCAST
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("broadcast") & owner_filter)
async def cmd_broadcast(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply(
            "📡 **Reply to a message** with /broadcast to send it to all users."
        )
        return

    notice = await message.reply("📡 Broadcasting…")
    ok = fail = 0

    async for user in await get_all_users():
        try:
            await message.reply_to_message.copy(user["user_id"])
            ok += 1
            await asyncio.sleep(0.05)      # flood control
        except Exception:
            fail += 1

    await notice.edit(
        f"✅ **Broadcast Complete!**\n\n"
        f"✔️ Success : **{ok}**\n"
        f"❌ Failed  : **{fail}**"
    )
