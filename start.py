from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS
from database import (
    add_user, get_channels, get_categories, get_category,
    create_request, get_request, update_request_status
)
from keyboards import (
    subscribe_keyboard, categories_keyboard, category_detail_keyboard,
    admin_review_keyboard
)

start_router = Router()


class UserStates(StatesGroup):
    waiting_screenshot = State()


async def get_not_subscribed_channels(bot: Bot, user_id: int) -> list:
    channels = await get_channels()
    not_subscribed = []
    for chat_id, title, username, invite_link, chat_type in channels:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append((chat_id, title, username, invite_link, chat_type))
        except TelegramBadRequest:
            continue
    return not_subscribed


async def show_categories_or_empty(message_or_callback, edit: bool = False):
    categories = await get_categories()
    text = "Quyidagi kategoriyalardan birini tanlang:" if categories else \
        "Hozircha kategoriyalar mavjud emas. Keyinroq urinib ko'ring."
    markup = categories_keyboard(categories) if categories else None
    if edit:
        await message_or_callback.edit_text(text, reply_markup=markup)
    else:
        await message_or_callback.answer(text, reply_markup=markup)


@start_router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, bot: Bot):
    await add_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name)

    not_subscribed = await get_not_subscribed_channels(bot, message.from_user.id)
    if not_subscribed:
        await message.answer(
            "👋 Assalomu alaykum!\n\nBotdan foydalanish uchun quyidagi kanal/guruh(lar)ga "
            "obuna bo'ling, so'ngra <b>✅ Tekshirish</b> tugmasini bosing:",
            reply_markup=subscribe_keyboard(not_subscribed)
        )
        return

    await message.answer("✅ Xush kelibsiz!")
    await show_categories_or_empty(message)


@start_router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot):
    not_subscribed = await get_not_subscribed_channels(bot, callback.from_user.id)
    if not_subscribed:
        await callback.answer("❌ Siz hali barcha kanal/guruhlarga obuna bo'lmadingiz!", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=subscribe_keyboard(not_subscribed))
        except TelegramBadRequest:
            pass
        return
    await callback.message.delete()
    await callback.message.answer("✅ Rahmat! Endi botdan to'liq foydalanishingiz mumkin.")
    await show_categories_or_empty(callback.message)


@start_router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_categories_or_empty(callback.message, edit=True)


@start_router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    category_id = int(callback.data.replace("cat_", ""))
    category = await get_category(category_id)
    if category is None:
        await callback.answer("Bu kategoriya topilmadi.", show_alert=True)
        return

    _, name, price, payment_link, channel_link = category
    await callback.message.edit_text(
        f"🎬 <b>{name}</b>\n"
        f"💰 Narxi: {price}\n"
        f"💳 To'lov ma'lumoti: <code>{payment_link}</code>\n\n"
        f"To'lovni amalga oshiring, so'ngra chekni yuborish uchun "
        f"pastdagi <b>📤 Chek yuborish</b> tugmasini bosing.",
        reply_markup=category_detail_keyboard(category_id, payment_link)
    )


@start_router.callback_query(F.data.startswith("pay_"))
async def ask_screenshot(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.replace("pay_", ""))
    await state.update_data(category_id=category_id)
    await state.set_state(UserStates.waiting_screenshot)
    await callback.message.answer("📸 To'lov chekining skrinshotini (rasm sifatida) shu yerga yuboring.")


@start_router.message(UserStates.waiting_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    category_id = data.get("category_id")
    category = await get_category(category_id)
    await state.clear()

    if category is None:
        await message.answer("⚠️ Kategoriya topilmadi. Qaytadan /start bosing.")
        return

    _, name, price, payment_link, channel_link = category
    screenshot_file_id = message.photo[-1].file_id
    request_id = await create_request(message.from_user.id, category_id, screenshot_file_id)

    await message.answer("✅ Chekingiz qabul qilindi, admin tekshirib chiqadi. Iltimos kuting.")

    caption = (
        f"🆕 <b>Yangi to'lov so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} "
        f"(@{message.from_user.username or 'username yo\u2019q'})\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"🎬 Kategoriya: {name}\n"
        f"💰 Narxi: {price}\n"
        f"🔢 So'rov ID: {request_id}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(admin_id, screenshot_file_id, caption=caption,
                                  reply_markup=admin_review_keyboard(request_id))
        except Exception:
            continue


@start_router.message(UserStates.waiting_screenshot)
async def wrong_screenshot_format(message: Message):
    await message.answer("⚠️ Iltimos, chekni <b>rasm (screenshot)</b> sifatida yuboring.")


@start_router.callback_query(F.data.startswith("approve_"))
async def approve_request(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        return
    request_id = int(callback.data.replace("approve_", ""))
    request = await get_request(request_id)
    if request is None:
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return
    _, user_id, category_id, screenshot_file_id, status = request
    if status != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    category = await get_category(category_id)
    await update_request_status(request_id, "approved")
    if category:
        _, name, price, payment_link, channel_link = category
        try:
            await bot.send_message(
                user_id,
                f"✅ To'lovingiz tasdiqlandi!\n\n🎬 {name}\n\n🔗 Kanalga qo'shilish uchun havola:\n{channel_link}"
            )
        except Exception:
            pass

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ <b>TASDIQLANDI</b>", reply_markup=None
    )
    await callback.answer("Tasdiqlandi ✅")


@start_router.callback_query(F.data.startswith("reject_"))
async def reject_request(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        return
    request_id = int(callback.data.replace("reject_", ""))
    request = await get_request(request_id)
    if request is None:
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return
    _, user_id, category_id, screenshot_file_id, status = request
    if status != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await update_request_status(request_id, "rejected")
    try:
        await bot.send_message(user_id, "❌ To'lovingiz tasdiqlanmadi. Agar xato bo'lsa, admin bilan bog'laning.")
    except Exception:
        pass

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ <b>RAD ETILDI</b>", reply_markup=None
    )
    await callback.answer("Rad etildi ❌")
