import asyncio
from config import ADMIN_IDS
from database import load_users, load_banned

async def notify_admins(bot, text, reply_markup=None):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup, parse_mode="Markdown")
        except:
            pass

async def notify_all_users(bot, text):
    users = load_users()
    banned = load_banned()
    for user in users:
        if user["id"] in banned:
            continue
        try:
            await bot.send_message(user["id"], text, parse_mode="Markdown")
        except:
            pass
        await asyncio.sleep(0.05)
