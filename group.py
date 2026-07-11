import re
import time
import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.exceptions import TelegramBadRequest

from config import (
    DEFAULT_SWEAR_WORDS, FLOOD_MAX_MESSAGES, FLOOD_WINDOW_SECONDS,
    FLOOD_MUTE_MINUTES, WARNING_AUTO_DELETE_SECONDS
)
from database import register_group, unregister_group, get_group, get_custom_words, get_global_mandatory

group_router = Router()

LINK_PATTERN = re.compile(r"(https?://|t\.me/|telegram\.me/|@\w{4,})", re.IGNORECASE)
_message_log: dict[tuple[int, int], list[float]] = {}


async def _delete_and_warn(message: Message, bot: Bot, warning_text: str):
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    warn_msg = await message.answer(warning_text)

    async def _auto_delete():
        await asyncio.sleep(WARNING_AUTO_DELETE_SECONDS)
        try:
            await warn_msg.delete()
        except TelegramBadRequest:
            pass

    asyncio.create_task(_auto_delete())


async def _is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except TelegramBadRequest:
        return False


@group_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def on_bot_removed(event: ChatMemberUpdated):
    await unregister_group(event.chat.id)


@group_router.my_chat_member()
async def on_bot_status_changed(event: ChatMemberUpdated):
    if event.new_chat_member.user.id != event.bot.id:
        return
    if event.new_chat_member.status == "administrator":
        await register_group(event.chat.id, event.chat.title or "Noma'lum guruh")
        logging.info(f"[GROUP] Bot admin qilindi: {event.chat.title} ({event.chat.id})")
    elif event.new_chat_member.status in ("left", "kicked"):
        await unregister_group(event.chat.id)


@group_router.message(F.new_chat_members)
async def welcome_new_member(message: Message):
    group = await get_group(message.chat.id)
    welcome_text = group["welcome_text"] if group else "👋 Xush kelibsiz, {name}!"
    for new_member in message.new_chat_members:
        if new_member.is_bot:
            continue
        text = welcome_text.replace("{name}", new_member.full_name).replace("{title}", message.chat.title or "")
        await message.answer(text)


@group_router.message(F.chat.type.in_({"group", "supergroup"}), F.text | F.caption)
async def moderate_message(message: Message, bot: Bot):
    group = await get_group(message.chat.id)
    if group is None:
        return

    user_id = message.from_user.id
    if await _is_admin(bot, message.chat.id, user_id):
        return

    text = (message.text or message.caption or "")

    # 1) ANTI-FLOOD
    if group["flood_filter_enabled"]:
        key = (message.chat.id, user_id)
        now = time.time()
        timestamps = [t for t in _message_log.get(key, []) if now - t < FLOOD_WINDOW_SECONDS]
        timestamps.append(now)
        _message_log[key] = timestamps

        if len(timestamps) > FLOOD_MAX_MESSAGES:
            try:
                until = int(time.time() + FLOOD_MUTE_MINUTES * 60)
                await bot.restrict_chat_member(
                    message.chat.id, user_id,
                    permissions={"can_send_messages": False}, until_date=until
                )
                await message.answer(
                    f"🚫 {message.from_user.full_name} juda tez-tez yozgani uchun "
                    f"{FLOOD_MUTE_MINUTES} daqiqaga cheklandi."
                )
            except TelegramBadRequest:
                pass
            try:
                await message.delete()
            except TelegramBadRequest:
                pass
            return

    # 2) SO'KINISH FILTRI
    if group["swear_filter_enabled"]:
        custom_words = await get_custom_words(message.chat.id)
        all_words = DEFAULT_SWEAR_WORDS + custom_words
        lowered = text.lower()
        if any(word in lowered for word in all_words):
            await _delete_and_warn(message, bot, f"⚠️ {message.from_user.full_name}, iltimos, madaniy so'zlashing.")
            return

    # 3) HAVOLA/REKLAMA FILTRI
    if group["link_filter_enabled"]:
        if LINK_PATTERN.search(text):
            await _delete_and_warn(
                message, bot, f"⚠️ {message.from_user.full_name}, guruhda havola/reklama tarqatish taqiqlangan."
            )
            return

    # 4) MAJBURIY OBUNA (guruhning o'zi + bot egasining globali)
    unmet = []
    if group["mandatory_chat_id"]:
        try:
            member = await bot.get_chat_member(group["mandatory_chat_id"], user_id)
            if member.status in ("left", "kicked"):
                unmet.append((group["mandatory_chat_link"], group["mandatory_chat_title"]))
        except TelegramBadRequest:
            pass

    global_sub = await get_global_mandatory()
    if global_sub:
        try:
            member = await bot.get_chat_member(global_sub["mandatory_chat_id"], user_id)
            if member.status in ("left", "kicked"):
                unmet.append((global_sub["mandatory_chat_link"], global_sub["mandatory_chat_title"]))
        except TelegramBadRequest:
            pass

    if unmet:
        links_text = "\n".join(f"➡️ <a href='{link}'>{title}</a>" for link, title in unmet)
        await _delete_and_warn(
            message, bot,
            f"⚠️ {message.from_user.full_name}, yozish uchun avval quyidagilarga obuna bo'ling:\n"
            f"{links_text}\n\nSo'ngra xabaringizni qaytadan yuboring."
        )
        return
