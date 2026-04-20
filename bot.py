import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from user_profile import profile_router
from user_withdraw import withdraw_router
from user_review import review_router
from admin import admin_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(profile_router)
dp.include_router(withdraw_router)
dp.include_router(review_router)
dp.include_router(admin_router)

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
