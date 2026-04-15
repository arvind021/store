"""
MOD Features:
  /special_link  — Store a file and get an EDITABLE link
  /update_link   — Update what a special link points to
  /mylinks       — List your special links
  /universal_link— Store a file accessible from any clone bot
  /custom_batch  — Batch of non-sequential message IDs
  /shortener     — Shorten any t.me link
"""

import uuid
import asyncio
import httpx

from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton
)
from config import Config
from database import (
    is_banned,
    save_special_link, get_special_link, update_special_link,
    get_user_special_links, delete_special_link,
    save_universal_link, get_universal_link,
    save_batch
)
from state import batch_sessions


# ─── guard helpers ───────────────────────────────────────
async def _guard(client, message):
    """Returns False (and replies) if user banned or not subbed."""
    uid = message.from_user.id
    if await is_banned(uid):
        await message.reply("❌ You are banned.")
        return False
    from plugins.start import check_force_sub, force_sub_buttons
    if not await check_force_sub(client, uid):
        await message.reply("⚠️ Join our channel first!",
                            reply_markup=await force_sub_buttons(client))
        return False
    return True


# ═══════════════════════════════════════════════════════════
#  /special_link
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("special_link") & filters.private)
async def cmd_special_link(client: Client, message: Message):
    if not await _guard(client, message):
        return

    if not message.reply_to_message or not _has_media(message.reply_to_message):
        await message.reply(
            "📎 **Reply to a file/photo/video** with /special_link\n\n"
            "The link you get will be **editable** — you can change what it points to later with /update_link."
        )
        return

    fwd = await message.reply_to_message.forward(Config.FILE_DB_CHANNEL)
    link_id = str(uuid.uuid4())[:10]
    await save_special_link(link_id, fwd.id, message.from_user.id,
                            name=_fname(message.reply_to_message))

    bot  = await client.get_me()
    link = f"https://t.me/{bot.username}?start=sl_{link_id}"

    await message.reply(
        f"✅ **Special Link Created!**\n\n"
        f"🔑 **Link ID:** `{link_id}`\n"
        f"🔗 **Link:**\n`{link}`\n\n"
        f"To update what this link points to:\n"
        f"`/update_link {link_id}` _(reply to new file)_",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Share", url=f"https://t.me/share/url?url={link}")]
        ])
    )


@Client.on_message(filters.command("update_link") & filters.private)
async def cmd_update_link(client: Client, message: Message):
    if not await _guard(client, message):
        return

    if len(message.command) < 2:
        await message.reply("**Usage:** Reply to a new file with\n`/update_link <link_id>`")
        return

    link_id = message.command[1]
    existing = await get_special_link(link_id)
    if not existing:
        await message.reply("❌ Special link not found.")
        return
    if existing["created_by"] != message.from_user.id:
        await message.reply("❌ This link doesn't belong to you.")
        return

    if not message.reply_to_message or not _has_media(message.reply_to_message):
        await message.reply("📎 Reply to a **new file** with /update_link <link_id>")
        return

    fwd = await message.reply_to_message.forward(Config.FILE_DB_CHANNEL)
    await update_special_link(link_id, fwd.id)
    await message.reply(f"✅ Special link `{link_id}` updated! Old links now serve the new file.")


@Client.on_message(filters.command("mylinks") & filters.private)
async def cmd_my_links(client: Client, message: Message):
    if not await _guard(client, message):
        return

    bot   = await client.get_me()
    links = get_user_special_links(message.from_user.id)
    text  = "🔗 **Your Special Links:**\n\n"
    count = 0
    async for doc in links:
        count += 1
        lnk = f"https://t.me/{bot.username}?start=sl_{doc['link_id']}"
        text += f"• `{doc['link_id']}` — [{doc.get('name','file')}]({lnk})\n"

    if count == 0:
        text = "You have no special links yet.\nUse /special_link (reply to a file) to create one."

    await message.reply(text, disable_web_page_preview=True)


# ═══════════════════════════════════════════════════════════
#  /universal_link
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("universal_link") & filters.private)
async def cmd_universal_link(client: Client, message: Message):
    if not await _guard(client, message):
        return

    if not message.reply_to_message or not _has_media(message.reply_to_message):
        await message.reply(
            "📎 **Reply to a file** with /universal_link\n\n"
            "This link works across any clone of this bot that shares the same database."
        )
        return

    fwd     = await message.reply_to_message.forward(Config.FILE_DB_CHANNEL)
    link_id = str(uuid.uuid4())[:10]
    await save_universal_link(link_id, fwd.id, message.from_user.id)

    bot  = await client.get_me()
    link = f"https://t.me/{bot.username}?start=ul_{link_id}"

    await message.reply(
        f"✅ **Universal Link Created!**\n\n"
        f"🔑 **Link ID:** `{link_id}`\n"
        f"🔗 **Link:**\n`{link}`\n\n"
        f"_This link is accessible from any clone bot sharing the same MongoDB._",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Share", url=f"https://t.me/share/url?url={link}")]
        ])
    )


# ═══════════════════════════════════════════════════════════
#  /custom_batch  — manually pick message IDs
# ═══════════════════════════════════════════════════════════

custom_batch_sessions = {}   # {user_id: [msg_id, ...]}


@Client.on_message(filters.command("custom_batch") & filters.private)
async def cmd_custom_batch(client: Client, message: Message):
    if not await _guard(client, message):
        return

    custom_batch_sessions[message.from_user.id] = []
    await message.reply(
        "📦 **Custom Batch Mode**\n\n"
        "Forward me any messages (from any chat) one by one.\n"
        "They don't have to be sequential!\n\n"
        "✅ /done  — Finish & get batch link\n"
        "❌ /cancel — Abort"
    )


@Client.on_message(filters.private & ~filters.command, group=10)
async def custom_batch_collector(client: Client, message: Message):
    """Intercept forwarded messages for custom_batch session."""
    user_id = message.from_user.id
    if user_id not in custom_batch_sessions:
        return
    if not message.forward_date:
        await message.reply("⚠️ Please **forward** messages, don't send originals.")
        return

    try:
        fwd = await message.forward(Config.FILE_DB_CHANNEL)
        custom_batch_sessions[user_id].append(fwd.id)
        n = len(custom_batch_sessions[user_id])
        await message.reply(f"✅ Message **#{n}** added! Forward more or /done.")
    except Exception as e:
        await message.reply(f"❌ Failed: `{e}`")


@Client.on_message(filters.command("done") & filters.private, group=10)
async def cmd_done_custom(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in custom_batch_sessions:
        return   # handled by batch.py

    files = custom_batch_sessions.pop(user_id)
    if not files:
        await message.reply("❌ No messages collected.")
        return

    batch_id = str(uuid.uuid4())[:8]
    await save_batch(batch_id, files, user_id)

    bot  = await client.get_me()
    link = f"https://t.me/{bot.username}?start=batch_{batch_id}"
    await message.reply(
        f"✅ **Custom Batch Saved!**\n\n"
        f"📦 Files : {len(files)}\n"
        f"🔗 Link  :\n`{link}`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Share", url=f"https://t.me/share/url?url={link}")]
        ])
    )


# ═══════════════════════════════════════════════════════════
#  /shortener — shorten a t.me or any link
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("shortener") & filters.private)
async def cmd_shortener(client: Client, message: Message):
    if not await _guard(client, message):
        return

    if len(message.command) < 2:
        await message.reply(
            "🔗 **Link Shortener**\n\n"
            "**Usage:** `/shortener <url>`\n\n"
            "Example:\n"
            "`/shortener https://t.me/yourbot?start=12345`"
        )
        return

    url = message.command[1]
    if not url.startswith("http"):
        await message.reply("❌ Please provide a valid URL starting with http/https.")
        return

    wait = await message.reply("⏳ Shortening…")
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            r = await http.get(
                "https://tinyurl.com/api-create.php",
                params={"url": url}
            )
        short = r.text.strip()
        if short.startswith("http"):
            await wait.edit(
                f"✅ **Shortened Link:**\n\n"
                f"**Original:**\n`{url}`\n\n"
                f"**Short:**\n`{short}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Share Short Link",
                                         url=f"https://t.me/share/url?url={short}")]
                ])
            )
        else:
            raise ValueError("Bad response")
    except Exception as e:
        await wait.edit(f"❌ Could not shorten link.\n`{e}`")


# ═══════════════════════════════════════════════════════════
#  DEEP-LINK HANDLER  sl_ and ul_ payloads
# ═══════════════════════════════════════════════════════════
# Extend the existing /start deep-link handling by registering
# a secondary handler.

@Client.on_message(filters.command("start") & filters.private, group=5)
async def start_special_payloads(client: Client, message: Message):
    if len(message.command) < 2:
        return

    payload = message.command[1]

    if payload.startswith("sl_"):
        link_id = payload[3:]
        doc = await get_special_link(link_id)
        if not doc:
            await message.reply("❌ Special link not found or deleted.")
            return
        try:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=Config.FILE_DB_CHANNEL,
                message_id=doc["msg_id"]
            )
        except Exception as e:
            await message.reply(f"❌ Could not retrieve file.\n`{e}`")

    elif payload.startswith("ul_"):
        link_id = payload[3:]
        doc = await get_universal_link(link_id)
        if not doc:
            await message.reply("❌ Universal link not found.")
            return
        try:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=Config.FILE_DB_CHANNEL,
                message_id=doc["msg_id"]
            )
        except Exception as e:
            await message.reply(f"❌ Could not retrieve file.\n`{e}`")


# ─── helpers ─────────────────────────────────────────────

def _has_media(m: Message) -> bool:
    return bool(
        m.document or m.video or m.audio or m.photo or
        m.voice or m.animation or m.video_note
    )

def _fname(m: Message) -> str:
    if m.document and m.document.file_name:  return m.document.file_name
    if m.video    and m.video.file_name:     return m.video.file_name
    if m.audio    and m.audio.file_name:     return m.audio.file_name
    if m.photo:    return "Photo"
    return "File"
