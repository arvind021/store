from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import Config
from database import add_user, is_banned
import asyncio


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

async def check_force_sub(client: Client, user_id: int) -> bool:
    """Return True if force-sub is disabled OR user has joined."""
    if Config.FORCE_SUB_CHANNEL == "0":
        return True
    try:
        member = await client.get_chat_member(
            int(Config.FORCE_SUB_CHANNEL), user_id
        )
        return member.status.value in ("member", "administrator", "creator", "owner")
    except Exception:
        return False


async def force_sub_buttons(client: Client) -> InlineKeyboardMarkup:
    try:
        link = await client.export_chat_invite_link(int(Config.FORCE_SUB_CHANNEL))
    except Exception:
        link = "https://t.me"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=link)],
        [InlineKeyboardButton("✅ I Joined", callback_data="check_sub")]
    ])


# ═══════════════════════════════════════════════════════════
#  /start
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user_id   = message.from_user.id
    user_name = message.from_user.first_name

    # Banned?
    if await is_banned(user_id):
        await message.reply("❌ You are **banned** from using this bot.")
        return

    # Save user
    await add_user(user_id, user_name)

    # Force Subscribe check
    if not await check_force_sub(client, user_id):
        await message.reply(
            "⚠️ **Access Denied!**\n\n"
            "You must join our channel before using the bot.\n"
            "👇 Join below and click **I Joined**.",
            reply_markup=await force_sub_buttons(client)
        )
        return

    # Deep-link payload?
    if len(message.command) > 1:
        payload = message.command[1]
        if payload.startswith("batch_"):
            await _send_batch(client, message, payload[6:])
        else:
            await _send_file(client, message, payload)
        return

    # Default welcome
    await message.reply(
        f"👋 **Hello {user_name}!**\n\n"
        "I am a **File Store Bot** 🤖\n"
        "Send me any file and I'll give you a **permanent shareable link**!\n\n"
        "📌 Commands:\n"
        "• /batch — Store multiple files at once\n"
        "• /settings — Your preferences\n"
        "• /help  — All commands\n"
        "• /about — About this bot",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help",     callback_data="help"),
                InlineKeyboardButton("ℹ️ About",    callback_data="about")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu"),
                InlineKeyboardButton("📊 Stats",    callback_data="stats_cb")
            ],
            [InlineKeyboardButton("⚡ CREATE MY OWN CLONE", callback_data="clone_info")],
        ])
    )


# ═══════════════════════════════════════════════════════════
#  /help  /about
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(_, message: Message):
    await message.reply(
        "**📖 Help Menu**\n\n"
        "**👤 User Commands:**\n"
        "`/start`        — Start the bot\n"
        "`/help`         — Show this menu\n"
        "`/about`        — About the bot\n"
        "`/batch`        — Store multiple files\n"
        "`/custom_batch` — Store random messages\n"
        "`/shortener`    — Shorten a link\n"
        "`/settings`     — Your preferences\n"
        "`/cancel`       — Cancel active session\n\n"
        "**🛡️ Mod / Admin Commands:**\n"
        "`/special_link`   — Editable link\n"
        "`/universal_link` — Multi-clone link\n"
        "`/update_link`    — Update special link target\n"
        "`/mylinks`        — Your special links\n"
        "`/ban <id>`       — Ban a user\n"
        "`/unban <id>`     — Unban a user\n"
        "`/stats`          — Bot statistics\n"
        "`/broadcast`      — Broadcast message\n\n"
        "**📤 How to store a file?**\n"
        "Just send any file/photo/video → get a permanent link instantly!"
    )


@Client.on_message(filters.command("about") & filters.private)
async def about_cmd(_, message: Message):
    await message.reply(
        "**🤖 File Store Bot**\n\n"
        "A premium Telegram bot to store files permanently "
        "and share them via links.\n\n"
        "• Powered by **Pyrogram**\n"
        "• Database: **MongoDB**\n"
        "• Features: Force-Sub, Batch, Broadcast, Ban/Unban"
    )


# ═══════════════════════════════════════════════════════════
#  CALLBACK — check sub / help / about
# ═══════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^check_sub$"))
async def cb_check_sub(client: Client, cb: CallbackQuery):
    if await check_force_sub(client, cb.from_user.id):
        await cb.message.delete()
        await cb.message.reply(
            f"✅ **Verified!** Welcome {cb.from_user.first_name}!\n"
            "Now send me any file to get started."
        )
    else:
        await cb.answer("❌ You haven't joined yet!", show_alert=True)


@Client.on_callback_query(filters.regex("^help$"))
async def cb_help(_, cb: CallbackQuery):
    await cb.message.edit_text(
        "**📖 Help Menu**\n\n"
        "`/batch`  — Store multiple files\n"
        "`/cancel` — Cancel batch\n"
        "Just send a file to store it!\n\n"
        "_Admin: /ban /unban /stats /broadcast_",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]
        )
    )


@Client.on_callback_query(filters.regex("^about$"))
async def cb_about(_, cb: CallbackQuery):
    await cb.message.edit_text(
        "**🤖 File Store Bot**\n\n"
        "Permanent file storage with shareable links.\n"
        "Built with Pyrogram + MongoDB.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]
        )
    )


@Client.on_callback_query(filters.regex("^back_home$"))
async def cb_back(_, cb: CallbackQuery):
    await cb.message.edit_text(
        "👋 **Welcome back!**\n\nSend any file or use /help.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help",     callback_data="help"),
                InlineKeyboardButton("ℹ️ About",    callback_data="about")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu"),
                InlineKeyboardButton("📊 Stats",    callback_data="stats_cb")
            ],
            [InlineKeyboardButton("⚡ CREATE MY OWN CLONE", callback_data="clone_info")],
        ])
    )


@Client.on_callback_query(filters.regex("^clone_info$"))
async def cb_clone_info(_, cb: CallbackQuery):
    await cb.message.edit_text(
        "⚡ **Create Your Own Clone**\n\n"
        "You can deploy your own File Store Bot!\n\n"
        "**Steps:**\n"
        "1️⃣ Get API credentials from https://my.telegram.org\n"
        "2️⃣ Create a bot via @BotFather\n"
        "3️⃣ Setup MongoDB (Atlas free tier works)\n"
        "4️⃣ Fill in your `.env` file\n"
        "5️⃣ Run `python main.py`\n\n"
        "📂 Full source code is available in the bot package.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_home")]
        ])
    )


@Client.on_callback_query(filters.regex("^stats_cb$"))
async def cb_stats(_, cb: CallbackQuery):
    from database import get_user_count
    count = await get_user_count()
    await cb.answer(f"👥 Total Users: {count}", show_alert=True)


@Client.on_callback_query(filters.regex("^settings_menu$"))
async def cb_settings_menu(_, cb: CallbackQuery):
    from database import get_settings
    s = await get_settings(cb.from_user.id)
    await cb.message.edit_text(
        "⚙️ **Your Settings**\n\n"
        f"🗑 Auto-Delete files after sending : {'✅' if s['auto_delete'] else '❌'}\n"
        f"🔔 Notify when file stored          : {'✅' if s['notify_store'] else '❌'}\n"
        f"📄 Show filename in link message    : {'✅' if s['show_filename'] else '❌'}\n"
        f"🌐 Language                         : `{s['language'].upper()}`\n\n"
        "Tap a button to toggle:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'✅' if s['auto_delete'] else '❌'} Auto-Delete",
                    callback_data="toggle_auto_delete"
                ),
                InlineKeyboardButton(
                    f"{'✅' if s['notify_store'] else '❌'} Notify Store",
                    callback_data="toggle_notify_store"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if s['show_filename'] else '❌'} Show Filename",
                    callback_data="toggle_show_filename"
                ),
                InlineKeyboardButton(
                    f"🌐 {'EN' if s['language']=='en' else 'HI'} → Switch",
                    callback_data="toggle_language"
                )
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="back_home")]
        ])
    )


@Client.on_callback_query(filters.regex("^toggle_"))
async def cb_toggle_setting(_, cb: CallbackQuery):
    from database import get_settings, update_settings
    key_map = {
        "toggle_auto_delete":   "auto_delete",
        "toggle_notify_store":  "notify_store",
        "toggle_show_filename": "show_filename",
        "toggle_language":      "language",
    }
    action = cb.data
    key = key_map.get(action)
    if not key:
        return

    s = await get_settings(cb.from_user.id)
    if key == "language":
        new_val = "hi" if s["language"] == "en" else "en"
    else:
        new_val = not s[key]

    await update_settings(cb.from_user.id, key, new_val)
    # refresh settings panel
    await cb_settings_menu(_, cb)


# ═══════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════

async def _send_file(client: Client, message: Message, payload: str):
    try:
        msg_id = int(payload)
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=Config.FILE_DB_CHANNEL,
            message_id=msg_id
        )
    except Exception as e:
        await message.reply(f"❌ File not found!\n`{e}`")


async def _send_batch(client: Client, message: Message, batch_id: str):
    from database import get_batch
    batch = await get_batch(batch_id)
    if not batch:
        await message.reply("❌ Batch not found or deleted!")
        return

    notice = await message.reply(
        f"📦 Sending **{len(batch['messages'])}** file(s)…"
    )
    ok, fail = 0, 0
    for mid in batch["messages"]:
        try:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=Config.FILE_DB_CHANNEL,
                message_id=mid
            )
            ok += 1
            await asyncio.sleep(0.4)
        except Exception:
            fail += 1

    await notice.edit(
        f"✅ Done! Sent: **{ok}** | Failed: **{fail}**"
    )
