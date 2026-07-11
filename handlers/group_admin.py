from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from database import (
    get_group, set_welcome_text, set_mandatory_chat, remove_mandatory_chat,
    toggle_filter, add_custom_word, remove_custom_word, get_global_mandatory
)
from git_sync import sync_database_to_github

group_admin_router = Router()


async def _require_admin(message: Message, bot: Bot) -> bool:
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ("administrator", "creator"):
        await message.answer("❌ Bu buyruqni faqat guruh adminlari ishlata oladi.")
        return False
    return True


@group_admin_router.message(Command("settings"), F.chat.type.in_({"group", "supergroup"}))
async def show_settings(message: Message, bot: Bot):
    if not await _require_admin(message, bot):
        return
    group = await get_group(message.chat.id)
    if group is None:
        await message.answer("⚠️ Bot bu guruhda hali admin sifatida ro'yxatdan o'tmagan.")
        return

    mandatory = group["mandatory_chat_title"] or "o'rnatilmagan"
    global_sub = await get_global_mandatory()
    global_text = global_sub["mandatory_chat_title"] if global_sub else "o'rnatilmagan"
    await message.answer(
        "⚙️ <b>Guruh sozlamalari</b>\n\n"
        f"👋 Xush kelibsiz xabari: {group['welcome_text']}\n"
        f"🔗 Havola filtri: {'✅ yoqilgan' if group['link_filter_enabled'] else '❌ o\u2019chirilgan'}\n"
        f"🌊 Anti-flood: {'✅ yoqilgan' if group['flood_filter_enabled'] else '❌ o\u2019chirilgan'}\n"
        f"🤬 So'kinish filtri: {'✅ yoqilgan' if group['swear_filter_enabled'] else '❌ o\u2019chirilgan'}\n"
        f"📢 Guruhning o'z majburiy obunasi: {mandatory}\n"
        f"🌐 Bot egasining global majburiy obunasi: {global_text} "
        f"<i>(o'zgartirib bo'lmaydi)</i>\n\n"
        "<b>Buyruqlar:</b>\n"
        "/setwelcome &lt;matn&gt; - xush kelibsiz xabari ({name} - ism)\n"
        "/setsub - majburiy obuna o'rnatish (forward qiling)\n"
        "/removesub - majburiy obunani bekor qilish\n"
        "/togglelinks /toggleflood /toggleswear - filtrlarni yoqish/o'chirish\n"
        "/addword &lt;so'z&gt; /removeword &lt;so'z&gt; - taqiqlangan so'zlar"
    )


@group_admin_router.message(Command("setwelcome"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_set_welcome(message: Message, bot: Bot, command: CommandObject):
    if not await _require_admin(message, bot):
        return
    if not command.args:
        await message.answer("Masalan: <code>/setwelcome Assalomu alaykum, {name}!</code>")
        return
    await set_welcome_text(message.chat.id, command.args)
    await sync_database_to_github(f"Xush kelibsiz xabari yangilandi: {message.chat.id}")
    await message.answer("✅ Xush kelibsiz xabari yangilandi.")


@group_admin_router.message(Command("setsub"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_set_sub_instructions(message: Message, bot: Bot):
    if not await _require_admin(message, bot):
        return
    await message.answer(
        "📌 Majburiy obuna qilmoqchi bo'lgan kanal/guruhdan xabarni shu yerga <b>forward</b> qiling.\n\n"
        "Bot o'sha yerda admin bo'lishi shart."
    )


@group_admin_router.message(F.forward_from_chat, F.chat.type.in_({"group", "supergroup"}))
async def process_setsub_forward(message: Message, bot: Bot):
    if not await _require_admin(message, bot):
        return
    chat = message.forward_from_chat
    try:
        bot_member = await bot.get_chat_member(chat.id, bot.id)
    except TelegramBadRequest:
        await message.answer("❌ Bot o'sha kanal/guruhda topilmadi.")
        return
    if bot_member.status not in ("administrator", "creator"):
        await message.answer("❌ Bot o'sha kanal/guruhda admin emas.")
        return

    link = f"https://t.me/{chat.username}" if chat.username else None
    if not link:
        try:
            link = await bot.export_chat_invite_link(chat.id)
        except TelegramBadRequest:
            await message.answer("❌ Bot taklif havolasi yarata olmadi.")
            return

    await set_mandatory_chat(message.chat.id, chat.id, link, chat.title)
    await sync_database_to_github(f"Majburiy obuna o'rnatildi: {message.chat.id} -> {chat.title}")
    await message.answer(f"✅ Majburiy obuna o'rnatildi: <b>{chat.title}</b>")


@group_admin_router.message(Command("removesub"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_remove_sub(message: Message, bot: Bot):
    if not await _require_admin(message, bot):
        return
    await remove_mandatory_chat(message.chat.id)
    await sync_database_to_github(f"Majburiy obuna bekor qilindi: {message.chat.id}")
    await message.answer("✅ Majburiy obuna talabi bekor qilindi.")


@group_admin_router.message(Command("togglelinks"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_toggle_links(message: Message, bot: Bot):
    if not await _require_admin(message, bot):
        return
    new_value = await toggle_filter(message.chat.id, "link_filter_enabled")
    await sync_database_to_github(f"Havola filtri o'zgartirildi: {message.chat.id}")
    await message.answer(f"🔗 Havola filtri: {'✅ yoqildi' if new_value else '❌ o\u2019chirildi'}")


@group_admin_router.message(Command("toggleflood"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_toggle_flood(message: Message, bot: Bot):
    if not await _require_admin(message, bot):
        return
    new_value = await toggle_filter(message.chat.id, "flood_filter_enabled")
    await sync_database_to_github(f"Anti-flood o'zgartirildi: {message.chat.id}")
    await message.answer(f"🌊 Anti-flood: {'✅ yoqildi' if new_value else '❌ o\u2019chirildi'}")


@group_admin_router.message(Command("toggleswear"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_toggle_swear(message: Message, bot: Bot):
    if not await _require_admin(message, bot):
        return
    new_value = await toggle_filter(message.chat.id, "swear_filter_enabled")
    await sync_database_to_github(f"So'kinish filtri o'zgartirildi: {message.chat.id}")
    await message.answer(f"🤬 So'kinish filtri: {'✅ yoqildi' if new_value else '❌ o\u2019chirildi'}")


@group_admin_router.message(Command("addword"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_add_word(message: Message, bot: Bot, command: CommandObject):
    if not await _require_admin(message, bot):
        return
    if not command.args:
        await message.answer("Masalan: <code>/addword so'z</code>")
        return
    await add_custom_word(message.chat.id, command.args.strip())
    await sync_database_to_github(f"Taqiqlangan so'z qo'shildi: {message.chat.id}")
    await message.answer("✅ So'z qo'shildi.")


@group_admin_router.message(Command("removeword"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_remove_word(message: Message, bot: Bot, command: CommandObject):
    if not await _require_admin(message, bot):
        return
    if not command.args:
        await message.answer("Masalan: <code>/removeword so'z</code>")
        return
    await remove_custom_word(message.chat.id, command.args.strip())
    await sync_database_to_github(f"Taqiqlangan so'z olib tashlandi: {message.chat.id}")
    await message.answer("✅ So'z olib tashlandi.")
