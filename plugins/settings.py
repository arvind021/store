from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_settings, is_banned


@Client.on_message(filters.command("settings") & filters.private)
async def cmd_settings(client: Client, message: Message):
    user_id = message.from_user.id
    if await is_banned(user_id):
        return

    from plugins.start import check_force_sub, force_sub_buttons
    if not await check_force_sub(client, user_id):
        await message.reply("⚠️ Join our channel first!",
                            reply_markup=await force_sub_buttons(client))
        return

    s = await get_settings(user_id)
    await message.reply(
        "⚙️ **Your Settings**\n\n"
        f"🗑 Auto-Delete files after sending : {'✅' if s['auto_delete'] else '❌'}\n"
        f"🔔 Notify when file stored         : {'✅' if s['notify_store'] else '❌'}\n"
        f"📄 Show filename in link message   : {'✅' if s['show_filename'] else '❌'}\n"
        f"🌐 Language                        : `{s['language'].upper()}`",
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
