import asyncio

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import ADMIN_IDS
from database import (
    add_channel, remove_channel, get_channels, channels_count,
    add_category, get_categories, remove_category,
    users_count, get_all_users,
    groups_count, get_all_groups,
    set_global_mandatory, remove_global_mandatory, get_global_mandatory,
    add_scheduled_ad, get_scheduled_ads, remove_scheduled_ad, toggle_scheduled_ad
)
from keyboards import (
    main_admin_keyboard, back_to_main_admin_keyboard, cancel_keyboard,
    channels_menu_keyboard, channels_remove_keyboard,
    categories_menu_keyboard, categories_remove_keyboard,
    groups_menu_keyboard, scheduled_menu_keyboard, scheduled_target_keyboard,
    scheduled_remove_keyboard
)
from git_sync import sync_database_to_github

admin_router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminStates(StatesGroup):
    waiting_channel = State()
    waiting_category_name = State()
    waiting_category_price = State()
    waiting_category_payment_link = State()
    waiting_category_channel_link = State()
    waiting_category_info = State()
    waiting_broadcast_users = State()
    waiting_broadcast_groups = State()
    waiting_global_sub_forward = State()
    waiting_scheduled_content = State()
    waiting_scheduled_time = State()


# ============================================================
# BOSH MENYU / NAVIGATSIYA
# ============================================================

@admin_router.message(Command("admin"), F.chat.type == "private")
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛠 Admin panel:", reply_markup=main_admin_keyboard())


@admin_router.callback_query(F.data == "admin_back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("🛠 Admin panel:", reply_markup=main_admin_keyboard())


@admin_router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("🛠 Admin panel:", reply_markup=main_admin_keyboard())


@admin_router.callback_query(F.data == "menu_channels")
async def menu_channels(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text("📢 Majburiy obuna kanallari:", reply_markup=channels_menu_keyboard())


@admin_router.callback_query(F.data == "menu_categories")
async def menu_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text("🛍 To'lov kategoriyalari:", reply_markup=categories_menu_keyboard())


@admin_router.callback_query(F.data == "menu_groups")
async def menu_groups(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text("👥 Guruhlar boshqaruvi:", reply_markup=groups_menu_keyboard())


# ============================================================
# MAJBURIY OBUNA KANALLARI
# ============================================================

@admin_router.callback_query(F.data == "admin_add_channel")
async def admin_add_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_channel)
    await callback.message.edit_text(
        "📌 Botni kanal/guruhga <b>admin</b> qilib qo'shing, so'ng o'sha yerdan "
        "istalgan xabarni shu yerga <b>forward</b> qiling.",
        reply_markup=cancel_keyboard()
    )


@admin_router.message(AdminStates.waiting_channel, F.chat.type == "private")
async def process_add_channel(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    chat = message.forward_from_chat
    if chat is None:
        await message.answer("⚠️ Iltimos, kanal/guruhdan xabarni forward qiling.", reply_markup=cancel_keyboard())
        return

    try:
        bot_member = await bot.get_chat_member(chat.id, bot.id)
    except TelegramBadRequest:
        await message.answer("❌ Bot bu chatda topilmadi.", reply_markup=cancel_keyboard())
        return
    if bot_member.status not in ("administrator", "creator"):
        await message.answer("❌ Bot bu yerda admin emas.", reply_markup=cancel_keyboard())
        return

    invite_link = ""
    if not chat.username:
        try:
            invite_link = await bot.export_chat_invite_link(chat.id)
        except TelegramBadRequest:
            await message.answer("❌ Bot taklif havolasi yarata olmadi.", reply_markup=cancel_keyboard())
            return

    chat_type = "channel" if chat.type == "channel" else "group"
    await add_channel(chat.id, chat.title, chat.username or "", invite_link, chat_type)
    await state.clear()
    await sync_database_to_github(f"Kanal qo'shildi: {chat.title}")
    await message.answer(f"✅ \"{chat.title}\" qo'shildi!")
    await message.answer("📢 Majburiy obuna kanallari:", reply_markup=channels_menu_keyboard())


@admin_router.callback_query(F.data == "admin_list_channels")
async def admin_list_channels(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    channels = await get_channels()
    if not channels:
        await callback.answer("Hozircha kanal qo'shilmagan.", show_alert=True)
        return
    await callback.message.edit_text("📃 Ro'yxat (o'chirish uchun bosing):", reply_markup=channels_remove_keyboard(channels))


@admin_router.callback_query(F.data.startswith("remove_ch_"))
async def admin_remove_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    chat_id = int(callback.data.replace("remove_ch_", ""))
    await remove_channel(chat_id)
    await sync_database_to_github(f"Kanal o'chirildi: {chat_id}")
    channels = await get_channels()
    if channels:
        await callback.message.edit_text("📃 Ro'yxat (o'chirish uchun bosing):", reply_markup=channels_remove_keyboard(channels))
    else:
        await callback.message.edit_text("Ro'yxat bo'sh.", reply_markup=channels_menu_keyboard())
    await callback.answer("🗑 O'chirildi")


# ============================================================
# TO'LOV KATEGORIYALARI
# ============================================================

@admin_router.callback_query(F.data == "admin_add_category")
async def admin_add_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_category_name)
    await callback.message.edit_text("📝 Kategoriya nomini yuboring:", reply_markup=cancel_keyboard())


@admin_router.message(AdminStates.waiting_category_name, F.chat.type == "private")
async def process_category_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminStates.waiting_category_price)
    await message.answer("💰 Narxini yuboring:", reply_markup=cancel_keyboard())


@admin_router.message(AdminStates.waiting_category_price, F.chat.type == "private")
async def process_category_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(price=message.text.strip())
    await state.set_state(AdminStates.waiting_category_payment_link)
    await message.answer("💳 To'lov ma'lumotini yuboring (karta raqami yoki havola):", reply_markup=cancel_keyboard())


@admin_router.message(AdminStates.waiting_category_payment_link, F.chat.type == "private")
async def process_category_payment_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(payment_link=message.text.strip())
    await state.set_state(AdminStates.waiting_category_channel_link)
    await message.answer("🔗 Kanal havolasini yuboring (to'lovdan keyin beriladigan):", reply_markup=cancel_keyboard())


@admin_router.message(AdminStates.waiting_category_channel_link, F.chat.type == "private")
async def process_category_channel_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(channel_link=message.text.strip())
    await state.set_state(AdminStates.waiting_category_info)
    await message.answer(
        "📋 Qo'shimcha ma'lumot yuboring — bu AI mijozlarga batafsil savollarga "
        "(nechta post bor, namuna bormi, ishonchli-mi va h.k.) javob berishda ishlatadi.\n\n"
        "Masalan: <i>\"Kanalda 500+ post bor, har kuni yangilanadi, 200 dan ortiq "
        "obunachi bor, 3 kunlik kafolat beramiz\"</i>\n\n"
        "Agar hozircha qo'shimcha ma'lumot bo'lmasa, <code>/empty</code> deb yuboring.",
        reply_markup=cancel_keyboard()
    )


@admin_router.message(AdminStates.waiting_category_info, F.chat.type == "private")
async def process_category_info(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    info = "" if message.text.strip() == "/empty" else message.text.strip()
    data = await state.get_data()
    await add_category(data.get("name"), data.get("price"), data.get("payment_link"), data.get("channel_link"), info)
    await state.clear()
    await sync_database_to_github(f"Kategoriya qo'shildi: {data.get('name')}")
    await message.answer(f"✅ \"{data.get('name')}\" qo'shildi!")
    await message.answer("🛍 To'lov kategoriyalari:", reply_markup=categories_menu_keyboard())


@admin_router.callback_query(F.data == "admin_list_categories")
async def admin_list_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    categories = await get_categories()
    if not categories:
        await callback.answer("Hozircha kategoriya qo'shilmagan.", show_alert=True)
        return
    await callback.message.edit_text("📃 Ro'yxat (o'chirish uchun bosing):", reply_markup=categories_remove_keyboard(categories))


@admin_router.callback_query(F.data.startswith("remove_cat_"))
async def admin_remove_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    category_id = int(callback.data.replace("remove_cat_", ""))
    await remove_category(category_id)
    await sync_database_to_github(f"Kategoriya o'chirildi: {category_id}")
    categories = await get_categories()
    if categories:
        await callback.message.edit_text("📃 Ro'yxat (o'chirish uchun bosing):", reply_markup=categories_remove_keyboard(categories))
    else:
        await callback.message.edit_text("Ro'yxat bo'sh.", reply_markup=categories_menu_keyboard())
    await callback.answer("🗑 O'chirildi")


# ============================================================
# GURUHLAR BOSHQARUVI (global obuna + broadcast)
# ============================================================

@admin_router.callback_query(F.data == "grp_setglobalsub")
async def grp_setglobalsub(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_global_sub_forward)
    await callback.message.edit_text(
        "📌 Barcha guruhlar uchun majburiy qilmoqchi bo'lgan kanal/guruhdan "
        "xabarni shu yerga <b>forward</b> qiling.",
        reply_markup=cancel_keyboard()
    )


@admin_router.message(AdminStates.waiting_global_sub_forward, F.chat.type == "private")
async def process_global_sub_forward(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    chat = message.forward_from_chat
    if chat is None:
        await message.answer("⚠️ Iltimos, kanal/guruhdan xabarni forward qiling.", reply_markup=cancel_keyboard())
        return
    try:
        bot_member = await bot.get_chat_member(chat.id, bot.id)
    except TelegramBadRequest:
        await message.answer("❌ Bot bu chatda topilmadi.", reply_markup=cancel_keyboard())
        return
    if bot_member.status not in ("administrator", "creator"):
        await message.answer("❌ Bot bu yerda admin emas.", reply_markup=cancel_keyboard())
        return

    link = f"https://t.me/{chat.username}" if chat.username else None
    if not link:
        try:
            link = await bot.export_chat_invite_link(chat.id)
        except TelegramBadRequest:
            await message.answer("❌ Bot taklif havolasi yarata olmadi.", reply_markup=cancel_keyboard())
            return

    await set_global_mandatory(chat.id, link, chat.title)
    await state.clear()
    await sync_database_to_github(f"Global obuna o'rnatildi: {chat.title}")
    await message.answer(f"✅ Global majburiy obuna o'rnatildi: <b>{chat.title}</b>")
    await message.answer("👥 Guruhlar boshqaruvi:", reply_markup=groups_menu_keyboard())


@admin_router.callback_query(F.data == "grp_removeglobalsub")
async def grp_removeglobalsub(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await remove_global_mandatory()
    await sync_database_to_github("Global obuna bekor qilindi")
    await callback.answer("Bekor qilindi")
    await callback.message.edit_text("👥 Guruhlar boshqaruvi:", reply_markup=groups_menu_keyboard())


@admin_router.callback_query(F.data == "grp_broadcast")
async def grp_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast_groups)
    await callback.message.edit_text("📢 Barcha guruhlarga yubormoqchi bo'lgan xabaringizni yuboring.", reply_markup=cancel_keyboard())


@admin_router.message(AdminStates.waiting_broadcast_groups, F.chat.type == "private")
async def process_broadcast_groups(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    groups = await get_all_groups()
    status_msg = await message.answer(f"⏳ Yuborilmoqda... (0/{len(groups)})")
    success, failed = 0, 0
    for i, chat_id in enumerate(groups, start=1):
        try:
            await message.copy_to(chat_id)
            success += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        if i % 20 == 0:
            await asyncio.sleep(1)
    await status_msg.edit_text(f"✅ Yakunlandi!\n📤 Muvaffaqiyatli: {success}\n❌ Yuborilmadi: {failed}")
    await message.answer("👥 Guruhlar boshqaruvi:", reply_markup=groups_menu_keyboard())


# ============================================================
# AVTOMATIK TAKRORIY REKLAMA
# ============================================================

@admin_router.callback_query(F.data == "menu_scheduled")
async def menu_scheduled(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text("⏰ Avtomatik takroriy reklama:", reply_markup=scheduled_menu_keyboard())


@admin_router.callback_query(F.data == "sched_add")
async def sched_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_scheduled_content)
    await callback.message.edit_text(
        "📝 Har kuni avtomatik yuboriladigan xabaringizni (matn, rasm, video) yuboring.",
        reply_markup=cancel_keyboard()
    )


@admin_router.message(AdminStates.waiting_scheduled_content, F.chat.type == "private")
async def sched_add_content(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(source_chat_id=message.chat.id, source_message_id=message.message_id)
    await state.set_state(AdminStates.waiting_scheduled_time)
    await message.answer(
        "🕐 Har kuni soat nechada yuborilsin? Vaqtni <b>SS:DD</b> formatida yozing "
        "(Toshkent vaqti bo'yicha, masalan: <code>09:00</code> yoki <code>18:30</code>).",
        reply_markup=cancel_keyboard()
    )


@admin_router.message(AdminStates.waiting_scheduled_time, F.chat.type == "private")
async def sched_add_time(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    time_text = message.text.strip()
    parts = time_text.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        await message.answer("⚠️ Noto'g'ri format. Masalan: <code>09:00</code>", reply_markup=cancel_keyboard())
        return
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await message.answer("⚠️ Vaqt noto'g'ri. Soat 00-23, daqiqa 00-59 oralig'ida bo'lsin.", reply_markup=cancel_keyboard())
        return

    await state.update_data(send_time=f"{hour:02d}:{minute:02d}")
    await message.answer("🎯 Kimlarga yuborilsin?", reply_markup=scheduled_target_keyboard())


@admin_router.callback_query(F.data.startswith("sched_target_"))
async def sched_add_target(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    target = callback.data.replace("sched_target_", "")  # groups | users | both
    data = await state.get_data()
    await add_scheduled_ad(data["source_chat_id"], data["source_message_id"], data["send_time"], target)
    await state.clear()
    await sync_database_to_github(f"Avtomatik reklama qo'shildi: {data['send_time']}")
    await callback.message.edit_text(
        f"✅ Avtomatik reklama sozlandi! Har kuni soat <b>{data['send_time']}</b>da yuboriladi.",
        reply_markup=scheduled_menu_keyboard()
    )


@admin_router.callback_query(F.data == "sched_list")
async def sched_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ads = await get_scheduled_ads()
    if not ads:
        await callback.answer("Hozircha avtomatik reklama qo'shilmagan.", show_alert=True)
        return
    await callback.message.edit_text(
        "📃 Avtomatik reklamalar (o'chirish uchun bosing):",
        reply_markup=scheduled_remove_keyboard(ads)
    )


@admin_router.callback_query(F.data.startswith("sched_remove_"))
async def sched_remove(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ad_id = int(callback.data.replace("sched_remove_", ""))
    await remove_scheduled_ad(ad_id)
    await sync_database_to_github(f"Avtomatik reklama o'chirildi: {ad_id}")
    ads = await get_scheduled_ads()
    if ads:
        await callback.message.edit_text("📃 Avtomatik reklamalar (o'chirish uchun bosing):", reply_markup=scheduled_remove_keyboard(ads))
    else:
        await callback.message.edit_text("Ro'yxat bo'sh.", reply_markup=scheduled_menu_keyboard())
    await callback.answer("🗑 O'chirildi")


# ============================================================
# FOYDALANUVCHILARGA XABAR (shaxsiy chatdagilar)
# ============================================================

@admin_router.callback_query(F.data == "admin_broadcast_users")
async def admin_broadcast_users_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast_users)
    await callback.message.edit_text("📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.", reply_markup=cancel_keyboard())


@admin_router.message(AdminStates.waiting_broadcast_users, F.chat.type == "private")
async def process_broadcast_users(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    users = await get_all_users()
    status_msg = await message.answer(f"⏳ Yuborilmoqda... (0/{len(users)})")
    success, failed = 0, 0
    for i, user_id in enumerate(users, start=1):
        try:
            await message.copy_to(user_id)
            success += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        if i % 20 == 0:
            await asyncio.sleep(1)
    await status_msg.edit_text(f"✅ Yakunlandi!\n📤 Muvaffaqiyatli: {success}\n❌ Yuborilmadi: {failed}")
    await message.answer("🛠 Admin panel:", reply_markup=main_admin_keyboard())


# ============================================================
# UMUMIY STATISTIKA
# ============================================================

@admin_router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    u = await users_count()
    c = await channels_count()
    cats = await get_categories()
    g = await groups_count()
    global_sub = await get_global_mandatory()
    global_text = global_sub["mandatory_chat_title"] if global_sub else "o'rnatilmagan"

    await callback.answer()
    await callback.message.answer(
        f"📊 <b>Umumiy statistika</b>\n\n"
        f"👤 Foydalanuvchilar: {u}\n"
        f"📢 Majburiy obuna kanallari: {c}\n"
        f"🛍 To'lov kategoriyalari: {len(cats)}\n"
        f"👥 Bot admin bo'lgan guruhlar: {g}\n"
        f"🌐 Global majburiy obuna: {global_text}"
    )
