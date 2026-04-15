from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import save_batch, is_banned
from state import batch_sessions
import uuid


@Client.on_message(filters.command("batch") & filters.private)
async def cmd_batch(client: Client, message: Message):
    user_id = message.from_user.id

    if await is_banned(user_id):
        return

    # Check force-sub
    from plugins.start import check_force_sub, force_sub_buttons
    if not await check_force_sub(client, user_id):
        await message.reply(
            "⚠️ Join our channel first!",
            reply_markup=await force_sub_buttons(client)
        )
        return

    batch_sessions[user_id] = []
    await message.reply(
        "📦 **Batch Mode Activated!**\n\n"
        "Now send me all the files you want to store together.\n\n"
        "✅ Send **/done** when finished.\n"
        "❌ Send **/cancel** to abort."
    )


@Client.on_message(filters.command("done") & filters.private)
async def cmd_done(client: Client, message: Message):
    user_id = message.from_user.id

    if user_id not in batch_sessions:
        await message.reply("❌ No active batch session.\nUse /batch to start.")
        return

    files = batch_sessions.pop(user_id)

    if not files:
        await message.reply("❌ No files collected. Batch cancelled.")
        return

    batch_id = str(uuid.uuid4())[:8]
    await save_batch(batch_id, files, user_id)

    bot  = await client.get_me()
    link = f"https://t.me/{bot.username}?start=batch_{batch_id}"

    await message.reply(
        f"✅ **Batch Saved!**\n\n"
        f"📦 **Files:** {len(files)}\n"
        f"🔑 **Batch ID:** `{batch_id}`\n"
        f"🔗 **Link:**\n`{link}`\n\n"
        f"Anyone using this link will receive all {len(files)} files at once!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔗 Share Batch",
                url=f"https://t.me/share/url?url={link}"
            )]
        ])
    )


@Client.on_message(filters.command("cancel") & filters.private)
async def cmd_cancel(_, message: Message):
    user_id = message.from_user.id
    if user_id in batch_sessions:
        count = len(batch_sessions.pop(user_id))
        await message.reply(f"❌ Batch cancelled. ({count} file(s) discarded)")
    else:
        await message.reply("No active batch session.")
