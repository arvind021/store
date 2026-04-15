from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import is_banned
from state import batch_sessions

# All media types we accept
MEDIA_FILTER = (
    filters.document  | filters.video    | filters.audio  |
    filters.photo     | filters.voice    | filters.animation |
    filters.video_note
)


@Client.on_message(filters.private & MEDIA_FILTER & ~filters.command)
async def handle_media(client: Client, message: Message):
    user_id = message.from_user.id

    if await is_banned(user_id):
        return

    # ── Force-sub check ──────────────────────────────────
    from plugins.start import check_force_sub, force_sub_buttons
    if not await check_force_sub(client, user_id):
        await message.reply(
            "⚠️ Join our channel first!",
            reply_markup=await force_sub_buttons(client)
        )
        return

    # ── BATCH MODE: user is collecting files ─────────────
    if user_id in batch_sessions:
        await _add_to_batch(client, message, user_id)
        return

    # ── SINGLE FILE STORE ─────────────────────────────────
    await _store_single(client, message)


# ─────────────────────────────────────────────────────────
async def _store_single(client: Client, message: Message):
    """Forward file to DB channel and return shareable link."""
    try:
        fwd = await message.forward(Config.FILE_DB_CHANNEL)
    except Exception as e:
        await message.reply(f"❌ Could not store file!\n`{e}`")
        return

    bot   = await client.get_me()
    link  = f"https://t.me/{bot.username}?start={fwd.id}"
    fname = _get_filename(message)

    await message.reply(
        f"✅ **File Stored!**\n\n"
        f"📄 **Name:** `{fname}`\n"
        f"🔗 **Link:**\n`{link}`\n\n"
        f"Anyone with this link can access the file.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔗 Share Link",
                url=f"https://t.me/share/url?url={link}"
            )]
        ])
    )


async def _add_to_batch(client: Client, message: Message, user_id: int):
    """Add file to the user's active batch session."""
    try:
        fwd = await message.forward(Config.FILE_DB_CHANNEL)
        batch_sessions[user_id].append(fwd.id)
        count = len(batch_sessions[user_id])
        await message.reply(
            f"📦 File **#{count}** added to batch!\n"
            "Send more files or /done to finish."
        )
    except Exception as e:
        await message.reply(f"❌ Failed to add file: `{e}`")


def _get_filename(message: Message) -> str:
    if message.document   and message.document.file_name:
        return message.document.file_name
    if message.video      and message.video.file_name:
        return message.video.file_name
    if message.audio      and message.audio.file_name:
        return message.audio.file_name
    if message.photo:       return "Photo"
    if message.voice:       return "Voice Message"
    if message.video_note:  return "Video Note"
    if message.animation:   return "GIF"
    return "Unknown"
