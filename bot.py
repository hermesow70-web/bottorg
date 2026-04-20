import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from user import router as user_router
from withdraw import router as withdraw_router
from review import router as review_router
from admin import router as admin_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(withdraw_router)
dp.include_router(review_router)
dp.include_router(admin_router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
