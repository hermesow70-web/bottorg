import logging
import os
import asyncio
from datetime import datetime
from db import load_users, load_banned
from config import ADMIN_IDS

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def notify_all_users(bot, text, reply_markup=None, photo=None, video=None):
    users = load_users()
    banned = load_banned()
    for user in users:
        if user["id"] in banned:
            continue
        try:
            if photo:
                await bot.send_photo(user["id"], photo=photo, caption=text, reply_markup=reply_markup)
            elif video:
                await bot.send_video(user["id"], video=video, caption=text, reply_markup=reply_markup)
            else:
                await bot.send_message(user["id"], text, reply_markup=reply_markup)
        except:
            pass
        await asyncio.sleep(0.05)

async def notify_admins(bot, text, reply_markup=None):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup)
        except:
            pass
