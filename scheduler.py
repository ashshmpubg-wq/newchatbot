import asyncio
import logging
from datetime import datetime, timedelta, timezone
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from database import get_scheduled_ads, mark_scheduled_ad_sent, get_all_groups, get_all_users

TASHKENT_TZ = timezone(timedelta(hours=5))
CHECK_INTERVAL_SECONDS = 60


async def _send_ad_to_targets(bot: Bot, ad, targets: list[int]):
    success = 0
    for i, chat_id in enumerate(targets, start=1):
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=ad["source_chat_id"],
                message_id=ad["source_message_id"]
            )
            success += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
        if i % 20 == 0:
            await asyncio.sleep(1)
    return success


async def scheduler_loop(bot: Bot):
    """Har daqiqada avtomatik reklamalarni tekshirib, vaqti kelganlarini yuboradi."""
    logging.info("[SCHEDULER] Avtomatik reklama rejalashtiruvchisi ishga tushdi")
    while True:
        try:
            now = datetime.now(TASHKENT_TZ)
            now_time_str = now.strftime("%H:%M")
            today_str = now.strftime("%Y-%m-%d")

            ads = await get_scheduled_ads()
            for ad in ads:
                if not ad["enabled"]:
                    continue
                if ad["last_sent_date"] == today_str:
                    continue
                if now_time_str < ad["send_time"]:
                    continue

                targets = []
                if ad["target"] in ("groups", "both"):
                    targets += await get_all_groups()
                if ad["target"] in ("users", "both"):
                    targets += await get_all_users()

                success = await _send_ad_to_targets(bot, ad, targets)
                await mark_scheduled_ad_sent(ad["id"], today_str)
                logging.info(f"[SCHEDULER] Reklama #{ad['id']} yuborildi ({success}/{len(targets)})")
        except Exception as e:
            logging.error(f"[SCHEDULER-ERROR] {type(e).__name__}: {e}")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
