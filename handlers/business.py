import time
import logging

from aiogram import Router, Bot

from config import OWNER_ID, BOT_USERNAME
from ai import generate_reply
from database import get_categories

business_router = Router()

paused_until: dict[int, float] = {}
greeted_chats: set[int] = set()
PAUSE_SECONDS = 30 * 60  # 30 daqiqa


async def _build_categories_context() -> str:
    categories = await get_categories()
    context = f"To'lov chekini mijoz shu botga yuborishi kerak: @{BOT_USERNAME} (u yerda /start bosib, chek yuboradi)."
    if not categories:
        return context
    lines = []
    for _, name, price, payment_link, channel_link, info in categories:
        line = f"- {name}: {price} | To'lov ma'lumoti: {payment_link}"
        if info:
            line += f" | Qo'shimcha: {info}"
        lines.append(line)
    return context + "\n\nMavjud kanallar/kategoriyalar (faqat shu ro'yxatdagi ma'lumotdan foydalan):\n" + "\n".join(lines)


@business_router.business_message()
async def handle_business_message(message, bot: Bot):
    chat_id = message.chat.id
    connection_id = message.business_connection_id

    if message.from_user and message.from_user.id == OWNER_ID:
        paused_until[chat_id] = time.time() + PAUSE_SECONDS
        logging.info(f"[PAUSE] {chat_id} uchun AI 30 daqiqaga to'xtatildi")
        return

    if paused_until.get(chat_id, 0) > time.time():
        return

    if not message.text:
        return

    categories_context = await _build_categories_context()

    if chat_id not in greeted_chats:
        greeted_chats.add(chat_id)
        intro_note = (
            "\n\nMUHIM: bu foydalanuvchi bilan birinchi suhbat. Javobingni "
            "\"Salom! Profil egasi hozir band, tez orada o'zi javob beradi. "
            "Men uning AI yordamchisiman, savolingizga hozir yordam beraman:\" "
            "kabi qisqa tanishtiruv bilan boshla, keyin savolga javob ber."
        )
        extra_context = categories_context + intro_note
    else:
        extra_context = categories_context

    reply_text = await generate_reply(message.text, extra_context=extra_context)
    try:
        await bot.send_message(chat_id=chat_id, text=reply_text, business_connection_id=connection_id)
    except Exception as e:
        logging.error(f"[ERROR] Javob yuborib bo'lmadi: {e}")
