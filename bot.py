import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from user import user_router
from admin import admin_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(admin_router)

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
