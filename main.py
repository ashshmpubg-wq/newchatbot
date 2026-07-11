import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers.admin_panel import admin_router
from handlers.start import start_router
from handlers.group_admin import group_admin_router
from handlers.group import group_router
from handlers.business import business_router
from scheduler import scheduler_loop


async def main():
    logging.basicConfig(level=logging.INFO)

    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Tartib: admin panel -> foydalanuvchi (shaxsiy) -> guruh admin buyruqlari -> guruh moderatsiyasi -> business
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(group_admin_router)
    dp.include_router(group_router)
    dp.include_router(business_router)

    logging.info("=" * 50)
    logging.info("🤖 Universal bot ishga tushdi!")
    logging.info("=" * 50)

    await bot.delete_webhook(drop_pending_updates=True)

    asyncio.create_task(scheduler_loop(bot))

    await dp.start_polling(bot, allowed_updates=[
        "message", "callback_query", "my_chat_member",
        "business_connection", "business_message",
        "edited_business_message", "deleted_business_messages"
    ])


if __name__ == "__main__":
    asyncio.run(main())