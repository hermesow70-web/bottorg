import asyncio
from config import ADMIN_IDS
from database import load_users, is_banned

async def notify_admins(bot, text):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except:
            pass

async def notify_all_users(bot, text):
    users = load_users()
    for user in users:
        if is_banned(user["id"]):
            continue
        try:
            await bot.send_message(user["id"], text, parse_mode="Markdown")
        except:
            pass
        await asyncio.sleep(0.05)
